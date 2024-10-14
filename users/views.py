from fastapi import Depends, APIRouter, HTTPException, status
from database import get_db
from .schemas import UserCreate, UserProfile, ProfileUpdate, UserResponse
from mysql.connector import connection
from auth.hashing import Hash
from auth.views import get_current_user


user_router = APIRouter()

user_tags = ["User"]
profile_tags = ["Profile"]


## POST endpoint to create an user
@user_router.post("/user/", status_code=status.HTTP_201_CREATED, tags=user_tags)
def create_user(data: UserCreate, db: connection.MySQLConnection = Depends(get_db)):
    cursor = db.cursor()
    
    # Check if the email already exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
    result = cursor.fetchone()
    if result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    # Check the password length (it should be greater than or equals to 4 characters)
    if len(data.password) < 4:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password contains atleast 4 characters")
    
    # Insert the new user in the database
    cursor.execute("INSERT INTO users (email, password) VALUES(%s, %s)", (data.email, Hash.bcrypt(data.password)))
    db.commit()
    
    # Return the inserted user 
    return {"detail": "User created successfully"}
    

## GET endpoint to view the users
@user_router.get("/users/", status_code=status.HTTP_200_OK, tags=user_tags)
def all_users(db: connection.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    
    # Get all the users
    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()
    
    # If no users found
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    
    # Return the list of users
    return result


## POST endpoint to create user profile
@user_router.post("/profile/", status_code=status.HTTP_201_CREATED, tags=profile_tags)
def create_profile(data: UserProfile, db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor()
        
    # Check if the user profile already exists
    cursor.execute("SELECT id FROM profile WHERE user_id = %s", (current_user["id"],))
    result = cursor.fetchone()
    if result:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists")
    
    # Insert the new profile in the database
    insert_query = """
        INSERT INTO profile (user_id, first_name, last_name, phone_number, gender, role, city, address, longitude, latitude) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (
        current_user["id"], 
        data.first_name, 
        data.last_name, 
        data.phone_number, 
        data.gender, 
        data.role,
        data.city,
        data.address, 
        data.longitude, 
        data.latitude
    )) 

    # Commit the transaction
    db.commit()
    
    # Return the success message
    return {"detail": "Profile created successfully"}


## GET endpoint to view user profile
@user_router.get("/profile/", status_code=status.HTTP_200_OK, tags=profile_tags)
def view_profile(db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor(dictionary=True)
    
    # Check the user exist with this id or not
    cursor.execute("SELECT * FROM profile WHERE user_id = %s", (current_user["id"],))
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    
    # Return the user profile
    return result


## PATCH endpoint for user profile
@user_router.patch("/profile/", status_code=status.HTTP_200_OK, tags=profile_tags)
def update_profile(data: ProfileUpdate, db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor()

    # Check if the profile exists
    cursor.execute("SELECT id FROM profile WHERE user_id = %s", (current_user["id"],))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    
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
    
    if data.address and not data.address == "string":
        update_fields.append("address = %s")
        update_values.append(data.address)
        
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    # Finalize query and execute
    query += ", ".join(update_fields) + " WHERE user_id = %s"
    update_values.append(current_user["id"])

    cursor.execute(query, tuple(update_values))
    db.commit()

    return {"message": "Profile updated successfully"}
    

## DELETE endpoint for user profile
@user_router.delete("/profile/", status_code=status.HTTP_200_OK, tags=profile_tags)
def delete_profile(db: connection.MySQLConnection = Depends(get_db), current_user: UserResponse = Depends(get_current_user)):
    cursor = db.cursor()
    
    # Check if the profile exists
    cursor.execute("SELECT * FROM profile WHERE user_id = %s", (current_user["id"],))
    result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_data, detail="Profile not found")
    
    # Delete user profile from the database
    cursor.execute("DELETE FROM profile WHERE user_id = %s", (current_user["id"],))
    db.commit()
    
    # Return the success message
    return {"detail": "Profile deleted successfully"}


