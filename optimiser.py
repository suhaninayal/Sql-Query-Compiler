import re
from semantic import get_table_columns

class SQLQueryOptimizer:
    def __init__(self, query):
        self.query = query

    def remove_where_1_equals_1(self):
        # Remove "WHERE 1=1" and clean up leftover AND or whitespace
        self.query = re.sub(
            r'\bWHERE\s+1\s*=\s*1\s*(AND\s+)?', 
            'WHERE ', 
            self.query, 
            flags=re.IGNORECASE
        )
        # Remove dangling WHERE with no conditions
        self.query = re.sub(r'\bWHERE\s*(AND\s*)+', 'WHERE ', self.query, flags=re.IGNORECASE)
        self.query = re.sub(r'\bWHERE\s*($|;)', '', self.query, flags=re.IGNORECASE).strip()
        return self

    def remove_redundant_predicates(self):
        # Remove redundant conditions like "age > 30 AND age > 25" keeping stricter
        self.query = re.sub(
            r'WHERE\s+(\w+)\s*>\s*(\d+)\s*AND\s*\1\s*>\s*(\d+)',
            lambda m: f"WHERE {m.group(1)} > {max(int(m.group(2)), int(m.group(3)))}",
            self.query,
            flags=re.IGNORECASE
        )
        return self

    def remove_redundant_joins(self):
        # Remove redundant joins on the same table with the same ON condition
        join_pattern = re.compile(
            r'(JOIN\s+(\w+)(?:\s+\w+)?\s+ON\s+([^\s]+)\s*=\s*([^\s]+))',
            flags=re.IGNORECASE
        )
        joins = join_pattern.findall(self.query)
        seen = set()
        to_remove = []
        for full_join, table, left_cond, right_cond in joins:
            key = (table.lower(), left_cond.lower(), right_cond.lower())
            if key in seen:
                to_remove.append(full_join)
            else:
                seen.add(key)
        for rem in to_remove:
            self.query = self.query.replace(rem, '')
        return self

    def optimize_where_conditions(self):
        # Remove duplicate simple conditions in WHERE clause (e.g. col=5 AND col=5)
        where_match = re.search(r'WHERE\s+(.+)', self.query, flags=re.IGNORECASE | re.DOTALL)
        if not where_match:
            return self

        where_clause = where_match.group(1).strip()
        # Split conditions by AND, ignoring parentheses and nested logic for simplicity
        conditions = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)

        # Normalize and remove duplicates
        seen = set()
        filtered_conditions = []
        for cond in conditions:
            normalized = cond.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                filtered_conditions.append(cond.strip())

        new_where = ' AND '.join(filtered_conditions)
        self.query = re.sub(r'WHERE\s+(.+)', f'WHERE {new_where}', self.query, flags=re.IGNORECASE | re.DOTALL)

        return self

    def simplify_select_star(self):
        # Replace SELECT * with actual column names using get_table_columns()
        pattern = re.compile(r'SELECT\s+\*\s+FROM\s+(\w+)', flags=re.IGNORECASE)
        def replacer(match):
            table = match.group(1)
            try:
                columns = get_table_columns(table)
                if columns:
                    return f"SELECT {', '.join(columns)} FROM {table}"
            except Exception:
                return match.group(0)
            return match.group(0)
        self.query = pattern.sub(replacer, self.query)
        return self

    def flatten_subqueries(self):
        # Flatten subqueries like: FROM (SELECT * FROM table WHERE cond) alias
        pattern = re.compile(
            r'FROM\s+\(\s*SELECT\s+\*\s+FROM\s+(\w+)\s+WHERE\s+([^)]+?)\s*\)\s+(\w+)',
            flags=re.IGNORECASE
        )

        match = pattern.search(self.query)
        if match:
            base_table = match.group(1)
            condition = match.group(2).strip()
            alias = match.group(3)

            self.query = pattern.sub(f'FROM {base_table} {alias}', self.query)

            if re.search(r'\bWHERE\b', self.query, flags=re.IGNORECASE):
                self.query = re.sub(
                    r'\bWHERE\b',
                    f'WHERE {alias}.{condition} AND',
                    self.query,
                    flags=re.IGNORECASE,
                    count=1
                )
                self.query = re.sub(r'AND\s+AND', 'AND', self.query)
            else:
                self.query += f' WHERE {alias}.{condition}'

            self.query = re.sub(r'WHERE\s+AND', 'WHERE', self.query)

        return self

    def reorder_joins(self):
        # Simple reorder by table name
        join_pattern = re.compile(r'JOIN\s+(\w+)\s+ON\s+([^\s]+)\s*=\s*[^\s]+', flags=re.IGNORECASE)
        joins = join_pattern.findall(self.query)

        if joins:
            joins = sorted(joins, key=lambda x: x[0].lower())
            join_clauses = [f'JOIN {table} ON {on_condition}' for table, on_condition in joins]
            first_join_match = join_pattern.search(self.query)
            if first_join_match:
                start = first_join_match.start()
                prefix = self.query[:start]
                suffix = join_pattern.sub('', self.query[start:])
                self.query = prefix + ' ' + ' '.join(join_clauses) + ' ' + suffix

        return self

    def optimize(self):
        return (
            self.remove_where_1_equals_1()
                .flatten_subqueries()
                .remove_redundant_predicates()
                .remove_redundant_joins()
                .optimize_where_conditions()
                .simplify_select_star()
                .reorder_joins()
                .query
        )


# Example usage
if __name__ == "__main__":
    query = """
    SELECT *
    FROM (
        SELECT *
        FROM employees
        WHERE age > 30
    ) e
    JOIN departments d ON e.dept_id = d.dept_id
    JOIN salaries s ON e.emp_id = s.emp_id
    WHERE 1=1
    AND age > 30
    AND emp_id = 5;
    """
    optimizer = SQLQueryOptimizer(query)
    optimized_query = optimizer.optimize()
    print("Original Query:\n", query)
    print("Optimized Query:\n", optimized_query)
