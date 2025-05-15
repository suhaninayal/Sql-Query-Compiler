import mysql.connector
from db_config import get_connection
import re

def check_table_exists(table_name):
    conn = get_connection()
    if conn is None:
        return False
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_table_columns(table_name):
    conn = get_connection()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = [row[0] for row in cursor.fetchall()]
    conn.close()
    return columns

def get_column_data_type(table_name, column_name):
    conn = get_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table_name}")
    columns = cursor.fetchall()
    conn.close()
    for col in columns:
        if col[0] == column_name:
            return col[1]  # Return the data type
    return None

def check_column_exists(table_name, column_name):
    return column_name in get_table_columns(table_name)

def validate_column_data_type(table_name, column_name, value):
    column_type = get_column_data_type(table_name, column_name)
    if not column_type:
        return False
    
    # Check if the value is numeric
    if re.match(r'^\d+(\.\d+)?$', str(value)):
        return column_type.startswith("int") or column_type.startswith("decimal") or column_type.startswith("float")
    
    # Check if the value is a string
    if re.match(r'^".*"$', str(value)) or re.match(r"^'.*'$", str(value)):
        return column_type.startswith("char") or column_type.startswith("text")
    
    return True

def validate_semantics(query):
    query = query.strip().strip(';')
    tokens = query.upper().split()

    if query.upper().startswith("SELECT"):
        try:
            table_name = query.upper().split("FROM")[1].split()[0]
            if not check_table_exists(table_name):
                return f"Semantic Error: Table '{table_name}' does not exist."
            
            # Validate columns referenced in WHERE clause
            if "WHERE" in tokens:
                where_index = tokens.index("WHERE")
                for i in range(where_index + 1, len(tokens)):
                    if tokens[i] == "=" and not check_column_exists(table_name, tokens[i-1]):
                        return f"Semantic Error: Column '{tokens[i-1]}' does not exist in table '{table_name}'."
            
            return "Semantic Check Passed: SELECT"
        except:
            return "Semantic Error: Unable to extract table name from SELECT query."

    elif query.upper().startswith("INSERT INTO"):
        try:
            table_name = tokens[2]
            if not check_table_exists(table_name):
                return f"Semantic Error: Table '{table_name}' does not exist."
            return "Semantic Check Passed: INSERT"
        except:
            return "Semantic Error: Unable to extract table name from INSERT query."

    elif query.upper().startswith("UPDATE"):
        try:
            table_name = tokens[1]
            if not check_table_exists(table_name):
                return f"Semantic Error: Table '{table_name}' does not exist."
            
            # Validate columns referenced in SET clause
            if "SET" in tokens:
                set_index = tokens.index("SET")
                for i in range(set_index + 1, len(tokens)):
                    if tokens[i] == "=" and not check_column_exists(table_name, tokens[i-1]):
                        return f"Semantic Error: Column '{tokens[i-1]}' does not exist in table '{table_name}'."
            return "Semantic Check Passed: UPDATE"
        except:
            return "Semantic Error: Unable to extract table name from UPDATE query."

    elif query.upper().startswith("DELETE FROM"):
        try:
            table_name = tokens[2]
            if not check_table_exists(table_name):
                return f"Semantic Error: Table '{table_name}' does not exist."
            return "Semantic Check Passed: DELETE"
        except:
            return "Semantic Error: Unable to extract table name from DELETE query."

    elif query.upper().startswith("DROP TABLE"):
        try:
            table_name = tokens[2]
            if not check_table_exists(table_name):
                return f"Semantic Error: Table '{table_name}' does not exist."
            return "Semantic Check Passed: DROP"
        except:
            return "Semantic Error: Unable to extract table name from DROP query."

    elif "JOIN" in tokens:
        try:
            idx_join = tokens.index("JOIN")
            table1 = tokens[tokens.index("FROM") + 1]
            table2 = tokens[idx_join + 1]
            if not check_table_exists(table1) or not check_table_exists(table2):
                return f"Semantic Error: One or both tables in JOIN ('{table1}', '{table2}') do not exist."
            return "Semantic Check Passed: JOIN"
        except:
            return "Semantic Error: Unable to validate JOIN query."

    # WHERE condition semantic validation
    if "WHERE" in tokens:
        where_index = tokens.index("WHERE")
        table_name = tokens[tokens.index("FROM") + 1]  # Extract table name for validation
        for i in range(where_index + 1, len(tokens)):
            # Validate columns
            if tokens[i] == "=" and not check_column_exists(table_name, tokens[i-1]):
                return f"Semantic Error: Column '{tokens[i-1]}' does not exist in table '{table_name}'."
            # Validate data types for comparisons
            if tokens[i] == "=":
                left_value = tokens[i-1]
                right_value = tokens[i+1]
                if not validate_column_data_type(table_name, tokens[i-1], right_value):
                    return f"Semantic Error: Incompatible data types for comparison: '{left_value}' and '{right_value}'."
            
    return "Semantic Check Skipped: Unsupported query type."

