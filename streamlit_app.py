import streamlit as st
import re

from semantic import check_table_exists, validate_semantics
from lexer import lexer
from optimiser import SQLQueryOptimizer
from executor import execute_query
from parser import SQLSyntaxParser

def extract_table_name(query):
    match = re.search(r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)', query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def main():
    st.set_page_config(page_title="SQL Query Compiler", layout="wide")
    st.title("🧠 SQL Query Compiler & Optimizer")

    query_type = st.selectbox("Choose SQL Query Type", ["SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "JOIN"])
    query = st.text_area(f"📝 Enter your {query_type} SQL query:")

    phases = [
        "Original Query",
        "Lexical Analysis",
        "Syntax Analysis",
        "Optimization",
        "Semantic Analysis",
        "Execution (SELECT only)"
    ]

    selected_phase = st.sidebar.selectbox("Select Compiler Phase to View", phases)

    if not query:
        st.info("🔎 Please enter a SQL query above to begin analysis.")
        return

    try:
        tokens = list(lexer(query))
        parser = SQLSyntaxParser(tokens)
        syntax_result = parser.parse()
        optimizer = SQLQueryOptimizer(query)
        optimizer.optimize()
        optimization_steps = optimizer.get_steps()
        optimized_query = optimization_steps[-1][1]
        semantic_result = validate_semantics(optimized_query)
        table_name = extract_table_name(optimized_query)
        execution_result = None
        if optimized_query.strip().lower().startswith("select") and table_name and check_table_exists(table_name):
            execution_result = execute_query(optimized_query)

        if selected_phase == "Original Query":
            st.subheader("🔹 Original Query")
            st.code(query, language='sql')

        elif selected_phase == "Lexical Analysis":
            st.subheader("🧩 Lexical Analysis (Tokens)")
            st.json(tokens)

        elif selected_phase == "Syntax Analysis":
            st.subheader("📐 Syntax Analysis")
            st.write(syntax_result)

        elif selected_phase == "Optimization":
            st.subheader("🚀 Optimized Query: Step-by-Step")
            for i, (desc, step_query) in enumerate(optimization_steps):
                with st.expander(f"Step {i + 1}: {desc}", expanded=(i == 0)):
                    st.code(step_query, language='sql')

        elif selected_phase == "Semantic Analysis":
            st.subheader("🧠 Semantic Analysis")
            st.write(semantic_result)

        elif selected_phase == "Execution (SELECT only)":
            st.subheader("📊 Execution (Only SELECT queries)")
            if not optimized_query.strip().lower().startswith("select"):
                st.warning("⚠️ Only SELECT queries are executed. Other types are analyzed but not run.")
            else:
                if not table_name:
                    st.error("⚠️ Could not extract table name from the query.")
                elif not check_table_exists(table_name):
                    st.error(f"❌ Table '{table_name}' does not exist.")
                else:
                    st.success(f"✅ Table '{table_name}' exists.")
                    if isinstance(execution_result, str):
                        st.error(execution_result)
                    else:
                        st.dataframe(execution_result)

        st.markdown("---")
        st.subheader("📄 Summary")
        st.code("Original Query:\n" + query, language='sql')
        st.code("Final Optimized Query:\n" + optimized_query, language='sql')

    except Exception as e:
        st.error(f"❗ Error during processing: {e}")

    st.markdown("---")
    st.caption("Developed by Suhani, Deepanshu, Unnati, Ankit – SQL Query Compiler")

if __name__ == "__main__":
    main()
