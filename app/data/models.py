from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    """A MongoDB ObjectID."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class Choice(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    text: str = Field(...)
    is_ground_truth: bool = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UpdateAnswer(BaseModel):
    puzzleId: PyObjectId = Field(...)  # identifier for associated puzzle
    choiceId: PyObjectId = Field(...)  # identifier for selected choice

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Answer(UpdateAnswer):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")


# type aliases for activation records
Token = str
ActivationAndToken = list[int | Token]
ActivationRecord = list[ActivationAndToken | Token]


class PuzzleBasics(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    description: str | None = Field(None)
    choices: list[Choice] = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Puzzle(PuzzleBasics):
    activationRecords: list[ActivationRecord] = Field(...)
