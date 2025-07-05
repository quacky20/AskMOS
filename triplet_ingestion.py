from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from typing import List, Dict

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

AUTH = (USERNAME, PASSWORD)

class Neo4jTripletIngester:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        self.driver.close()
    
    def create_triplet_nodes_and_relationships(self, triplets: List[Dict]):
        with self.driver.session() as session:
            for triplet in triplets:
                subject = triplet.get('subject', '').strip()
                predicate = triplet.get('predicate', '').strip()
                obj = triplet.get('object', '').strip()
                
                if subject and predicate and obj:
                    session.run("""
                        MERGE (s:Entity {name: $subject})
                        MERGE (o:Entity {name: $object})
                        MERGE (s)-[r:RELATES {type: $predicate}]->(o)
                        """, 
                        subject=subject, 
                        object=obj, 
                        predicate=predicate
                    )
    
    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def get_graph_stats(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN 
                    count(n) as node_count,
                    count{()-[]->()} as relationship_count,
                    collect(distinct labels(n)) as node_labels
            """)
            return result.single()
    
    def query_graph(self, query: str):
        with self.driver.session() as session:
            result = session.run(query)
            return [record for record in result]
    
    def find_connections(self, entity_name: str, depth: int = 2):
        with self.driver.session() as session:
            query = f"""
                MATCH path = (start:Entity {{name: $entity_name}})-[*1..{depth}]-(connected)
                RETURN path, connected.name as connected_name, length(path) as path_length
            """
            result = session.run(query, entity_name=entity_name)
            return [record for record in result]

# def main():
#     # Sample triplets (replace with your actual triplets)
#     sample_triplets = [
#         {"subject": "John", "predicate": "works at", "object": "Google"},
#         {"subject": "John", "predicate": "lives in", "object": "San Francisco"},
#         {"subject": "John", "predicate": "lives with", "object": "his wife Sarah"},
#         {"subject": "Google", "predicate": "is", "object": "a technology company"},
#         {"subject": "Google", "predicate": "founded by", "object": "Larry Page and Sergey Brin"},
#         {"subject": "Sarah", "predicate": "teaches", "object": "mathematics"},
#         {"subject": "Sarah", "predicate": "teaches at", "object": "Stanford University"}
#     ]
    
#     # Initialize Neo4j connection
#     # Replace with your actual Neo4j credentials
#     ingester = Neo4jTripletIngester(
#         uri=URI,
#         username=USERNAME,
#         password=PASSWORD
#     )
    
#     try:
#         # CLEAR EXISTING DATA
#         # ingester.clear_database()
    
#         print("Ingesting triplets into Neo4j...")
#         ingester.create_triplet_nodes_and_relationships(sample_triplets)
        
#         stats = ingester.get_graph_stats()
#         print(f"Graph stats: {stats}")
        
#         print("\nExample queries:")
        
#         john_connections = ingester.find_connections("John")
#         print(f"John's connections: {len(john_connections)} paths found")
#         for conn in john_connections:
#             print(f"  - Connected to: {conn['connected_name']} (distance: {conn['path_length']})")

#         all_relationships = ingester.query_graph("""
#             MATCH (s:Entity)-[r]->(o:Entity)
#             RETURN s.name as subject, type(r) as predicate, o.name as object
#         """)
#         print(f"\nAll relationships:")
#         for rel in all_relationships:
#             print(f"  - {rel['subject']} --[{rel['predicate']}]--> {rel['object']}")
        
#         popular_entities = ingester.query_graph("""
#             MATCH (n:Entity)-[r]-()
#             RETURN n.name as entity, count(r) as connection_count
#             ORDER BY connection_count DESC
#             LIMIT 5
#         """)
#         print(f"\nMost connected entities:")
#         for entity in popular_entities:
#             print(f"  - {entity['entity']}: {entity['connection_count']} connections")
        
#     except Exception as e:
#         print(f"Error: {e}")
    
#     finally:
#         ingester.close()

if __name__ == "__main__":
    # main()
    pass