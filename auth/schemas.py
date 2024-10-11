from pydantic import BaseModel, EmailStr


## Login schema
class Login(BaseModel):
    email: EmailStr
    password: str
    
    
class Token(BaseModel):
    access_token: str
    token_type: str 
    
    
class TokenData(BaseModel):
    id: int | None = None
    email: str | None = None