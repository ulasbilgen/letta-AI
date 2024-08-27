from typing import TYPE_CHECKING
import uuid
from logging import getLogger
from typing import Optional
from uuid import UUID
from humps import pascalize
from importlib import import_module

from pydantic import BaseModel, ConfigDict, Field, field_validator

from memgpt.orm.sqlalchemy_base import SqlalchemyBase
from memgpt.orm.errors import NoResultFound

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from memgpt.orm.sqlalchemy_base import SqlalchemyBase

# from: https://gist.github.com/norton120/22242eadb80bf2cf1dd54a961b151c61


logger = getLogger(__name__)

def get_paired_model(model_name: str) -> "SqlalchemyBase":
    """gets a sqlalchemy model for a pydantic model"""
    model_name = pascalize(model_name).capitalize()
    Model = getattr(import_module("memgpt.orm.__all__"), model_name)
    if Model is None:
        raise AttributeError(f"SQL Model {model_name} not found")
    return Model

class MemGPTBase(BaseModel):
    """Base schema for MemGPT schemas (does not include model provider schemas, e.g. OpenAI)"""

    model_config = ConfigDict(
        # allows you to use the snake or camelcase names in your code (ie user_id or userId)
        populate_by_name=True,
        # allows you do dump a sqlalchemy object directly (ie PersistedAddress.model_validate(SQLAdress)
        from_attributes=True,
        # throw errors if attributes are given that don't belong
        extra="forbid",
    )

    # def __id_prefix__(self):
    #    raise NotImplementedError("All schemas must have an __id_prefix__ attribute!")

    @classmethod
    def generate_id_field(cls, prefix: Optional[str] = None) -> "Field":
        prefix = prefix or cls.__id_prefix__

        # TODO: generate ID from regex pattern?
        def _generate_id() -> str:
            return f"{prefix}-{uuid.uuid4()}"

        return Field(
            ...,
            description=cls._id_description(prefix),
            pattern=cls._id_regex_pattern(prefix),
            examples=[cls._id_example(prefix)],
            default_factory=_generate_id,
        )

    # def _generate_id(self) -> str:
    #    return f"{self.__id_prefix__}-{uuid.uuid4()}"

    @classmethod
    def _id_regex_pattern(cls, prefix: str):
        """generates the regex pattern for a given id"""
        return (
            r"^" + prefix + r"-"  # prefix string
            r"[a-fA-F0-9]{8}"  # 8 hexadecimal characters
            # r"[a-fA-F0-9]{4}-"  # 4 hexadecimal characters
            # r"[a-fA-F0-9]{4}-"  # 4 hexadecimal characters
            # r"[a-fA-F0-9]{4}-"  # 4 hexadecimal characters
            # r"[a-fA-F0-9]{12}$"  # 12 hexadecimal characters
        )

    @classmethod
    def _id_example(cls, prefix: str):
        """generates an example id for a given prefix"""
        return [prefix + "-123e4567-e89b-12d3-a456-426614174000"]

    @classmethod
    def _id_description(cls, prefix: str):
        """generates a factory function for a given prefix"""
        return f"The human-friendly ID of the {prefix.capitalize()}"

    @field_validator("id", check_fields=False, mode="before")
    @classmethod
    def allow_bare_uuids(cls, v, values):
        """to ease the transition to stripe ids,
        we allow bare uuids and convert them with a warning
        """
        _ = values  # for SCA
        if isinstance(v, UUID):
            logger.warning("Bare UUIDs are deprecated, please use the full prefixed id!")
            return f"{cls.__id_prefix__}-{v}"
        return v

    @property
    def __sqlalchemy_model__(self) -> "str":
        """The string representation of the matching sqlalchemy model. Must be declared on all pydantic base objects"""
        raise NotImplementedError

    def to_sqlalchemy(self, db_session: "Session") -> SqlalchemyBase:
        """convert the pydantic model to a sqlalchemy model"""
        SqlModel: "SqlalchemyBase" = get_paired_model(self.__sqlalchemy_model__)
        if self.id:
            try:
                return SqlModel.read(identifier=self.id, db_session=db_session)
            except NoResultFound:
                logger.info("Instance does not exist, creating new local instance.")
        return SqlModel(**self.model_dump(exclude_none=True))