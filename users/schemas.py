from pydantic import BaseModel, EmailStr
from typing import Optional
from enums import GenderEnum, RoleEnum
    

class UserCreate(BaseModel):
    email: EmailStr
    password: str 
    
    
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    password: str 
    

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    gender: GenderEnum
    role: RoleEnum
    city: str
    location: str
    longitude: str
    latitude: str    
    
    
class ProfileUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    gender: Optional[GenderEnum]
    location: Optional[str]
    city: Optional[str]
    longitude: Optional[str]
    latitude: Optional[str]
    role: Optional[RoleEnum]