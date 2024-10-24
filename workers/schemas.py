from pydantic import BaseModel
from enums import RateEnum
from typing import Optional


class WorkingAreaInfo(BaseModel):
    name: str
    rate_type: RateEnum
    rate: int
    description: str
     

class WorkingAreaInfoUpdate(BaseModel):
    id: int
    name: Optional[str]
    rate_type: Optional[RateEnum]
    rate: Optional[int]
    description: Optional[str]


class Worker(BaseModel):
    profile_id: int


class WorkerRating(BaseModel):
    worker_id: int
    stars: int 
    
    
class WorkerRatingUpdate(BaseModel):
    stars: int
    
    