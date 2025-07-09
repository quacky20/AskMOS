import streamlit as st
from RAG.graph_query_engine import GraphRAG
from RAG.semantic_rag.retriever_engine import SemanticRAG

# Initialize RAG Engines
graph_rag = GraphRAG()
semantic_rag = SemanticRAG()

# UI Setup
st.set_page_config(page_title="Smart RAG Assistant", layout="wide")
st.title("🧠 Smart AI Help Bot")

user_query = st.text_input("Ask your question here:")

if st.button("Get Answer") and user_query:
    st.markdown("### 💡 Answer")

    graph_answer, semantic_answer = None, None
    errors = []

    # Try Graph RAG
    try:
        graph_answer = graph_rag.process_query(user_query)
    except Exception as e:
        errors.append(f"Graph RAG failed: {e}")

    # Try Semantic RAG
    try:
        semantic_answer = semantic_rag.process_query(user_query)
    except Exception as e:
        errors.append(f"Semantic RAG failed: {e}")

    # Decision Logic
    if graph_answer and not semantic_answer:
        st.markdown("#### 📊 From Graph RAG")
        st.success(graph_answer)

    elif semantic_answer and not graph_answer:
        st.markdown("#### 📄 From Semantic RAG")
        st.success(semantic_answer)

    elif graph_answer and semantic_answer:
        combined_prompt = f"""
You are an intelligent assistant helping a user by combining structured data from a knowledge graph and unstructured data from semantic retrieval.

User Query: {user_query}

Answer from Knowledge Graph:
{graph_answer}

Answer from Semantic Retrieval:
{semantic_answer}

Provide a clear, helpful, and final response to the user:
"""
        try:
            final_answer = semantic_rag.llm.invoke(combined_prompt).content.strip()
            st.markdown("#### 🔁 Combined RAG Answer")
            st.success(final_answer)
        except Exception as e:
            errors.append(f"Final LLM generation failed: {e}")
            st.markdown("#### ⚠️ Partial Combined Results")
            st.markdown("**📊 Graph RAG:**")
            st.info(graph_answer)
            st.markdown("**📄 Semantic RAG:**")
            st.info(semantic_answer)

    else:
        st.error("❌ No answer could be generated from either system.")
        for err in errors:
            st.warning(err)

    # Optional Debug Output
    with st.expander("🛠 Debug Info"):
        st.markdown("**Graph RAG Raw Output**")
        st.code(graph_answer if graph_answer else "No answer from Graph RAG.", language="markdown")

        st.markdown("**Semantic RAG Raw Output**")
        st.code(semantic_answer if semantic_answer else "No answer from Semantic RAG.", language="markdown")

        if errors:
            st.markdown("**Errors:**")
            for err in errors:
                st.error(err)