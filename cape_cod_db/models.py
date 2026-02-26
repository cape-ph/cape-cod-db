from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

# NOTE: For now we're going to keep all models in one module. Should this get
#       painful we will look at splitting this out. Both ways of doing models
#       are covered in the SQLModel docs.


class CapeModel(SQLModel):
    """Base class for all CAPE DB tables.

    Contains fields that all CAPE tables should support.
    """

    created_at: datetime = Field(default=datetime.utcnow(), nullable=False)
    last_edited: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.utcnow()},
    )


class User(CapeModel, table=True):
    """Represents a CAPE User"""

    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    # TODO: use email to test migrations...
    # email: str = Field(index=True)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}(id='{self.id}', "
            f"first_name='{self.first_name}', "
            f"last_name='{self.last_name}'>"
        )
