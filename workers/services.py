import mysql.connector
from fastapi import status, HTTPException


## Helper function to fetch user profile
def get_user_profile(cursor, user_id: int):
    cursor.execute("SELECT id, role FROM profile WHERE user_id = %s", (user_id,))
    return cursor.fetchone()


## Helper function to check if worker already exists
def is_worker_exists(cursor, profile_id: int):
    cursor.execute("SELECT id FROM worker WHERE profile_id = %s", (profile_id,))
    return cursor.fetchone() is not None


## Helper function to insert a new worker profile
def create_worker_profile(cursor, profile_id: int):
    cursor.execute("INSERT INTO worker (profile_id) VALUES (%s)", (profile_id,))


## Helper function to get worker id by user id
def get_worker_id_by_user_id(cursor, user_id: int):
    cursor.execute(
        "SELECT id FROM worker WHERE profile_id = (SELECT id FROM profile WHERE user_id = %s)",
        (user_id,),
    )
    return cursor.fetchone()


## Helper function to insert new working area informations
def insert_working_area_info(cursor, worker_id: int, data):
    insert_query = """
        INSERT INTO working_area_info (worker_id, name, rate_type, rate, description) 
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(
        insert_query,
        (
            worker_id,
            data.name,
            data.rate_type,
            data.rate,
            data.description,
        ),
    )


## Helper function to get workers (working area informations)
def get_working_area_info(cursor, current_user):
    get_query = """
        SELECT wai.* FROM working_area_info AS wai 
        JOIN worker AS w ON wai.worker_id = w.id
        JOIN profile AS p ON w.profile_id = p.id
        WHERE p.user_id = %s 
    """
    cursor.execute(get_query, (current_user["id"],))
    return cursor.fetchall()


## Helper function to delete working area information
def delete_working_area_info(cursor, area_info_id: int):
    cursor.execute("DELETE FROM working_area_info WHERE id = %s", (area_info_id,))
    return cursor.rowcount  # Returns the number of affected rows


## Helper function to create worker rating (given by user)
def create_worker_rating(cursor, user_id: int, worker_id: int, stars: int):
    try:
        cursor.execute(
            "INSERT INTO ratings (user_id, worker_id, stars) VALUES (%s, %s, %s)",
            (user_id, worker_id, stars),
        )
        return cursor.rowcount  # Return the number of affected rows to check success

    except mysql.connector.IntegrityError as e:
        if e.errno == 1062:  # Duplicate entry error
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate entry: You have already rated this worker.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected integrity error occurred.",
            )

    except mysql.connector.DatabaseError as e:
        if e.errno == 3819:  # Check constraint violation for stars range
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stars count should be in the range of 1 to 5",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred.",
            )
            

## Helper function to fetch worker by ID
def fetch_worker_by_id(cursor, worker_id: int):
    cursor.execute("SELECT id FROM worker WHERE id = %s", (worker_id,))
    return cursor.fetchone()  # fetch one worker if exists


## Helper function to check for an existing "Pending" request
def get_existing_request(cursor, user_id: int, worker_id: int):
    cursor.execute(
        "SELECT status FROM worker_requests WHERE user_id = %s AND worker_id = %s LIMIT 1",
        (user_id, worker_id),
    )
    return cursor.fetchone()  # fetch one row with status if exists


## Helper function to insert a new request into the table
def insert_new_worker_request(cursor, user_id: int, worker_id: int):
    cursor.execute(
        "INSERT INTO worker_requests (user_id, worker_id, status) VALUES (%s, %s, %s)",
        (user_id, worker_id, "Pending"),
    )
    return cursor.lastrowid, cursor.rowcount  # return new request ID and rowcount to check success


## Helper function to get worker request status
def get_worker_request_status(cursor, request_id):
    cursor.execute(
        "SELECT status FROM worker_requests WHERE id = %s", (request_id,)
    )
    return cursor.fetchall()

## Helper function to update worker_requests status
def update_worker_request_status(cursor, request_id, response):
    cursor.execute(
            "UPDATE worker_requests SET status = %s WHERE id = %s",
            (response, request_id),
        )
