# lexer.py
# Phase 1: Lexical Analysis - Tokenizing SQL query

import re

# Define token types
KEYWORDS = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP", "JOIN", "INNER", "LEFT", "RIGHT", "ON", "VALUES", "SET"]
OPERATORS = ["=", "<", ">", "<=", ">=", "<>", "LIKE", "AND", "OR", "NOT"]
PUNCTUATION = [",", "(", ")", "*", ";","."]

# Regular expressions for matching tokens
token_specification = [
    ('KEYWORD',     r'\b(?:' + '|'.join(KEYWORDS) + r')\b'),
    ('OPERATOR',    r'|'.join([re.escape(op) for op in OPERATORS])),
    ('PUNCTUATION', r'|'.join([re.escape(p) for p in PUNCTUATION])),
    ('IDENTIFIER',  r'[A-Za-z_][A-Za-z0-9_]*'),
    ('NUMBER',      r'\b\d+\b'),
    ('STRING',      r"'[^']*'"),
    ('WHITESPACE',  r'[ \t\r\n]+'),  
    ('MISMATCH',    r'.')            
]

# Combine all token patterns into one regex
master_pattern = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
compiled_regex = re.compile(master_pattern)

def lexer(query):
    """Lexical analyzer that yields tokens (type, value) from SQL query."""
    position = 0
    while position < len(query):
        match = compiled_regex.match(query, position)
        if match:
            token_type = match.lastgroup
            value = match.group(token_type)

            if token_type == 'WHITESPACE':
                position = match.end()
                continue
            elif token_type == 'MISMATCH':
                raise ValueError(f"Illegal character at position {position}: '{value}'")
            else:
                yield (token_type, value)

            position = match.end()
        else:
            raise ValueError(f"Illegal character at position {position}")
