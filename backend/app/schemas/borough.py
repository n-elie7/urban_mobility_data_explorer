from pydantic import BaseModel


# What we actually return when someone reads a borough
class BoroughResponse(BaseModel):
    borough_id: int
    name: str

    model_config = {"from_attributes": True}
