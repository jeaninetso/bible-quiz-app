from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# Every response model mirrors the frontend's TS types field-for-field
# (including key casing) so the frontend's Zod schemas can validate this
# API's JSON with zero changes.


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str = Field(repr=False)  # never echoed back in logs/errors


class UserOut(CamelModel):
    username: str


class BookOut(CamelModel):
    id: int
    code: str
    name: str
    testament: str
    chapter_count: int
    is_available: bool


class PassageOut(CamelModel):
    reference: str
    text: str
