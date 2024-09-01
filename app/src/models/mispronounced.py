from pydantic import BaseModel


class Mispronounced(BaseModel):
    id: int
    word: str
    filename: str
