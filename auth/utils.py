from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends, status
from jwt import ExpiredSignatureError, InvalidTokenError
import jwt


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 7200


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract email and user_id from the token
        email: str = payload.get("sub")
        user_id: str = payload.get("id")
        
        # Validate that the necessary data is present
        if email is None or user_id is None:
            raise credentials_exception
    
        token_data = {"email": email, "id": user_id}
        return token_data

    except ExpiredSignatureError:
        # Handle expired token error with an appropriate response
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    except InvalidTokenError:
        # Handle general JWT errors 
        raise credentials_exception 
    

