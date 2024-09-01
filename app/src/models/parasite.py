from pydantic import BaseModel
from typing import List


class CorrectVersion(BaseModel):
    word: str
    incorrectUsage: str
    correctUsage: str


class Parasite(BaseModel):
    word: str
    correctVersions: List[CorrectVersion]
    filename: str
    id: int
