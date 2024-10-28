from auth.hashing import Hash


## Helper function to check if email already exists
def email_exists(cursor, email: str) -> bool:
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    return cursor.fetchone() is not None


## Helper function to validate password length
def validate_password_length(password: str) -> bool:
    return len(password) >= 4


## Helper function to insert a new user into the database
def insert_new_user(cursor, data):
    hashed_password = Hash.bcrypt(data.password)
    cursor.execute(
        "INSERT INTO users (email, password) VALUES (%s, %s)",
        (data.email, hashed_password),
    )
    return (
        cursor.lastrowid,
        cursor.rowcount,
    )  # Return new user ID and row count for success check


## Helper function to get all users
def list_all_users(cursor):
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


## Helper function to check if the user profile already exists
def profile_exists(cursor, user_id: int) -> bool:
    cursor.execute("SELECT id FROM profile WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


## Helper function to insert a new profile into the database
def insert_profile(cursor, user_id: int, data):
    insert_query = """
        INSERT INTO profile (user_id, first_name, last_name, phone_number, gender, role, city, location, longitude, latitude) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(
        insert_query,
        (
            user_id,
            data.first_name,
            data.last_name,
            data.phone_number,
            data.gender,
            data.role,
            data.city,
            data.location,
            data.longitude,
            data.latitude,
        ),
    )
    return (
        cursor.lastrowid,
        cursor.rowcount,
    )  # Return new profile ID and row count for success check


## Helper function to fetch user profile
def fetch_profile(cursor, current_user):
    cursor.execute("SELECT * FROM profile WHERE user_id = %s", (current_user["id"],))
    return cursor.fetchone()


## Helper function to delete user profile
def delete_user_profile(cursor, current_user):
    cursor.execute("DELETE FROM profile WHERE user_id = %s", (current_user["id"],))


## Helper function to update address
def update_live_address(cursor, current_user, city, location, longitude, latitude):
    update_address_query = """
        UPDATE profile SET city = %s, location = %s, longitude = %s, latitude = %s WHERE user_id = %s
    """

    cursor.execute(
        update_address_query, (city, location, longitude, latitude, current_user["id"])
    )
    return cursor.rowcount


## Helper function to get current user role
def get_curr_user_role(cursor, current_user):
    cursor.execute("SELECT role FROM profile WHERE user_id = %s", (current_user["id"],))
    return cursor.fetchall()


## Helper function to switch user role
def switch_user_role(cursor, current_user, role):
    cursor.execute(
        "UPDATE profile SET role = %s WHERE user_id = %s",
        (role, current_user["id"]),
    )
