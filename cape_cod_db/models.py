from datetime import datetime, timezone

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

# NOTE: For now we're going to keep all models in one module. Should this get
#       painful we will look at splitting this out. Both ways of doing models
#       are covered in the SQLModel docs.


class CapeModel(SQLModel):
    """Base class for all CAPE DB tables.

    Contains fields that all CAPE tables should support.
    """

    created_at: datetime = Field(
        default=datetime.now(timezone.utc), nullable=False
    )
    last_edited: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )


class User(CapeModel, table=True):
    """Represents a CAPE User"""

    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    # TODO:
    #   - find a validator library and use somewhere in the chain of
    #     adding/updating users (api, db layer, etc)
    email: str = Field(index=True, unique=True)

    def __repr__(self):
        # TODO: we want to make __repr__ methods useful for log tracing, but def
        #       want to keep PII and (hopefully unlikely in this DB) PHI out.
        #       this is for testing things right now but includes PII.
        #       Additionally if we have a method that is usable for all table
        #       models we can just put it in the base class or make a mixin
        return (
            f"<{self.__class__.__name__}(id='{self.id}', "
            f"first_name='{self.first_name}', "
            f"last_name='{self.last_name}'>"
        )


class Tributary(CapeModel, table=True):
    """Organizational unit that owns resources and has user members.

    Tributaries represent organizational units (teams, departments, projects)
    that produce data and own AWS/infrastructure resources. Users belong to
    one or more tributaries, and this membership grants base permissions.

    Every tributary gets 4 standard S3 buckets for the data pipeline:
    1. Raw user data uploads (triggers ETL)
    2. Cleaned user upload data (cataloged in datalake)
    3. Raw analysis results (triggers ETL)
    4. Cleaned analysis result data (cataloged)

    These buckets are represented as Resource records, not fields on this model.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    code: str = Field(unique=True, index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))
    parent_id: int | None = Field(default=None, foreign_key="tributary.id")
    attributes: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )


class UserTributary(SQLModel, table=True):
    """Many-to-many relationship between users and tributaries with role.

    Represents user membership in a tributary. A user can belong to multiple
    tributaries with different roles. This is the core attribute for ABAC
    authorization decisions.

    Roles:
    - "member": Standard access to tributary resources
    - "admin": Elevated access, can manage tributary membership
    - "viewer": Read-only access
    """

    user_id: int = Field(foreign_key="user.id", primary_key=True)
    tributary_id: int = Field(foreign_key="tributary.id", primary_key=True)
    role: str = Field(default="member")
    granted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    granted_by: int | None = Field(default=None, foreign_key="user.id")
    expires_at: datetime | None = None


class Resource(CapeModel, table=True):
    """Generic resource that can be authorized via ABAC.

    Platform-agnostic resource registry supporting AWS resources (S3, EC2,
    Lambda, Glue, etc.) and non-AWS resources (applications, databases).
    Uses JSONB attributes for resource-specific fields.

    Examples:
    - S3: resource_identifier="s3://bucket/path",
          attributes={"bucket": "cape-datalake", "path_prefix": "eng/uploads/",
                      "category": "raw_uploads"}
    - EC2: resource_identifier="arn:aws:ec2:...:instance/i-abc",
           attributes={"instance_id": "i-abc", "instance_type": "t3.medium"}
    - App: resource_identifier="cape-web-app-prod",
           attributes={"url": "https://app.example.com", "environment": "prod"}
    """

    id: int | None = Field(default=None, primary_key=True)
    resource_type: str = Field(index=True)
    resource_identifier: str = Field(unique=True, index=True)
    display_name: str
    tributary_id: int | None = Field(default=None, foreign_key="tributary.id")
    access_type: str
    attributes: dict = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )


class UserAttribute(CapeModel, table=True):
    """Flexible attribute storage for advanced ABAC.

    Stores user-level attributes for authorization decisions. Common use cases:
    - User lifecycle: user_status="quarantine"|"active"|"suspended"|"deactivated"
    - Admin privileges: is_admin="true"
    - Clearance levels: clearance_level="secret"
    - System roles: system_role="security_auditor"
    - AD/SAML synced attributes: source="ad" or "saml"

    Attributes are deployment-specific. The system provides the capability;
    specific workflows determine which attributes to use.
    """

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    attribute_key: str
    attribute_value: str
    source: str | None = None
