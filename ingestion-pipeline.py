from dotenv import load_dotenv
import os
from triplet_extractor import TripletExtractor
from triplet_ingestion import Neo4jTripletIngester
import json

load_dotenv()

class TripletApp:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_username = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.neo4j_uri, self.neo4j_username, self.neo4j_password]):
            raise ValueError("Neo4j credentials not found in environment variables")

        self.extractor = TripletExtractor(api_key=self.groq_api_key)
        self.ingester = Neo4jTripletIngester(
            uri=self.neo4j_uri,
            username=self.neo4j_username,
            password=self.neo4j_password
        )
    
    def process_text(self, text, clear_db=False, model="meta-llama/llama-4-maverick-17b-128e-instruct"):
        try:
            # print("🔍 Extracting triplets from text...")
            # print(f"Text preview: {text[:200]}{'...' if len(text) > 200 else ''}")
            # print("-" * 50)
            
            triplets = self.extractor.extract_triplets(text, model=model)
            
            if not triplets:
                print("❌ No triplets extracted from the text")
                return {"triplets": [], "stats": None, "success": False}
            
            # print(f"Extracted {len(triplets)} triplets:")
            # for i, triplet in enumerate(triplets, 1):
            #     print(f"  {i}. {triplet.get('subject', 'N/A')} → {triplet.get('predicate', 'N/A')} → {triplet.get('object', 'N/A')}")
            
            # print("\nIngesting triplets into Neo4j...")

            if clear_db:
                print("Clearing existing database...")
                self.ingester.clear_database()

            self.ingester.create_triplet_nodes_and_relationships(triplets)

            stats = self.ingester.get_graph_stats()
            
            # print(f"Successfully ingested triplets!")
            # print(f"Graph Stats:")
            # print(f"   - Nodes: {stats['node_count']}")
            # print(f"   - Relationships: {stats['relationship_count']}")
            
            return {
                "triplets": triplets,
                "stats": stats,
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Error processing text: {e}")
            return {"triplets": [], "stats": None, "success": False, "error": str(e)}
    
    def query_graph(self, query):
        try:
            return self.ingester.query_graph(query)
        except Exception as e:
            print(f"❌ Error executing query: {e}")
            return []
    
    def find_entity_connections(self, entity_name, depth=2):
        try:
            return self.ingester.find_connections(entity_name, depth)
        except Exception as e:
            print(f"❌ Error finding connections for {entity_name}: {e}")
            return []
    
    def get_popular_entities(self, limit=10):
        query = f"""
            MATCH (n:Entity)-[r]-()
            RETURN n.name as entity, count(r) as connection_count
            ORDER BY connection_count DESC
            LIMIT {limit}
        """
        return self.query_graph(query)
    
    def get_all_relationships(self):
        query = """
            MATCH (s:Entity)-[r]->(o:Entity)
            RETURN s.name as subject, type(r) as predicate, o.name as object
        """
        return self.query_graph(query)
    
    def close(self):
        self.ingester.close()

def text_pipeline(file_name, passed):
    with open(file_name, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sample_text = data["text"]

    try:
        app = TripletApp()

        result = app.process_text(sample_text)
        
        if result["success"]:
            print("✅ Passed")
            passed = passed + 1
        
        else:
            print("❌ Failed to process text")
            if "error" in result:
                print(f"Error: {result['error']}")
    
    except Exception as e:
        print(f"❌ Application error: {e}")
    
    finally:
        if 'app' in locals():
            app.close()


# def main():
#     sample_text = """
#     About Us
#     Space Applications Centre (SAC) is an ISRO Centre located at Ahmedabad, dealing with a wide variety of themes from satellite payload development, operational data reception and processing to societal applications. SAC is responsible for the development, realization and qualification of communication, navigation, earth observation and planetary payloads and related data processing and ground systems in the areas of communications, broadcasting, remote sensing and disaster monitoring / mitigation. Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) is a Data Centre of Space Applications Centre (SAC) and has facility for satellite data reception, processing, analysis and dissemination. MOSDAC is operationally supplying earth observation data from Indian meteorology and oceanography satellites, to cater to national and international research requirements.
#     """
    
#     try:
#         app = TripletApp()

#         result = app.process_text(sample_text, clear_db=True)
        
#         if result["success"]:
#             print("\n" + "="*60)
#             print("🔍 EXPLORING THE KNOWLEDGE GRAPH")
#             print("="*60)
            
#             print("\n📋 All Relationships:")
#             relationships = app.get_all_relationships()
#             for rel in relationships[:10]:
#                 print(f"  • {rel['subject']} --[{rel['predicate']}]--> {rel['object']}")
            
#             if len(relationships) > 10:
#                 print(f"  ... and {len(relationships) - 10} more relationships")
            
#             print("\n🏆 Most Connected Entities:")
#             popular = app.get_popular_entities(5)
#             for entity in popular:
#                 print(f"  • {entity['entity']}: {entity['connection_count']} connections")
            
#             if popular:
#                 sample_entity = popular[0]['entity']
#                 print(f"\n🔗 Connections for '{sample_entity}':")
#                 connections = app.find_entity_connections(sample_entity, depth=2)
#                 for conn in connections[:5]:  # Show first 5
#                     print(f"  • Connected to: {conn['connected_name']} (distance: {conn['path_length']})")
        
#         else:
#             print("❌ Failed to process text")
#             if "error" in result:
#                 print(f"Error: {result['error']}")
    
#     except Exception as e:
#         print(f"❌ Application error: {e}")
    
#     finally:
#         if 'app' in locals():
#             app.close()

if __name__ == "__main__":

    directory = './mosdac_scraped'

    passed = 0
    total = 0

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            text_pipeline(filepath, passed)
            total = total + 1

    print (f"Passed {passed}/{total}")