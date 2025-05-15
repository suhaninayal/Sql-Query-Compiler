import re

class SQLSyntaxParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def advance(self):
        self.position += 1

    def parse(self):
        if not self.tokens:
            return "No query provided."
        
        # Perform syntax checks
        error = self.check_for_missing_clauses()
        if error:
            return error

        error = self.check_for_unbalanced_parentheses()
        if error:
            return error
        
        error = self.check_for_missing_commas()
        if error:
            return error

        token_values = [t[1].upper() for t in self.tokens]

        if "SELECT" in token_values:
            return self.parse_select()
        elif "INSERT" in token_values:
            return self.parse_insert()
        elif "UPDATE" in token_values:
            return self.parse_update()
        elif "DELETE" in token_values:
            return self.parse_delete()
        elif "DROP" in token_values:
            return self.parse_drop()
        elif "JOIN" in token_values or "INNER" in token_values or "LEFT" in token_values or "RIGHT" in token_values:
            return self.parse_join()
        else:
            return "Unsupported query type."

    def check_for_missing_clauses(self):
        """Check for missing essential clauses like 'FROM' in SELECT."""
        if "SELECT" in [t[1].upper() for t in self.tokens] and "FROM" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'FROM' clause is missing in SELECT query."
        if "INSERT" in [t[1].upper() for t in self.tokens] and "INTO" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'INTO' clause is missing in INSERT query."
        if "DELETE" in [t[1].upper() for t in self.tokens] and "FROM" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'FROM' clause is missing in DELETE query."
        return None

    def check_for_unbalanced_parentheses(self):
        """Check for unbalanced parentheses."""
        open_parentheses = sum(1 for t in self.tokens if t[1] == '(')
        close_parentheses = sum(1 for t in self.tokens if t[1] == ')')
        
        if open_parentheses != close_parentheses:
            return "Syntax Error: Unbalanced parentheses."
        return None

    def check_for_missing_commas(self):
    
        for i in range(1, len(self.tokens) - 1):
            prev_token = self.tokens[i - 1][1]
            current_token = self.tokens[i][1]
            next_token = self.tokens[i + 1][1]

        # Skip if any token is a keyword or symbol
            skip_tokens = {'*', ',', 'FROM', 'WHERE', 'AND', 'OR', 'ON', 'INTO', 'SET', 'VALUES'}
            if current_token.upper() in skip_tokens or prev_token.upper() in skip_tokens or next_token.upper() in skip_tokens:
                continue

        # If three words appear in sequence without commas between them, raise an error
            if re.match(r'^\w+$', prev_token) and re.match(r'^\w+$', current_token) and re.match(r'^\w+$', next_token):
                return f"Syntax Error: Missing comma before '{current_token}' at position {i}."
        return None


    def parse_select(self):
        if "FROM" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'FROM' clause is missing in SELECT query."

        if "WHERE" in [t[1].upper() for t in self.tokens]:
            return self.pushdown_where("SELECT")
        
        if "GROUP BY" in [t[1].upper() for t in self.tokens]:
            return self.parse_group_by()
        
        if "HAVING" in [t[1].upper() for t in self.tokens]:
            return self.parse_having()

        return "SELECT query parsed successfully."

    def parse_insert(self):
        required = ["INSERT", "INTO", "VALUES"]
        for req in required:
            if req not in [t[1].upper() for t in self.tokens]:
                return f"Syntax Error: '{req}' clause is missing in INSERT query."
        
        if "WHERE" in [t[1].upper() for t in self.tokens]:
            return self.pushdown_where("INSERT")
        
        return "INSERT query parsed successfully."

    def parse_update(self):
        if "SET" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'SET' clause is missing in UPDATE query."

        if "WHERE" in [t[1].upper() for t in self.tokens]:
            return self.pushdown_where("UPDATE")
        
        return "UPDATE query parsed successfully."

    def parse_delete(self):
        if "FROM" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'FROM' clause is missing in DELETE query."
        
        if "WHERE" in [t[1].upper() for t in self.tokens]:
            return self.pushdown_where("DELETE")
        
        return "DELETE query parsed successfully."

    def parse_drop(self):
        if "TABLE" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'TABLE' keyword missing in DROP query."
        
        return "DROP query parsed successfully."

    def parse_join(self):
        if "JOIN" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: JOIN clause missing."
        if "ON" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: ON clause missing in JOIN."
        
        if "WHERE" in [t[1].upper() for t in self.tokens]:
            return self.pushdown_where("JOIN")
        
        return "JOIN query parsed successfully."

    def parse_where(self):
        where_index = [t[1].upper() for t in self.tokens].index("WHERE")
        if where_index + 1 >= len(self.tokens):
            return "Syntax Error: No condition specified after WHERE."
        
        where_condition = self.tokens[where_index + 1:]
        return "WHERE clause parsed successfully."

    def pushdown_where(self, query_type):
        """
        Push down the WHERE condition to an earlier point in the query if possible.
        Specifically, handle SELECT, INSERT, UPDATE, DELETE, JOIN queries.
        """
        where_index = [t[1].upper() for t in self.tokens].index("WHERE")
        where_condition = self.tokens[where_index + 1:]
        predicate = " ".join([t[1] for t in where_condition])  # Collect the WHERE condition

        # Handle SELECT queries: Push WHERE into the FROM clause if present
        if query_type == "SELECT":
            if "FROM" in [t[1].upper() for t in self.tokens]:
                return f"Pushing WHERE condition into FROM: {predicate}"

        # Handle INSERT queries: INSERT typically doesn't have WHERE, but we could handle it
        elif query_type == "INSERT":
            # Normally INSERT won't have WHERE, but if present, push it down.
            return f"Pushing WHERE condition into INSERT VALUES: {predicate}"

        # Handle UPDATE queries: Push WHERE condition into the UPDATE clause
        elif query_type == "UPDATE":
            if "SET" in [t[1].upper() for t in self.tokens]:
                return f"Pushing WHERE condition into UPDATE: {predicate}"

        # Handle DELETE queries: Push WHERE condition into DELETE
        elif query_type == "DELETE":
            if "FROM" in [t[1].upper() for t in self.tokens]:
                return f"Pushing WHERE condition into DELETE: {predicate}"

        # Handle JOIN queries: Move WHERE condition into the ON clause
        elif query_type == "JOIN":
            if "ON" in [t[1].upper() for t in self.tokens]:
                return f"Pushing WHERE condition into JOIN ON: {predicate}"

        return f"WHERE clause pushed down successfully for {query_type}."

    def parse_group_by(self):
        group_by_index = [t[1].upper() for t in self.tokens].index("GROUP BY")
        if group_by_index + 1 >= len(self.tokens):
            return "Syntax Error: No columns specified for GROUP BY."
        
        group_by_columns = self.tokens[group_by_index + 1:]
        for column in group_by_columns:
            if column[1].upper() in ['AND', 'ORDER', 'HAVING']:
                break
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column[1]):
                return f"Syntax Error: Invalid column name '{column[1]}' in GROUP BY."

        return "GROUP BY clause parsed successfully."

    def parse_having(self):
        if "GROUP BY" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: HAVING clause cannot exist without GROUP BY."

        having_index = [t[1].upper() for t in self.tokens].index("HAVING")
        if having_index + 1 >= len(self.tokens):
            return "Syntax Error: No condition specified for HAVING."
        
        having_condition = self.tokens[having_index + 1:]
        return "HAVING clause parsed successfully."


# Example usage:
tokens = [
    ("SELECT", "SELECT"),
    ("*", "*"),
    ("FROM", "FROM"),
    ("employees", "employees"),
    ("WHERE", "WHERE"),
    ("age", "age"),
    ("=", "="),
    ("30", "30")
]

parser = SQLSyntaxParser(tokens)
print(parser.parse())
