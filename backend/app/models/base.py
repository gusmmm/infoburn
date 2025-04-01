from bson import ObjectId
from pydantic import BaseModel, ConfigDict

class PyObjectId(ObjectId):
    """Custom type for handling MongoDB ObjectIds"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        """Validate and convert the value to ObjectId"""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception:
                raise ValueError("Invalid ObjectId")
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        """Define the Pydantic core schema for PyObjectId"""
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

class InfoBurnBaseModel(BaseModel):
    """Base model for InfoBurn models"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )