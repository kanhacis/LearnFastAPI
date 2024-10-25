from fastapi import APIRouter, Depends, status, HTTPException
import mysql.connector
from mysql.connector import connection
from database import get_db
from .schemas import (
    WorkingAreaInfo, WorkingAreaInfoUpdate, WorkerRating, 
    WorkerRatingUpdate
)
from users.schemas import UserResponse
from auth.views import get_current_user
from notification import worker_notifications, user_notifications


worker_router = APIRouter()


## POST Endpoint: Complete worker profile.
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


## POST Endpoint: Create working area info.
@worker_router.post("/working_area_info/", status_code=status.HTTP_201_CREATED, tags=["Worker area information"])
def create_working_area_info(
    data: WorkingAreaInfo, db: connection.MySQLConnection = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
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

 
## GET Endpoint: View working area info.
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

 
## PATCH Endpoint: Update working area info.
@worker_router.patch("/working_area_info/", status_code=status.HTTP_200_OK, tags=["Worker area information"])
async def update_working_area_info(
    data: WorkingAreaInfoUpdate, db: connection.MySQLConnection = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    cursor = db.cursor()

    # Check if the worker and their working area info exist
    get_worker_info_query = """
        SELECT wai.id, wai.worker_id FROM working_area_info as wai
        JOIN worker as w ON wai.worker_id = w.id
        JOIN profile as p ON w.profile_id = p.id
        WHERE p.user_id = %s AND wai.id = %s
    """
    await cursor.execute(get_worker_info_query, (current_user["id"], data.id))
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
        await cursor.execute(update_query, tuple(update_values))
        db.commit()
        
        return {"detail": "Working area information updated successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No working area info found to update")


## DELETE Endpoint: Delete working area info.
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


## POST Endpoint: User gives rating/stars to worker.
@worker_router.post("/worker_ratings/", status_code=status.HTTP_201_CREATED, tags=["Worker"])
async def worker_ratings(
    data: WorkerRating, db: connection.MySQLConnection = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    
    cursor = db.cursor() 
    
    try:
        await cursor.execute(
            "INSERT INTO ratings (user_id, worker_id, stars) VALUES (%s, %s, %s)",
            (current_user["id"], data.worker_id, data.stars)
        )
        
        if cursor.rowcount > 0:
            db.commit()
            return {"detail": "Rating created successfully"}

    except mysql.connector.IntegrityError as e:
        error_code = e.errno  # Error number from the exception
        
        if error_code == 1062:  # Duplicate entry error
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate entry: You have already rated this worker."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred."
            )
            
    except mysql.connector.DatabaseError as e:
        error_code = e.errno  # Error number from the exception
        
        if error_code == 3819:  # Check constraint is violated (stars count should be in the range to 1 to 5)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stars count should be in the range of 1 to 5"
            )
        
    
## PUT Endpoint: Update worker rating.
@worker_router.put("/worker_ratings/{worker_id}", status_code=status.HTTP_200_OK, tags=["Worker"])
def worker_ratings(
    worker_id: int, 
    data: WorkerRatingUpdate, 
    db: connection.MySQLConnection = Depends(get_db), 
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    cursor = db.cursor()
    
    try:
        cursor.execute(
            "UPDATE ratings SET stars = %s WHERE user_id = %s AND worker_id = %s",
            (data.stars, current_user["id"], worker_id)
        )
        
        if cursor.rowcount > 0:
            db.commit()
            return {"detail": "Rating updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No rating found to update with the worker id {worker_id}"
            )
        
    except mysql.connector.DatabaseError as e:
        error_code = e.errno  # Error number from the exception
        
        if error_code == 3819:  # Check constraint is violated (stars count should be in the range to 1 to 5)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stars count should be in the range of 1 to 5"
            )
            
        
## POST Endpoint: User sends a request to the worker.
@worker_router.post("/request_worker/", status_code=status.HTTP_201_CREATED, tags=["Worker"])
def request_worker(
    worker_id: int, db: connection.MySQLConnection = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    # Check if the user exists
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if the worker exists
    cursor = db.cursor()
    cursor.execute("SELECT id FROM worker WHERE id = %s", (worker_id,))
    current_worker = cursor.fetchall()
    
    if not current_worker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found")
    
    # Check if the user is sending the request again
    cursor.execute("SELECT status FROM worker_requests WHERE user_id = %s AND worker_id = %s LIMIT 1", 
                   (current_user["id"], worker_id))
    request_status = cursor.fetchall()
    
    if request_status and request_status[0][0] == "Pending":
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Please wait for worker response")
    
    # Insert new request
    cursor.execute(
        "INSERT INTO worker_requests (user_id, worker_id, status) VALUES (%s, %s, %s)", 
        (current_user["id"], worker_id, "Pending")
    )
    
    # Get the ID of the newly created worker_request
    worker_request_id = cursor.lastrowid

    if cursor.rowcount > 0:
        db.commit()

        # Notify the worker if they are connected to SSE
        if worker_id in worker_notifications:
            worker_notifications[worker_id].append(
                f"New request from User {current_user['id']} with Request ID {worker_request_id}"
            ) 
        
        return {"request_id": worker_request_id, "detail": "Request sent successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send request")

    
## PUT Endpoint: Worker accepts or rejects the request.
@worker_router.put("/request_worker/", status_code=status.HTTP_200_OK, tags=["Worker"])
def respond_to_request(
    request_id: int, response: str, 
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    cursor = db.cursor(dictionary=True)
    
    # Fetch the worker request id
    cursor.execute("SELECT id, status FROM worker_requests WHERE id = %s", (request_id,)) 
    worker_request = cursor.fetchall()
    
    if not worker_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if worker_request[0]["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Request already responded to")
    
    if response == "Accepted":
        # Update the worker_requests table with status accepted
        cursor.execute("UPDATE worker_requests SET status = %s WHERE id = %s", ("Accepted", request_id))
        db.commit()
        
        # Notify the worker if they are connected to SSE
        if request_id in user_notifications:
            user_notifications[request_id].append(
                f"Your request response is Accepted, with request ID {request_id}"
            ) 
      
    if response == "Rejected":
        # Update the worker_requests table with status rejected
        cursor.execute("UPDATE worker_requests SET status = %s WHERE id = %s", ("Rejected", request_id))
        db.commit()
        
        # Notify the worker if they are connected to SSE
        if request_id in user_notifications:
            user_notifications[request_id].append(
                f"Your request response is Rejected, with request ID {request_id}"
            ) 
            
    return {"message": f"Request {response}"} 
    
    
    