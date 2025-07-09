from langchain_groq import ChatGroq
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

class GraphRAG:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="meta-llama/llama-4-maverick-17b-128e-instruct",
            temperature=0.1
        )
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )

    def generate_cypher(self, query):
        prompt = f"""
You are an expert at querying a Neo4j knowledge graph.

Translate the following natural language question into a Cypher query.

- Nodes are labeled `Entity`
- Relationships are labeled `RELATES`, and each has an optional `type` property.
- Always use one relationship at a time in each MATCH clause. Avoid patterns that return a list of relationships.
- Use MATCH, WHERE, RETURN clauses only.
- Return the Cypher query only. No markdown, no explanation.

Question: "{query}"
Cypher:
"""
        raw_output = self.llm.invoke(prompt).content.strip()

        # Clean up markdown code block if present
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("`").split("\n", 1)[-1].strip()
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3].strip()

        return raw_output

    def run_cypher(self, cypher_query):
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [record.data() for record in result]

    def generate_answer(self, query, cypher_results):
        prompt = f"""
Based on the data returned from the knowledge graph below, answer the user's question:

Question: {query}
Graph Data: {cypher_results}
Answer:
"""
        return self.llm.invoke(prompt).content.strip()

    def process_query(self, user_query):
        cypher_query = self.generate_cypher(user_query)
        print(f"[Generated Cypher Query]\n{cypher_query}\n")

        try:
            result = self.run_cypher(cypher_query)
        except Exception as e:
            print(f"[Cypher Execution Error] {e}")
            raise

        if not result:
            return None  # return None to signal failure

        return self.generate_answer(user_query, result)

    def close(self):
        self.driver.close()