from flask import Flask, request, jsonify
from flask_cors import CORS
import networkx as nx
import matplotlib.pyplot as plt
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
    temperature=0.1,
)

def generate_cypher(nl_query):
    prompt = f"""
You are a Cypher expert. Convert the following natural language question into a single valid Cypher query.

Only output the query — do NOT add explanation, markdown, or commentary.

- Node Label: Entity
- Relationship: RELATES with a property `type`

Question: {nl_query}
"""
    response = llm.predict(prompt).strip()

    for line in response.splitlines():
        if line.strip().startswith("MATCH"):
            return response.strip()
    return ""

def run_cypher(cypher_query):
    with driver.session() as session:
        result = session.run(cypher_query)
        return [record.data() for record in result]

def generate_answer(question, graph_data):
    try:
        trimmed = graph_data[:5]
        graph_summary = json.dumps(trimmed, indent=2)

        prompt = f"""
You are an AI assistant helping users answer questions based on knowledge graph data.

Here is the user's question:
{question}

And here is relevant graph data (first 5 entries):
{graph_summary}

Based on the graph data, provide a direct and concise answer to the question above.
"""

        answer = llm.predict(prompt).strip()
        return answer if answer else "Sorry, I couldn't generate an answer from the current data."

    except Exception as e:
        return f"⚠️ Error generating answer: {str(e)}"


@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        cypher = generate_cypher(query)
        
        result = run_cypher(cypher)
        
        if result:
            final_answer = generate_answer(query, result)
            return jsonify({"answer": final_answer})
        else:
            return jsonify({"answer": "⚠️ No data found in the graph for this query."})
            
    except Exception as e:
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)