import re
from semantic import get_table_columns

class SQLQueryOptimizer:
    def __init__(self, query):
        self.query = query

    def remove_where_1_equals_1(self):
        # Remove "WHERE 1=1"
        self.query = re.sub(r'\bWHERE\s+1\s*=\s*1\b', '', self.query, flags=re.IGNORECASE)
        return self

    def remove_redundant_predicates(self):
        # Remove redundant conditions like "age > 30 AND age > 25"
        self.query = re.sub(
            r'WHERE\s+(\w+)\s*>\s*(\d+)\s*AND\s*\1\s*>\s*(\d+)',
            lambda m: f"WHERE {m.group(1)} > {max(int(m.group(2)), int(m.group(3)))}",
            self.query,
            flags=re.IGNORECASE
        )
        return self

    def remove_redundant_joins(self):
        # Remove redundant self joins like "JOIN emp ON emp.id = emp.id"
        self.query = re.sub(
            r'JOIN\s+(\w+)\s+ON\s+\1\.\w+\s*=\s*\1\.\w+',
            '',
            self.query,
            flags=re.IGNORECASE
        )
        return self

    def optimize_where_conditions(self):
        # Merge duplicate conditions like "col = 5 AND col = 5"
        self.query = re.sub(
            r'WHERE\s+(\w+)\s*=\s*(\d+)\s+AND\s+\1\s*=\s*\2',
            r'WHERE \1 = \2',
            self.query,
            flags=re.IGNORECASE
        )
        return self

    def simplify_select_star(self):
        # Replace SELECT * with actual column names using get_table_columns()
        match = re.search(r'SELECT\s+\*\s+FROM\s+(\w+)', self.query, flags=re.IGNORECASE)
        if match:
            table = match.group(1)
            try:
                columns = get_table_columns(table)
                if columns:
                    column_str = ', '.join(columns)
                    self.query = re.sub(
                        r'SELECT\s+\*\s+FROM',
                        f"SELECT {column_str} FROM",
                        self.query,
                        flags=re.IGNORECASE
                    )
            except Exception:
                pass  # Fail silently if column lookup fails
        return self

    def prune_unused_columns(self):
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM\s+(\w+)', self.query, flags=re.IGNORECASE)
        if not select_match:
            return self

        select_cols = select_match.group(1).split(',')
        table = select_match.group(2).strip()
        try:
            all_columns = set(get_table_columns(table))
            if not all_columns:
                return self

            used_columns = set()

            # Check WHERE clause
            where_match = re.search(r'\bWHERE\s+(.+?)(?:GROUP BY|ORDER BY|$)', self.query, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1)
                tokens = re.findall(r'\b\w+\b', where_clause)
                used_columns |= set(tokens) & all_columns

            # Check JOIN clauses
            join_matches = re.findall(r'ON\s+([^\s=]+)\s*=\s*([^\s]+)', self.query, flags=re.IGNORECASE)
            for left, right in join_matches:
                used_columns |= {left.split('.')[-1], right.split('.')[-1]} & all_columns

            # Fall back to all columns if none found
            if not used_columns:
                used_columns = all_columns

            final_columns = ', '.join(sorted(used_columns))
            self.query = re.sub(
                r'SELECT\s+.+?\s+FROM',
                f'SELECT {final_columns} FROM',
                self.query,
                flags=re.IGNORECASE
            )

        except Exception:
            pass

        return self



    def flatten_subqueries(self):
        # Flatten subqueries in FROM clause: (SELECT * FROM table WHERE condition) alias
        pattern = re.compile(
            r'FROM\s+\(\s*SELECT\s+\*\s+FROM\s+(\w+)\s+WHERE\s+([^)]+?)\s*\)\s+(\w+)',
            flags=re.IGNORECASE
        )

        match = pattern.search(self.query)
        if match:
            base_table = match.group(1)
            condition = match.group(2).strip()
            alias = match.group(3)

            # Replace subquery with flat FROM clause
            self.query = pattern.sub(f'FROM {base_table} {alias}', self.query)

            # Push the WHERE condition outside
            if re.search(r'\bWHERE\b', self.query, flags=re.IGNORECASE):
                self.query = re.sub(
                    r'\bWHERE\b',
                    f'WHERE {alias}.{condition} AND',
                    self.query,
                    flags=re.IGNORECASE
                )
            else:
                self.query += f' WHERE {alias}.{condition}'

        return self

    def reorder_joins(self):
        # Reorder joins based on the table size and the filter conditions
        # (A more advanced optimizer would require statistics about table size, indexes, etc.)
        join_pattern = re.compile(r'JOIN\s+(\w+)\s+ON\s+([^\s]+)\s*=\s*[^\s]+')
        joins = join_pattern.findall(self.query)

        if joins:
            # Sort joins based on the table name (simplified; ideally should use stats like table size)
            # In reality, you would want to use stats on table size and indexing, but here we use table names as a proxy.
            joins = sorted(joins, key=lambda x: x[0])  # Example heuristic: sorting by table name
            
            # Rebuild the query with reordered joins
            join_clauses = [f'JOIN {table} ON {on_condition}' for table, on_condition in joins]
            self.query = re.sub(join_pattern, ' '.join(join_clauses), self.query)

        return self

    def optimize(self):
        # Apply all optimization passes
        return (
            self.remove_where_1_equals_1()
                .remove_redundant_predicates()
                .remove_redundant_joins()
                .optimize_where_conditions()
                .simplify_select_star()
                .flatten_subqueries()
                .reorder_joins()
                .query
        )


# Example usage
if __name__ == "__main__":
    query = "SELECT * FROM employees e JOIN departments d ON e.dept_id = d.dept_id JOIN salaries s ON e.emp_id = s.emp_id;"
    optimized = SQLQueryOptimizer(query).optimize()
    print("Original Query:", query)
    print("Optimized Query:", optimized)
