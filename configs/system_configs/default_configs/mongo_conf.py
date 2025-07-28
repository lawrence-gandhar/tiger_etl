from dotenv import load_dotenv
import os

load_dotenv()  # Loads variables from .env into environment

MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', '27017'))
MONGODB_DB = os.getenv('MONGODB_DB', 'tiger_etl_mongo_db')
MONGODB_USER = os.getenv('MONGODB_USER', 'admin')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', '1234')

MONGODB_URI = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}"
