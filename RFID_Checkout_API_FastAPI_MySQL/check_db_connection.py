import os
import pymysql
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load .env file
load_dotenv()

# Get DB_URL from .env or use default
db_url = os.getenv("DB_URL", "mysql+pymysql://root:1234@127.0.0.1:3306/rfid_dabase?charset=utf8mb4")

print(f"Checking connection for: {db_url}")

# Parse the URL
if "+pymysql" in db_url:
    url_str = db_url.replace("mysql+pymysql://", "mysql://")
else:
    url_str = db_url

parsed = urlparse(url_str)
host = parsed.hostname
port = parsed.port or 3306
user = parsed.username
password = parsed.password
db_name = parsed.path.lstrip('/')

try:
    # Connect to MySQL (without selecting DB first)
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        port=port,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    print("Successfully connected to MySQL server.")
    
    # Check if database exists
    cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
    result = cursor.fetchone()
    
    if result:
        print(f"Database '{db_name}' already exists.")
    else:
        print(f"Database '{db_name}' does not exist. Creating...")
        cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database '{db_name}' created successfully.")
        
    cursor.close()
    conn.close()

except Exception as e:
    print(f"Initial connection to {host} failed: {e}")
    if host == '127.0.0.1':
        print("Retrying with host='localhost'...")
        try:
             conn = pymysql.connect(
                host='localhost',
                user=user,
                password=password,
                port=port,
                charset='utf8mb4'
            )
             print("Successfully connected to MySQL server via localhost.")
             cursor = conn.cursor()
             cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
             if cursor.fetchone():
                 print(f"Database '{db_name}' already exists.")
             else:
                 print(f"Database '{db_name}' does not exist. Creating...")
                 cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                 print(f"Database '{db_name}' created successfully.")
             cursor.close()
             conn.close()
        except Exception as e2:
            print(f"Retry with localhost also failed: {e2}")

