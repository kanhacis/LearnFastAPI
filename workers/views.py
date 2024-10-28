from fastapi import APIRouter, Depends, status, HTTPException
import mysql.connector
from mysql.connector import connection
from database import get_db
from .schemas import (
    WorkingAreaInfo,
    WorkingAreaInfoUpdate,
    WorkerRating,
    WorkerRatingUpdate,
)
from users.schemas import UserResponse
from auth.views import get_current_user
from notification import worker_notifications, user_notifications
from .services import (
    get_user_profile,
    is_worker_exists,
    create_worker_profile,
    get_worker_id_by_user_id,
    insert_working_area_info,
    get_working_area_info,
    check_worker_info,
    delete_working_area_info,
    create_worker_rating,
    fetch_worker_by_id,
    get_existing_request,
    insert_new_worker_request,
    update_worker_request_status,
    get_worker_request_status,
)


worker_router = APIRouter()

worker_tags = ["Worker"]
worker_area_info_tags = ["Worker area information"]


## POST Endpoint: Complete worker profile.
@worker_router.post("/worker/", status_code=status.HTTP_201_CREATED, tags=worker_tags)
async def create_worker(
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor(dictionary=True)

    profile_result = get_user_profile(cursor, current_user["id"])
    if not profile_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    if is_worker_exists(cursor, profile_result["id"]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Worker profile already exists"
        )

    if profile_result["role"] != "Worker":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User role must be 'Worker' to create a worker profile",
        )

    try:
        create_worker_profile(cursor, profile_result["id"])
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create worker profile: {str(e)}",
        )

    return {"detail": "Worker created successfully"}


## POST Endpoint: Create working area info.
@worker_router.post(
    "/working_area_info/",
    status_code=status.HTTP_201_CREATED,
    tags=worker_area_info_tags,
)
async def create_working_area_info(
    data: WorkingAreaInfo,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor(dictionary=True)

    worker_result = get_worker_id_by_user_id(cursor, current_user["id"])
    if not worker_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found, please create",
        )

    try:
        insert_working_area_info(cursor, worker_result["id"], data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create working area info: {str(e)}",
        )

    return {"detail": "Working area information created successfully"}


## GET Endpoint: View working area info.
@worker_router.get(
    "/working_area_info/", status_code=status.HTTP_200_OK, tags=worker_area_info_tags
)
async def view_working_area_info(
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor(dictionary=True)

    working_area_info_result = get_working_area_info(cursor, current_user)

    if working_area_info_result:
        return working_area_info_result
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Working area info not found"
        )


## PATCH Endpoint: Update working area info. *
@worker_router.patch(
    "/working_area_info/", status_code=status.HTTP_200_OK, tags=worker_area_info_tags
)
async def update_working_area_info(
    data: WorkingAreaInfoUpdate,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor()

    # Check if the worker and their working area info exist
    worker_info_result = check_worker_info(cursor, current_user, data)  # Fetch only one record

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        # Finalize the update query by adding the WHERE clause and worker_id
        update_query += (
            ", ".join(update_fields)
            + " WHERE working_area_info.worker_id = %s AND working_area_info.id = %s"
        )
        update_values.append(
            worker_id
        )  # Append worker_id to the list of values for the query
        update_values.append(
            data.id
        )  # Append working area info id to the list of values for the query

        # Execute the final update query
        cursor.execute(update_query, tuple(update_values))
        db.commit()

        return {"detail": "Working area information updated successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No working area info found to update",
        )


## DELETE Endpoint: Delete working area info.
@worker_router.delete(
    "/working_area_info/{id}",
    status_code=status.HTTP_200_OK,
    tags=worker_area_info_tags,
)
async def delete_working_area_info(
    id: int, db: connection.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor()

    affected_rows = delete_working_area_info(cursor, id)

    if affected_rows == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No working area info found with the given id",
        )

    db.commit()
    return {"detail": "Working area info successfully deleted"}


## POST Endpoint: User gives rating/stars to worker.
@worker_router.post(
    "/worker_ratings/", status_code=status.HTTP_201_CREATED, tags=worker_tags
)
async def worker_ratings(
    data: WorkerRating,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    cursor = db.cursor()

    try:
        # Using the helper function to handle the rating insertion and exceptions
        affected_rows = create_worker_rating(
            cursor, current_user["id"], data.worker_id, data.stars
        )

        if affected_rows > 0:
            db.commit()
            return {"detail": "Rating created successfully"}

        # Edge case: If no rows were affected (unlikely with successful insert), rollback.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create rating for unknown reasons.",
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rating: {str(e)}"
        )
        

## PUT Endpoint: Update worker rating. *
@worker_router.put(
    "/worker_ratings/{worker_id}", status_code=status.HTTP_200_OK, tags=worker_tags
)
async def worker_ratings(
    worker_id: int,
    data: WorkerRatingUpdate,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    cursor = db.cursor()

    try:
        cursor.execute(
            "UPDATE ratings SET stars = %s WHERE user_id = %s AND worker_id = %s",
            (data.stars, current_user["id"], worker_id),
        )

        if cursor.rowcount > 0:
            db.commit()
            return {"detail": "Rating updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No rating found to update with the worker id {worker_id}",
            )

    except mysql.connector.DatabaseError as e:
        error_code = e.errno  # Error number from the exception

        if (
            error_code == 3819
        ):  # Check constraint is violated (stars count should be in the range to 1 to 5)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stars count should be in the range of 1 to 5",
            )


## POST Endpoint: User sends a request to the worker.
@worker_router.post(
    "/request_worker/", status_code=status.HTTP_201_CREATED, tags=worker_tags
)
async def request_worker(
    worker_id: int,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Verify if the current user exists
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    cursor = db.cursor(dictionary=True)

    # Check if the specified worker exists
    worker = fetch_worker_by_id(cursor, worker_id)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found"
        )

    # Check if the user has already sent a request with "Pending" status
    existing_request = get_existing_request(cursor, current_user["id"], worker_id)
    if existing_request and existing_request["status"] == "Pending":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait for the worker's response before sending another request",
        )

    try:
        # Insert a new request and obtain the request ID
        request_id, affected_rows = insert_new_worker_request(
            cursor, current_user["id"], worker_id
        )

        if affected_rows > 0:
            db.commit()

            # Notify the worker if they are connected to SSE (Server-Sent Events)
            if worker_id in worker_notifications:
                worker_notifications[worker_id].append(
                    f"New request from User {current_user['id']} with Request ID {request_id}"
                )

            return {"request_id": request_id, "detail": "Request sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send request",
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to insert new request: {str(e)}",
        )


## PUT Endpoint: Worker accepts or rejects the request.
@worker_router.put("/request_worker/", status_code=status.HTTP_200_OK, tags=worker_tags)
async def respond_to_request(
    request_id: int,
    response: str,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor(dictionary=True)

    # Fetch the worker request id
    worker_request = get_worker_request_status()

    if not worker_request:
        raise HTTPException(status_code=404, detail="Request not found")

    if worker_request[0]["status"] != "Pending":
        raise HTTPException(status_code=400, detail="Request already responded to")

    # Update the worker_requests table with status
    try:
        update_worker_request_status(cursor, request_id, response)
        db.commit()

        # Notify the worker if they are connected to SSE
        if request_id in user_notifications:
            user_notifications[request_id].append(
                f"Your request response is {response}, with request ID {request_id}"
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update worker request status: {str(e)}",
        )

    return {"message": f"Request {response}"}
