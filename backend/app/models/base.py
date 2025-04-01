from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            json_schema=core_schema.str_schema(),
        )
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class InfoBurnBaseModel(BaseModel):
    """
    Base model for all InfoBurn models.
    Implements common configuration and functionality.
    
    Attributes:
        model_config: Pydantic V2 configuration
    """
    model_config = ConfigDict(
        validate_assignment=True,
        validate_by_name=True,  # Replaces allow_population_by_field_name
        json_encoders={
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    )