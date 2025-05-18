import mysql.connector
from db_config import get_connection
import pandas as pd

def execute_select_query(query):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=columns)
                return df
    except Exception as e:
        return f"Error executing SELECT: {str(e)}"

def execute_modify_query(query, operation):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()
                return f"{operation} successful, {cursor.rowcount} rows affected."
    except Exception as e:
        return f"Error executing {operation}: {str(e)}"

def execute_query(query):
    query_upper = query.strip().upper()
    if query_upper.startswith("SELECT"):
        return execute_select_query(query)
    elif query_upper.startswith("INSERT"):
        return execute_modify_query(query, "INSERT")
    elif query_upper.startswith("UPDATE"):
        return execute_modify_query(query, "UPDATE")
    elif query_upper.startswith("DELETE"):
        return execute_modify_query(query, "DELETE")
    else:
        return "Unsupported query type or invalid syntax."

# Example function to check tables in your database
def list_tables():
    query = "SHOW TABLES;"
    result = execute_select_query(query)
    if isinstance(result, pd.DataFrame):
        print("Tables in database:")
        print(result)
    else:
        print(result)

# Example usage
if __name__ == "__main__":
    list_tables()
