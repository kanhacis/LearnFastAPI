from enum import Enum


## Gender categories
class GenderEnum(str, Enum):
    Male = "Male"
    Female = "Female"
    Other = "Other"


## Role categories
class RoleEnum(str, Enum):
    User = "User"
    Worker = "Worker"
    
    
## Worker rate categories
class RateEnum(str, Enum):
    Per_hour = "Per_hour"
    Half_day = "Half_day"
    Full_day = "Full_day"
     