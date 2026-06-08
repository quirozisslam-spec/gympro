import os
import pymysql
from pymysql.cursors import DictCursor

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "gympro"),
    "charset":  "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": False,
}

SECRET_KEY = os.getenv("SECRET_KEY", "gympro-v4-secret-2024")

def get_connection():
    return pymysql.connect(**DB_CONFIG)
