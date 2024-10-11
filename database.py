# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# # MySQL Database URL
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@localhost/FastAPI"

# # Create the engine
# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# # Create a session for interacting with the DB
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Base class for our models
# Base = declarative_base()

# # Dependency for getting a DB session in FastAPI routes
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()



# database.py
import mysql.connector
from mysql.connector import pooling

# MySQL connection pooling for performance
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,
    pool_reset_session=True,
    host="localhost",
    database="FastAPI",
    user="root",
    password="root"
) 

# Dependency to get the connection for each request
def get_db():
    connection = connection_pool.get_connection()
    try:
        yield connection
    finally:
        connection.close()
