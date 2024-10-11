from fastapi import APIRouter, Depends, HTTPException, status
from mysql.connector import connection
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


from .hashing import Hash
from .utils import create_access_token, verify_token
from database import get_db
from .schemas import Login


auth_router = APIRouter(
    tags=["Authentication"]
)


bearer_scheme = HTTPBearer()


## Function to get the current user
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    return verify_token(token.credentials, credentials_exception) 


@auth_router.post("/login")
def login(data: Login, db: connection.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s", (data.email,))
    result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    
    if not Hash.verify(data.password, result["password"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect password")

    access_token = create_access_token(data={"sub": result["email"], "id": result["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

