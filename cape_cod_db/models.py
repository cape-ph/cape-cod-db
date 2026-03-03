from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

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
