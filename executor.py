import mysql.connector
from db_config import get_connection
import pandas as pd
import re

def execute_query(query, db_path='database.db'):
    try:
        with mysql.connector.connect(db=db_path) as conn:
            result = pd.read_sql_query(query, conn)
            return result
    except Exception as e:
        print(f"Execution Error: {e}")
        return None

def execute_select_query(query):
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=columns)
                return df
    except Exception as e:
        return f"Error executing SELECT: {str(e)}"

def execute_insert_query(query):
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()
                return f"Inserted {cursor.rowcount} rows."
    except Exception as e:
        return f"Error executing INSERT: {str(e)}"

def execute_update_query(query):
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()
                return f"Updated {cursor.rowcount} rows."
    except Exception as e:
        return f"Error executing UPDATE: {str(e)}"

def execute_delete_query(query):
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            with conn.cursor() as cursor:
                cursor.execute(query)
                conn.commit()
                return f"Deleted {cursor.rowcount} rows."
    except Exception as e:
        return f"Error executing DELETE: {str(e)}"

# Handling Join Queries
def execute_join_query(query):
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            with conn.cursor() as cursor:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=columns)
                return df
    except Exception as e:
        return f"Error executing JOIN: {str(e)}"

# Helper function to handle subqueries
def execute_subquery(query):
    # Extract the subquery using regex or parsing (simple example here)
    subquery_pattern = r"\((SELECT.*)\)"
    match = re.search(subquery_pattern, query)
    if match:
        subquery = match.group(1)
        return execute_select_query(subquery)
    return None

def execute_query_with_subquery(query):
    # If a query contains a subquery, execute it first and replace it
    subquery_result = execute_subquery(query)
    if subquery_result is not None:
        # Replace subquery in the main query with the result or pass subquery output
        # For simplicity, just return subquery result here
        return subquery_result
    return execute_select_query(query)

def execute_query_with_error_handling(query):
    try:
        if query.upper().startswith("SELECT"):
            return execute_select_query(query)
        elif query.upper().startswith("INSERT"):
            return execute_insert_query(query)
        elif query.upper().startswith("UPDATE"):
            return execute_update_query(query)
        elif query.upper().startswith("DELETE"):
            return execute_delete_query(query)
        elif "JOIN" in query.upper():
            return execute_join_query(query)
        else:
            return "Unsupported query type or invalid syntax."
    except Exception as e:
        return f"Database query execution error: {str(e)}"
