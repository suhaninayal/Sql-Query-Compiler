import re

class SQLSyntaxParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.root = None  
        
    def parse_qualified_name(self):
        """
        Parses tokens like identifier(.identifier)+ into a single qualified name string.
        e.g. ['e', '.', 'dept_id'] -> 'e.dept_id'
        """
        if self.position >= len(self.tokens):
            return None

        if not re.match(r'^\w+$', self.tokens[self.position][1]):
            return None

        parts = [self.tokens[self.position][1]]
        self.position += 1

        while (self.position + 1 < len(self.tokens) and
               self.tokens[self.position][1] == '.' and
               re.match(r'^\w+$', self.tokens[self.position + 1][1])):
            parts.append(self.tokens[self.position + 1][1])
            self.position += 2

        return ".".join(parts)

    def build_parse_tree(self):
        if not self.tokens:
            return {"type": "Empty Query"}

        root = {"type": "SQL Query", "children": []}
        self.position = 0
        current_keyword = None

        while self.position < len(self.tokens):
            token_type, token_value = self.tokens[self.position]
            upper_value = token_value.upper()

            if upper_value in ["SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE", "JOIN", "ON"]:
                current_keyword = {"type": upper_value, "children": []}
                root["children"].append(current_keyword)
                self.position += 1
            else:
                qualified_name = self.parse_qualified_name()
                if qualified_name:
                    node = {"type": "qualified_name", "value": qualified_name}
                    if current_keyword:
                        current_keyword["children"].append(node)
                    else:
                        root["children"].append(node)
                else:
                    node = {"type": "token", "value": token_value}
                    if current_keyword:
                        current_keyword["children"].append(node)
                    else:
                        root["children"].append(node)
                    self.position += 1

        self.root = root
        return root

    def current_token(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def advance(self):
        self.position += 1

    def parse(self):
        if not self.tokens:
            return "No query provided."

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
        tokens_upper = [t[1].upper() for t in self.tokens]
        if "SELECT" in tokens_upper and "FROM" not in tokens_upper:
            return "Syntax Error: 'FROM' clause is missing in SELECT query."
        if "INSERT" in tokens_upper and "INTO" not in tokens_upper:
            return "Syntax Error: 'INTO' clause is missing in INSERT query."
        if "DELETE" in tokens_upper and "FROM" not in tokens_upper:
            return "Syntax Error: 'FROM' clause is missing in DELETE query."
        return None

    def check_for_unbalanced_parentheses(self):
        open_parentheses = sum(1 for t in self.tokens if t[1] == '(')
        close_parentheses = sum(1 for t in self.tokens if t[1] == ')')
        if open_parentheses != close_parentheses:
            return "Syntax Error: Unbalanced parentheses."
        return None

    def check_for_missing_commas(self):
        i = 0
        while i < len(self.tokens):
            pos = i
            if not re.match(r'^\w+$', self.tokens[pos][1]):
                i += 1
                continue
            parts = [self.tokens[pos][1]]
            pos += 1
            while (pos + 1 < len(self.tokens) and
                   self.tokens[pos][1] == '.' and
                   re.match(r'^\w+$', self.tokens[pos + 1][1])):
                parts.append(self.tokens[pos + 1][1])
                pos += 2

            next_start = pos
            if next_start < len(self.tokens):
                if next_start < len(self.tokens) and re.match(r'^\w+$', self.tokens[next_start][1]):
                    after_first_end = pos
                    if after_first_end < len(self.tokens):
                        if self.tokens[after_first_end][1] != ',':
                            # Exception for special tokens that can come after qualified names
                            skip_tokens = {'*', ',', 'FROM', 'WHERE', 'AND', 'OR', 'ON', 'INTO', 'SET', 'VALUES'}
                            prev_token = self.tokens[after_first_end - 1][1].upper() if after_first_end - 1 >= 0 else None
                            curr_token = self.tokens[after_first_end][1].upper()
                            if curr_token not in skip_tokens and prev_token not in skip_tokens:
                                return f"Syntax Error: Missing comma before '{self.tokens[after_first_end][1]}' at position {after_first_end}."
            i = pos
        return None

    # The rest of your parsing methods remain unchanged...

    def parse_select(self):
        tokens_upper = [t[1].upper() for t in self.tokens]
        if "FROM" not in tokens_upper:
            return "Syntax Error: 'FROM' clause is missing in SELECT query."

        if "WHERE" in tokens_upper:
            return self.pushdown_where("SELECT")

        if "GROUP BY" in tokens_upper:
            return self.parse_group_by()

        if "HAVING" in tokens_upper:
            return self.parse_having()

        return "SELECT query parsed successfully."

    def parse_insert(self):
        required = ["INSERT", "INTO", "VALUES"]
        tokens_upper = [t[1].upper() for t in self.tokens]
        for req in required:
            if req not in tokens_upper:
                return f"Syntax Error: '{req}' clause is missing in INSERT query."

        if "WHERE" in tokens_upper:
            return self.pushdown_where("INSERT")

        return "INSERT query parsed successfully."

    def parse_update(self):
        tokens_upper = [t[1].upper() for t in self.tokens]
        if "SET" not in tokens_upper:
            return "Syntax Error: 'SET' clause is missing in UPDATE query."

        if "WHERE" in tokens_upper:
            return self.pushdown_where("UPDATE")

        return "UPDATE query parsed successfully."

    def parse_delete(self):
        tokens_upper = [t[1].upper() for t in self.tokens]
        if "FROM" not in tokens_upper:
            return "Syntax Error: 'FROM' clause is missing in DELETE query."

        if "WHERE" in tokens_upper:
            return self.pushdown_where("DELETE")

        return "DELETE query parsed successfully."

    def parse_drop(self):
        if "TABLE" not in [t[1].upper() for t in self.tokens]:
            return "Syntax Error: 'TABLE' keyword missing in DROP query."
        return "DROP query parsed successfully."

    def parse_join(self):
        tokens_upper = [t[1].upper() for t in self.tokens]
        if "JOIN" not in tokens_upper:
            return "Syntax Error: JOIN clause missing."
        if "ON" not in tokens_upper:
            return "Syntax Error: ON clause missing in JOIN."

        if "WHERE" in tokens_upper:
            return self.pushdown_where("JOIN")

        return "JOIN query parsed successfully."

    def parse_where(self):
        where_index = [t[1].upper() for t in self.tokens].index("WHERE")
        if where_index + 1 >= len(self.tokens):
            return "Syntax Error: No condition specified after WHERE."

        return "WHERE clause parsed successfully."

    def pushdown_where(self, query_type):
        where_index = [t[1].upper() for t in self.tokens].index("WHERE")
        where_condition = self.tokens[where_index + 1:]
        predicate = " ".join([t[1] for t in where_condition])

        if query_type == "SELECT" and "FROM" in [t[1].upper() for t in self.tokens]:
            return f"Pushing WHERE condition into FROM: {predicate}"
        elif query_type == "INSERT":
            return f"Pushing WHERE condition into INSERT VALUES: {predicate}"
        elif query_type == "UPDATE" and "SET" in [t[1].upper() for t in self.tokens]:
            return f"Pushing WHERE condition into UPDATE: {predicate}"
        elif query_type == "DELETE" and "FROM" in [t[1].upper() for t in self.tokens]:
            return f"Pushing WHERE condition into DELETE: {predicate}"
        elif query_type == "JOIN" and "ON" in [t[1].upper() for t in self.tokens]:
            return f"Pushing WHERE condition into JOIN ON: {predicate}"

        return f"WHERE clause pushed down successfully for {query_type}."

    def parse_group_by(self):
        token_values = [t[1].upper() for t in self.tokens]
        try:
            group_by_index = token_values.index("GROUP BY")
        except ValueError:
            return "Syntax Error: GROUP BY clause not found."

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
        token_values = [t[1].upper() for t in self.tokens]
        if "GROUP BY" not in token_values:
            return "Syntax Error: HAVING clause cannot exist without GROUP BY."

        try:
            having_index = token_values.index("HAVING")
        except ValueError:
            return "Syntax Error: HAVING clause not found."

        if having_index + 1 >= len(self.tokens):
            return "Syntax Error: No condition specified for HAVING."

        return "HAVING clause parsed successfully."


# Example usage:
tokens = [
    ("SELECT", "SELECT"),
    ("*", "*"),
    ("FROM", "FROM"),
    ("(", "("),
    ("SELECT", "SELECT"),
    ("*", "*"),
    ("FROM", "FROM"),
    ("employees", "employees"),
    ("WHERE", "WHERE"),
    ("age", "age"),
    (">", ">"),
    ("30", "30"),
    (")", ")"),
    ("e", "e"),
    ("JOIN", "JOIN"),
    ("departments", "departments"),
    ("d", "d"),
    ("ON", "ON"),
    ("e", "e"),
    (".", "."),
    ("dept_id", "dept_id"),
    ("=", "="),
    ("d", "d"),
    (".", "."),
    ("dept_id", "dept_id"),
    ("JOIN", "JOIN"),
    ("salaries", "salaries"),
    ("s", "s"),
    ("ON", "ON"),
    ("e", "e"),
    (".", "."),
    ("emp_id", "emp_id"),
    ("=", "="),
    ("s", "s"),
    (".", "."),
    ("emp_id", "emp_id"),
    ("WHERE", "WHERE"),
    ("1", "1"),
    ("=", "="),
    ("1", "1"),
    ("AND", "AND"),
    ("age", "age"),
    (">", ">"),
    ("25", "25"),
    ("AND", "AND"),
    ("age", "age"),
    (">", ">"),
    ("30", "30"),
    ("AND", "AND"),
    ("e", "e"),
    (".", "."),
    ("emp_id", "emp_id"),
    ("=", "="),
    ("5", "5"),
    ("AND", "AND"),
    ("e", "e"),
    (".", "."),
    ("emp_id", "emp_id"),
    ("=", "="),
    ("5", "5"),
    (";", ";")
]

parser = SQLSyntaxParser(tokens)
print(parser.parse())

# To build and print parse tree as dict
parse_tree = parser.build_parse_tree()
import json
print(json.dumps(parse_tree, indent=2))
