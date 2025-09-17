from pydantic import BaseModel, Field
from typing import List, Literal, Optional
AgeBand = Literal['7-10','11-13','14-19']
Mode = Literal['baseline','mid','post']
class AssessmentCreate(BaseModel):
    user_id: str
    age_band: AgeBand
    mode: Mode = 'baseline'
class NextItem(BaseModel):
    item_id: str
    format: Literal['likert','pictorial']
    stem: str
    options: List[str]
    domain: str
class ResponseIn(BaseModel):
    item_id: str
    category: int = Field(ge=0, le=4)
    rt_ms: Optional[int] = None
