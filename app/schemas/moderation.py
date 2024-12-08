from typing import List, Literal
from pydantic import BaseModel

class ModerationIssue(BaseModel):
    type: str
    severity: Literal["low", "medium", "high"]
    description: str

class ModerationResponse(BaseModel):
    status: Literal["flagged", "good_to_go"]
    issues: List[ModerationIssue] = []

class HTMLContent(BaseModel):
    content: str