import re
from semantic import get_table_columns

class SQLQueryOptimizer:
    def __init__(self, query):
        self.original_query = query
        self.query = query
        self.steps = [("Original Query", query.strip())]

    def log_step(self, description):
        if self.steps[-1][1].strip() != self.query.strip():
            self.steps.append((description, self.query.strip()))

    def remove_where_1_equals_1(self):
        original = self.query
        self.query = re.sub(
            r'\bWHERE\s+1\s*=\s*1\s*(AND\s+)?', 'WHERE ', self.query, flags=re.IGNORECASE
        )
        self.query = re.sub(r'\bWHERE\s*(AND\s*)+', 'WHERE ', self.query, flags=re.IGNORECASE)
        self.query = re.sub(r'\bWHERE\s*($|;)', '', self.query, flags=re.IGNORECASE).strip()
        if self.query != original:
            self.log_step("Removed 'WHERE 1=1'")
        return self

    def remove_redundant_predicates(self):
        original = self.query
        self.query = re.sub(
            r'WHERE\s+(\w+)\s*>\s*(\d+)\s*AND\s*\1\s*>\s*(\d+)',
            lambda m: f"WHERE {m.group(1)} > {max(int(m.group(2)), int(m.group(3)))}",
            self.query,
            flags=re.IGNORECASE
        )
        if self.query != original:
            self.log_step("Simplified redundant predicates in WHERE clause")
        return self

    def remove_redundant_joins(self):
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
        original = self.query
        for rem in to_remove:
            self.query = self.query.replace(rem, '')
        if self.query != original:
            self.log_step("Removed redundant joins")
        return self

    def join_elimination(self):
        join_pattern = re.compile(r'JOIN\s+(\w+)(?:\s+(\w+))?', flags=re.IGNORECASE)
        joins = join_pattern.findall(self.query)

        table_alias_refs = set()
        for match in re.finditer(r'(\w+)\.\w+', self.query):
            table_alias_refs.add(match.group(1).lower())

        from_tables = re.findall(r'FROM\s+(\w+)(?:\s+(\w+))?', self.query, flags=re.IGNORECASE)
        for tbl, alias in from_tables:
            table_alias_refs.add((alias or tbl).lower())

        original = self.query
        for table, alias in joins:
            tbl_alias = alias.lower() if alias else table.lower()
            if tbl_alias not in table_alias_refs:
                join_clause_pattern = re.compile(
                    rf'JOIN\s+{table}(?:\s+{alias})?\s+ON\s+[^J]+', flags=re.IGNORECASE)
                self.query = join_clause_pattern.sub('', self.query)

        if self.query != original:
            self.log_step("Eliminated unused joins")
        return self

    def optimize_where_conditions(self):
        where_match = re.search(r'WHERE\s+(.+)', self.query, flags=re.IGNORECASE | re.DOTALL)
        if not where_match:
            return self

        original = self.query
        where_clause = where_match.group(1).strip()
        conditions = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
        seen = set()
        filtered_conditions = []
        for cond in conditions:
            normalized = cond.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                filtered_conditions.append(cond.strip())
        new_where = ' AND '.join(filtered_conditions)
        self.query = re.sub(r'WHERE\s+(.+)', f'WHERE {new_where}', self.query, flags=re.IGNORECASE | re.DOTALL)
        if self.query != original:
            self.log_step("Removed duplicate conditions from WHERE clause")
        return self

    def simplify_select_star(self):
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

        original = self.query
        self.query = pattern.sub(replacer, self.query)
        if self.query != original:
            self.log_step("Replaced SELECT * with explicit column names")
        return self

    def flatten_subqueries(self):
        pattern = re.compile(
            r'FROM\s+\(\s*SELECT\s+\*\s+FROM\s+(\w+)\s+WHERE\s+([^)]+?)\s*\)\s+(\w+)',
            flags=re.IGNORECASE
        )
        match = pattern.search(self.query)
        if match:
            original = self.query
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
            if self.query != original:
                self.log_step("Flattened subquery in FROM clause")
        return self

    def reorder_joins(self):
        join_pattern = re.compile(r'JOIN\s+(\w+)\s+ON\s+([^\s]+)\s*=\s*[^\s]+', flags=re.IGNORECASE)
        joins = join_pattern.findall(self.query)
        if joins:
            original = self.query
            joins = sorted(joins, key=lambda x: x[0].lower())
            join_clauses = [f'JOIN {table} ON {on_condition}' for table, on_condition in joins]
            first_join_match = join_pattern.search(self.query)
            if first_join_match:
                start = first_join_match.start()
                prefix = self.query[:start]
                suffix = join_pattern.sub('', self.query[start:])
                self.query = prefix + ' ' + ' '.join(join_clauses) + ' ' + suffix
            if self.query != original:
                self.log_step("Reordered joins alphabetically by table name")
        return self

    def convert_or_to_in(self):
        where_match = re.search(r'WHERE\s+(.+)', self.query, flags=re.IGNORECASE | re.DOTALL)
        if not where_match:
            return self

        original = self.query
        where_clause = where_match.group(1).strip()
        conditions = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
        new_conditions = []
        for cond in conditions:
            if ' OR ' in cond.upper():
                or_parts = re.split(r'\s+OR\s+', cond, flags=re.IGNORECASE)
                col_name = None
                values = []
                valid = True
                for part in or_parts:
                    m = re.match(r'(\w+)\s*=\s*(.+)', part.strip(), flags=re.IGNORECASE)
                    if m:
                        this_col = m.group(1)
                        val = m.group(2).strip()
                        if col_name is None:
                            col_name = this_col
                        elif col_name.lower() != this_col.lower():
                            valid = False
                            break
                        values.append(val)
                    else:
                        valid = False
                        break
                if valid and col_name and len(values) > 1:
                    new_conditions.append(f"{col_name} IN ({', '.join(values)})")
                else:
                    new_conditions.append(cond)
            else:
                new_conditions.append(cond)
        new_where = " AND ".join(new_conditions)
        self.query = re.sub(r'WHERE\s+(.+)', f'WHERE {new_where}', self.query, flags=re.IGNORECASE | re.DOTALL)
        if self.query != original:
            self.log_step("Converted OR chains to IN clauses")
        return self

    def optimize(self):
        return (
            self.remove_where_1_equals_1()
                .flatten_subqueries()
                .remove_redundant_predicates()
                .remove_redundant_joins()
                .join_elimination()
                .optimize_where_conditions()
                .simplify_select_star()
                .convert_or_to_in()
                .reorder_joins()
        )

    def get_steps(self):
        return self.steps
