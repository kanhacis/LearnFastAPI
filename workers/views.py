from fastapi import APIRouter, Depends, status, HTTPException
from mysql.connector import connection
from database import get_db
from .schemas import Worker, WorkingAreaInfo, WorkingAreaInfoUpdate
from users.schemas import UserResponse
from auth.views import get_current_user


worker_router = APIRouter()


## POST endpoint to complete worker profile
@worker_router.post("/worker/", status_code=status.HTTP_201_CREATED, tags=["Worker"])
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
@worker_router.post("/working_area_info/", status_code=status.HTTP_201_CREATED, tags=["Worker area information"])
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
    
    
## GET endpoint to view my working area info
@worker_router.get("/working_area_info/", status_code=status.HTTP_200_OK, tags=["Worker area information"])
def view_working_area_info(db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor(dictionary=True)
    
    get_query = """
        SELECT wai.* FROM working_area_info AS wai 
        JOIN worker AS w ON wai.worker_id = w.id
        JOIN profile AS p ON w.profile_id = p.id
        WHERE p.user_id = %s 
    """
    cursor.execute(get_query, (current_user["id"],))
    working_area_info_result = cursor.fetchall()
    
    if working_area_info_result:
        return working_area_info_result
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Working area info not found")


## PATCH endpoint to update working area info
@worker_router.patch("/working_area_info/", status_code=status.HTTP_200_OK, tags=["Worker area information"])
def update_working_area_info(data: WorkingAreaInfoUpdate, db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor()

    # Check if the worker and their working area info exist
    get_worker_info_query = """
        SELECT wai.id, wai.worker_id FROM working_area_info as wai
        JOIN worker as w ON wai.worker_id = w.id
        JOIN profile as p ON w.profile_id = p.id
        WHERE p.user_id = %s AND wai.id = %s
    """
    cursor.execute(get_worker_info_query, (current_user["id"], data.id))
    worker_info_result = cursor.fetchone()  # Fetch only one record
    
    # Before executing the update query, make sure there are no unread results
    cursor.fetchall()  # Consume remaining results, if any
    
    # If the worker's working area info exists, proceed with the update
    if worker_info_result:
        worker_id = worker_info_result[1] 
        
        # Prepare the update query based on provided fields
        update_query = "UPDATE working_area_info SET "
        update_fields = []
        update_values = []

        if data.name and data.name != "string":
            update_fields.append("name = %s")
            update_values.append(data.name)
        
        if data.rate_type and data.rate_type != "string":
            update_fields.append("rate_type = %s")
            update_values.append(data.rate_type)
        
        if data.rate and data.rate != "string":
            update_fields.append("rate = %s")
            update_values.append(data.rate)
        
        if data.description and data.description != "string":
            update_fields.append("description = %s")
            update_values.append(data.description)
        
        # If no fields to update, raise an exception
        if not update_fields:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        
        # Finalize the update query by adding the WHERE clause and worker_id
        update_query += ", ".join(update_fields) + " WHERE working_area_info.worker_id = %s AND working_area_info.id = %s"
        update_values.append(worker_id)  # Append worker_id to the list of values for the query
        update_values.append(data.id) # Append working area info id to the list of values for the query

        # Execute the final update query
        cursor.execute(update_query, tuple(update_values))
        db.commit()
        
        return {"detail": "Working area information updated successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No working area info found to update")


## DELETE endpoint to delete working area info
@worker_router.delete("/working_area_info/{id}", status_code=status.HTTP_200_OK, tags=["Worker area information"])
def delete_working_area_info(id: int, db: connection.MySQLConnection = Depends(get_db)):
    cursor = db.cursor()

    # Execute the DELETE query
    cursor.execute("DELETE FROM working_area_info WHERE id = %s", (id,))
    
    # Check the number of affected rows
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No working area info found with the given id")
    
    # Commit the transaction if a row was deleted
    db.commit()

    return {"detail": "Working area info successfully deleted"}

    