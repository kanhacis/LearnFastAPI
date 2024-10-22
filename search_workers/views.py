from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from mysql.connector import connection

from database import get_db
from users.schemas import UserResponse
from auth.views import get_current_user


search_workers_router = APIRouter(
    tags=["Search workers"]
)


## Function to serialize the workers
def serialize_workers(results):
    workers = {}
    for row in results:
        email = row["email"]
        
        # If worker is not in the dictionary by email, add them
        if email not in workers:
            workers[email] = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "gender": row["gender"],
                "phone_number": row["phone_number"],
                "city": row["city"],
                "avg_stars": row["avg_stars"] if row["avg_stars"] else 0,
                "working_areas": []
            }
        
        # Append working area info to the worker
        workers[email]["working_areas"].append({
            "name": row["name"],
            "rate_type": row["rate_type"],
            "rate": row["rate"],
            "description": row["description"]
        })
        
    # Return the workers
    return workers


## Function to get working area info for the retrieved workers
def get_working_area_info(cursor, worker_ids):
    get_working_area_query = f"""
        SELECT 
            users.email, 
            profile.first_name, 
            profile.last_name, 
            profile.gender, 
            profile.phone_number, 
            profile.city, 
            working_area_info.name, 
            working_area_info.rate_type, 
            working_area_info.rate, 
            AVG(ratings.stars) AS avg_stars,
            working_area_info.description 
        FROM 
            users 
        JOIN 
            profile ON users.id = profile.user_id 
        JOIN 
            worker ON profile.id = worker.profile_id 
        JOIN 
            working_area_info ON worker.id = working_area_info.worker_id
        LEFT JOIN
            ratings ON worker.id = ratings.worker_id 
        WHERE 
            users.id IN ({', '.join([str(id) for id in worker_ids])})
        GROUP BY
            users.email, 
            profile.first_name, 
            profile.last_name, 
            profile.gender, 
            profile.phone_number, 
            profile.city, 
            working_area_info.name, 
            working_area_info.rate_type, 
            working_area_info.rate, 
            working_area_info.description;
    """ 
    
    cursor.execute(get_working_area_query)
    working_areas = cursor.fetchall() 
    
    return working_areas


## GET endpoint to search workers and filter ideal workers accordingly
@search_workers_router.get("/search_workers/", status_code=status.HTTP_200_OK)
def search_workers(
    db: connection.MySQLConnection = Depends(get_db),
    min_rate: Optional[float] = Query(None, description="Minimum rate for filtering"),
    max_rate: Optional[float] = Query(None, description="Maximum rate for filtering"),
    rate_type: Optional[str] = Query(None, description="Filter by rate type"),
    working_area_name: Optional[str] = Query(None, description="Filter by working area name"),
    gender: Optional[str] = Query(None, description="Filter by worker gender"),
    limit: int = Query(10, description="Limit the number of workers returned", gt=0),  # Default limit to 10
    page_no: int = Query(0, description="Number of workers to skip", ge=0),  # Default offset to 0
    current_user: UserResponse = Depends(get_current_user)
):
    cursor = db.cursor(dictionary=True)
    
    # Get current user city
    cursor.execute("SELECT city FROM profile WHERE user_id = %s", (current_user["id"],))
    curr_user_result = cursor.fetchone()
    
    # Base query to get distinct workers
    get_workers_query = """
        SELECT 
            users.id AS user_id,
            users.email,
            profile.first_name,
            profile.last_name,
            profile.gender,
            profile.phone_number,
            profile.city
        FROM 
            users 
        JOIN 
            profile ON users.id = profile.user_id 
        JOIN 
            worker ON profile.id = worker.profile_id 
        JOIN 
            working_area_info ON worker.id = working_area_info.worker_id
    """

    # List to store filters 
    filters = [] 

    # Add optional filters for working area info
    if min_rate is not None: 
        filters.append(f"working_area_info.rate >= {min_rate}") 
    if max_rate is not None: 
        filters.append(f"working_area_info.rate <= {max_rate}") 
    if rate_type:
        filters.append(f"working_area_info.rate_type = '{rate_type}'")
    if working_area_name:
        filters.append(f"working_area_info.name = '{working_area_name}'")
    if gender:
        filters.append(f"profile.gender = '{gender}'")
    
    # Add default filter by current user city and user role should be Worker
    if curr_user_result:
        city = curr_user_result["city"]
        email = current_user["email"]
        
        filters.append(f"profile.city = '{city}'") 
        filters.append(f"profile.role = 'Worker'")
        filters.append(f"users.email != '{email}'")

    # If there are any filters, append them to the query
    if filters:
        get_workers_query += " WHERE " + " AND ".join(filters)
    
    # Add pagination (LIMIT and OFFSET) to distinct workers
    get_workers_query += f" GROUP BY users.id LIMIT {limit} OFFSET {page_no * limit}"
    
    cursor.execute(get_workers_query)
    workers = cursor.fetchall()

    # If no workers are found, return an empty list
    if not workers:
        return []
    
    # Extract worker ids to fetch working area info for each
    worker_ids = [worker['user_id'] for worker in workers]
        
    # Call get_working_area_info() function to get the workers working areas informations
    working_areas = get_working_area_info(cursor, worker_ids)
        
    # Call serialize_workers() function to format the results
    result = serialize_workers(working_areas)
    
    # Return the list of workers with their respective working areas
    return list(result.values()) 
    
    