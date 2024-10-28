from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from database import get_db
from .schemas import UserCreate, UserProfile, ProfileUpdate, UserResponse
from mysql.connector import connection
from auth.hashing import Hash
from auth.views import get_current_user
from .utils import get_location
from .services import (
    email_exists,
    validate_password_length,
    insert_new_user,
    list_all_users,
    profile_exists,
    insert_profile,
    fetch_profile,
    delete_user_profile,
    update_live_address,
    get_curr_user_role,
    switch_user_role,
)


user_router = APIRouter()

user_tags = ["User"]
profile_tags = ["Profile"]


## POST Endpoint: Create an user.
@user_router.post("/user/", status_code=status.HTTP_201_CREATED, tags=user_tags)
async def create_user(
    data: UserCreate, db: connection.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor()

    try:
        # Check if the email already exists
        if email_exists(cursor, data.email):
            return JSONResponse(
                content={"detail": "Email already registered"},
                status_code=status.HTTP_409_CONFLICT,
            )

        # Validate password length
        if not validate_password_length(data.password):
            return JSONResponse(
                content={"detail": "Password must contain at least 4 characters"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Insert the new user and commit
        user_id, affected_rows = insert_new_user(cursor, data)
        if affected_rows > 0:
            db.commit()
            return JSONResponse(
                content={"detail": "User created successfully"},
                status_code=status.HTTP_201_CREATED,
            )
        else:
            return JSONResponse(
                content={"detail": "Something went wrong, Try again!"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        db.rollback()
        return JSONResponse(
            content={"detail": f"Failed to create new user: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


## GET Endpoint: List all users.
@user_router.get("/users/", status_code=status.HTTP_200_OK, tags=user_tags)
async def all_users(db: connection.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    # Get all the users
    result = list_all_users(cursor)

    # If no users found
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No users found"
        )

    # Return the list of users
    return result


## POST Endpoint: Create user profile.
@user_router.post("/profile/", status_code=status.HTTP_201_CREATED, tags=profile_tags)
async def create_profile(
    data: UserProfile,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor()

    try:
        # Check if the user profile already exists
        if profile_exists(cursor, current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Profile already exists"
            )

        # Insert the new profile into the database
        profile_id, affected_rows = insert_profile(cursor, current_user["id"], data)

        if affected_rows > 0:
            db.commit()
            return {"profile_id": profile_id, "detail": "Profile created successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create profile",
            )

    except Exception as e:
        db.rollback()  # Roll back transaction in case of any error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the profile: {str(e)}",
        )


## GET Endpoint: View user profile.
@user_router.get("/profile/", status_code=status.HTTP_200_OK, tags=profile_tags)
async def view_profile(
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor(dictionary=True)

    # Fetch user profile
    result = fetch_profile(cursor, current_user)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    # Return the user profile
    return result


## PATCH Endpoint: Update user profile.
@user_router.patch("/profile/", status_code=status.HTTP_200_OK, tags=profile_tags)
async def update_profile(
    data: ProfileUpdate,
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor()

    # Check if the profile exists
    if not profile_exists(cursor, current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    # Prepare the update query, checking if the fields are provided
    query = "UPDATE profile SET "
    update_fields = []
    update_values = []

    if data.first_name and not data.first_name == "string":
        update_fields.append("first_name = %s")
        update_values.append(data.first_name)

    if data.last_name and not data.last_name == "string":
        update_fields.append("last_name = %s")
        update_values.append(data.last_name)

    if data.phone_number and not data.phone_number == "string":
        update_fields.append("phone_number = %s")
        update_values.append(data.phone_number)

    if data.gender and not data.gender == "string":
        update_fields.append("gender = %s")
        update_values.append(data.gender)

    if data.location and not data.location == "string":
        update_fields.append("location = %s")
        update_values.append(data.location)

    if data.city and not data.city == "string":
        update_fields.append("city = %s")
        update_values.append(data.city)

    if data.longitude and not data.longitude == "string":
        update_fields.append("longitude = %s")
        update_values.append(data.longitude)

    if data.latitude and not data.latitude == "string":
        update_fields.append("latitude = %s")
        update_values.append(data.latitude)

    if data.role and not data.role == "string":
        update_fields.append("role = %s")
        update_values.append(data.role)

    # If no fields to update, raise an exception
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    # Finalize query and execute
    query += ", ".join(update_fields) + " WHERE user_id = %s"
    update_values.append(current_user["id"])

    cursor.execute(query, tuple(update_values))
    db.commit()

    return {"message": "Profile updated successfully"}


## DELETE Endpoint: Delete user profile.
@user_router.delete("/profile/", status_code=status.HTTP_200_OK, tags=profile_tags)
async def delete_profile(
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    cursor = db.cursor()

    # Check if the profile exists
    result = fetch_profile(cursor, current_user)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Profile not found"
        )

    try:
        # Delete user profile from the database
        delete_user_profile(cursor, current_user)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user profile: {str(e)}",
        )

    # Return the success message
    return {"detail": "Profile deleted successfully"}


## PUT Endpoint: Fetch user address using the ipinfo api and update it.
@user_router.put("/update_address/", status_code=status.HTTP_200_OK, tags=profile_tags)
async def update_address(
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    cursor = db.cursor()

    # Call get_location() to retrieve current user details
    address = get_location()

    if address is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve location data",
        )

    city, latitude, longitude, location = address

    try:
        rowcount = update_live_address(
            cursor, current_user, city, location, longitude, latitude
        )
        db.commit()

        if rowcount > 0:
            return {"detail": "User address updated successfully"}
        elif rowcount == 0:
            return {"detail": "Your address is up to date"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update live address: {str(e)}",
        )


## GET Endpoint: Fetch the current user address [city, latitude, longitude, location].
@user_router.get("/get_address/", status_code=status.HTTP_200_OK, tags=profile_tags)
async def get_address():
    # Call get_location() function (it returns city, latitude, longitude, and address)
    user_address = get_location()  # Renamed variable to avoid recursion

    if user_address is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve location data",
        )

    city, latitude, longitude, location = user_address

    response_data = {
        "city": city,
        "location": location,
        "longitude": longitude,
        "latitude": latitude,
    }

    return response_data


## PUT Endpoint: Update role in user profile (switch user role/type).
@user_router.put("/switch_role/", status_code=status.HTTP_200_OK, tags=profile_tags)
async def switch_role(
    db: connection.MySQLConnection = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    cursor = db.cursor(dictionary=True)

    # Get the current user role
    user_role = get_curr_user_role(cursor, current_user)

    # Change the user role in their profile table (Worker to User Or User to Worker)
    curr_user_role = user_role[0]["role"]

    try:
        if curr_user_role == "Worker":
            switch_user_role(cursor, current_user, "User")
            db.commit()
            return {"detail": "User profile switch to -User mode-"}
        else:
            switch_user_role(cursor, current_user, "Worker")
            db.commit()
            return {"detail": "User profile switch to -Worker mode-"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch user role: {str(e)}",
        )
