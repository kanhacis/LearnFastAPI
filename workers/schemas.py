from pydantic import BaseModel
from enums import RateEnum


class WorkingAreaInfo(BaseModel):
    name: str
    rate_type: RateEnum
    rate: int
    description: str
     

class Worker(BaseModel):
    profile_id: int
