from fastapi import APIRouter, Depends, status, HTTPException
from mysql.connector import connection
from database import get_db
from .schemas import Worker, WorkingAreaInfo
from users.schemas import UserResponse
from auth.views import get_current_user


worker_router = APIRouter(
    tags=["Worker"]
)


## POST endpoint to complete worker profile
@worker_router.post("/worker/", status_code=status.HTTP_201_CREATED)
def create_worker(db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor(dictionary=True)
    
    # Check (user profile should be created, to create worker profile)
    cursor.execute("SELECT id, role FROM profile WHERE user_id = %s", (current_user["id"],))
    profile_result = cursor.fetchone()
    
    if profile_result:
        # Check if the worker already exists
        cursor.execute("SELECT id FROM worker WHERE profile_id = %s", (profile_result["id"],))
        worker_result = cursor.fetchone()
        
        if worker_result:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Worker already exist")
        else:
            # Check the user role, It should be set to "Worker"
            if profile_result["role"] == "Worker":
                # Insert the worker in the database
                cursor.execute("INSERT INTO worker (profile_id) VALUES (%s)", (profile_result["id"],))
                db.commit()
                
                # Return success message
                return {"detail": "Worker created successfully"}
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User role should be Worker, please edit")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found") 
    
    
## POST endpoint to create working area info
@worker_router.post("/working_area_info/", status_code=status.HTTP_201_CREATED)
def create_working_area_info(data: WorkingAreaInfo, db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT id FROM worker WHERE profile_id = (SELECT id FROM profile WHERE user_id = %s)", (current_user["id"],))
    worker_result = cursor.fetchone()
    
    if worker_result:
        insert_query = """
            INSERT INTO working_area_info (worker_id, name, rate_type, rate, description) VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (worker_result["id"], data.name, data.rate_type, data.rate, data.description)) 
        db.commit()
        
        return {"detail": "Working area information created successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found, please create")

