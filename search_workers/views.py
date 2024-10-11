from fastapi import APIRouter, Depends, status, HTTPException, Query
from typing import Optional
from mysql.connector import connection

from database import get_db


search_workers_router = APIRouter(
    tags=["Search workers"]
)


@search_workers_router.get("/search_workers/", status_code=status.HTTP_200_OK)
def search_workers(
    db: connection.MySQLConnection = Depends(get_db),
    min_rate: Optional[float] = Query(None, description="Minimum rate for filtering"),
    max_rate: Optional[float] = Query(None, description="Maximum rate for filtering"),
    rate_type: Optional[str] = Query(None, description="Filter by rate type"),
    working_area_name: Optional[str] = Query(None, description="Filter by working area name"),
    gender: Optional[str] = Query(None, description="Filter by worker gender") 
):
    cursor = db.cursor(dictionary=True)
    
    # Base query
    get_query = """
        SELECT 
            users.email,
            profile.first_name,
            profile.last_name,
            profile.gender,
            working_area_info.name,
            working_area_info.rate_type,
            working_area_info.rate,
            working_area_info.description
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

    # Add optional filters 
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

    # If there are any filters, append them to the query
    if filters:
        get_query += " WHERE " + " AND ".join(filters)
    
    cursor.execute(get_query)
    results = cursor.fetchall() 
    
    workers = {}
    for row in results:
        email = row["email"]
        
        # If worker is not in the dictionary by email, add them
        if email not in workers:
            workers[email] = {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "gender": row["gender"],
                "working_areas": []
            }
        
        # Append working area info to the worker
        workers[email]["working_areas"].append({
            "name": row["name"],
            "rate_type": row["rate_type"],
            "rate": row["rate"],
            "description": row["description"]
        })
    
    # Convert the dictionary into a list of workers
    return list(workers.values())

    