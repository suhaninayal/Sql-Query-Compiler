import mysql.connector

# Database connection details
host = 'localhost'  # Your host, e.g., 'localhost' or an IP address
user = 'root'  # Your MySQL username
password = '2004'  # Your MySQL password
database = 'sql_compiler'  # The database to connect to

def get_connection():
    """Establish a connection to the database."""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        print("Connection successful")
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
