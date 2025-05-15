import streamlit as st
import re

from semantic import check_table_exists, validate_semantics
from lexer import lexer
from optimiser import SQLQueryOptimizer
from executor import execute_query_with_error_handling
from parser import SQLSyntaxParser

def extract_table_name(query):
    """Safely extract table name from SQL query using regex."""
    match = re.search(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def main():
    st.set_page_config(page_title="SQL Query Compiler", layout="wide")
    st.title("🔍 SQL Query Compiler & Optimizer")

    # Dropdown to select query type
    query_type = st.selectbox("Choose SQL Query Type", ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "JOIN"])
    
    # Text area for entering the SQL query
    query = st.text_area(f"📝 Enter your {query_type} SQL query:")

    if query:
        try:
            # Display original query
            st.subheader("🔹 Original Query")
            st.code(query, language='sql')

            # Phase 1: Lexical Analysis
            tokens = list(lexer(query))
            st.subheader("🧩 Lexical Analysis (Tokens):")
            st.json(tokens)

            # Phase 2: Syntax Analysis
            parser = SQLSyntaxParser(tokens)
            syntax_result = parser.parse()
            st.subheader("📐 Syntax Analysis:")
            st.write(syntax_result)

            # Phase 3: Optimization
            optimizer = SQLQueryOptimizer(query)
            optimized_query = optimizer.optimize()

            st.subheader("🚀 Optimized Query:")
            if optimized_query.strip() != query.strip():
                st.success("Query successfully optimized.")
                col1, col2 = st.columns(2)
                with col1:
                    st.caption("Original")
                    st.code(query, language='sql')
                with col2:
                    st.caption("Optimized")
                    st.code(optimized_query, language='sql')
            else:
                st.info("No optimizations were applied.")
                st.code(optimized_query, language='sql')

            # Phase 4: Semantic Analysis
            semantic_result = validate_semantics(optimized_query)
            st.subheader("🧠 Semantic Analysis:")
            st.write(semantic_result)

            # Phase 5: Execution (Only for SELECT queries)
            if optimized_query.strip().lower().startswith("select"):
                table_name = extract_table_name(optimized_query)

                if table_name:
                    if check_table_exists(table_name):
                        st.success(f"✅ Table '{table_name}' exists.")

                        result_df = execute_query_with_error_handling(optimized_query)
                        if isinstance(result_df, str):
                            st.error(result_df)
                        else:
                            st.subheader("📊 Query Result:")
                            st.dataframe(result_df)
                    else:
                        st.error(f"❌ Table '{table_name}' does not exist.")
                else:
                    st.error("⚠️ Could not extract table name from the query.")
            else:
                st.warning("⚠️ Only SELECT queries are executed. Other types are analyzed but not run.")

        except Exception as e:
            st.error(f"❗ Error during processing: {e}")
    else:
        st.info("🔎 Please enter a SQL query above to begin analysis.")

    # Displaying both original and optimized queries at the end
    if query and 'optimized_query' in locals():  # Ensure optimized_query exists
        st.subheader("Original Query:")
        st.code(query, language='sql')

        st.subheader("Optimized Query:")
        st.code(optimized_query, language='sql')

if __name__ == "__main__":
    main()
