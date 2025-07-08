from groq import Groq
import json
import re
from dotenv import load_dotenv
import os

class TripletExtractor:
    def __init__(self, api_key=None):
        self.client = Groq(api_key=api_key) if api_key else Groq()
    
    def extract_triplets(self, text, model="meta-llama/llama-4-maverick-17b-128e-instruct"):      
        prompt = f"""Extract structured triplets (subject, predicate, object) from the following text. 
        
        IMPORTANT: Return ONLY a valid JSON array with no additional text, explanations, or formatting.
        
        Rules:
        1. Each triplet should be in the format: (subject, predicate, object)
        2. Subject and object should be nouns or objects or entities that can act as nodes of a graph database
        3. Predicate should be a verb or verb phrase or prepositions describing the relationship between two nodes of a graph database
        4. Extract only meaningful relationships
        5. Return ONLY the JSON array, nothing else
        
        Text: "{text}"
        
        Expected output format (return only this, no explanations):
        [{{"subject": "...", "predicate": "...", "object": "..."}}, {{"subject": "...", "predicate": "...", "object": "..."}}]
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured triplets from text for creation of graph databases. Always return valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_completion_tokens=1024,
                top_p=0.9,
                stream=False,
                stop=None,
            )
            
            response_content = completion.choices[0].message.content
            
            triplets = self._parse_triplets_from_response(response_content)
            return triplets
            
        except Exception as e:
            print(f"Error during API call: {e}")
            return []
    
    def _parse_triplets_from_response(self, response_content):
        try:
            # Method 1: Find JSON within ```json code blocks
            json_block_match = re.search(r'```json\s*(\[.*?\])\s*```', response_content, re.DOTALL)
            if json_block_match:
                json_str = json_block_match.group(1)
                triplets = json.loads(json_str)
                return triplets
            
            # Method 2: Find JSON within ``` code blocks (without json label)
            code_block_match = re.search(r'```\s*(\[.*?\])\s*```', response_content, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
                triplets = json.loads(json_str)
                return triplets
            
            # Method 3: Find any JSON array in the response
            json_match = re.search(r'\[(?:[^[\]]*|\[[^\]]*\])*\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                # Clean up the JSON string to remove any trailing incomplete parts
                json_str = self._clean_json_string(json_str)
                triplets = json.loads(json_str)
                return triplets
            
            # Method 4: Try to parse the entire response as JSON
            triplets = json.loads(response_content.strip())
            return triplets
        
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print("Could not parse JSON from response. Raw response:")
            print(response_content[:500] + "..." if len(response_content) > 500 else response_content)
            return []
        
    def _clean_json_string(self, json_str):
        lines = json_str.split('\n')
        cleaned_lines = []
        brace_count = 0
        
        for line in lines:
            cleaned_lines.append(line)
            brace_count += line.count('{') - line.count('}')

            if brace_count == 0 and ']' in line:
                break
        
        cleaned_json = '\n'.join(cleaned_lines)
        
        last_bracket = cleaned_json.rfind(']')
        if last_bracket != -1:
            cleaned_json = cleaned_json[:last_bracket + 1]
        
        return cleaned_json
    
    def format_triplets(self, triplets):
        if not triplets:
            return "No triplets extracted."
        
        formatted = "\nExtracted Triplets:\n" + "="*40 + "\n"
        for i, triplet in enumerate(triplets, 1):
            formatted += f"{i}. Subject: {triplet.get('subject', 'N/A')}\n"
            formatted += f"   Predicate: {triplet.get('predicate', 'N/A')}\n"
            formatted += f"   Object: {triplet.get('object', 'N/A')}\n"
            formatted += "-" * 30 + "\n"
        
        return formatted

if __name__ == "__main__":
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")

    extractor = TripletExtractor(api_key=api_key)
    
    sample_text = """
    About Us\nSpace Applications Centre (SAC) is an ISRO Centre located at Ahmedabad, dealing with a wide variety of themes from satellite payload development, operational data reception and processing to societal applications. SAC is responsible for the development, realization and qualification of communication, navigation, earth observation and planetary payloads and related data processing and ground systems in the areas of communications, broadcasting, remote sensing and disaster monitoring / mitigation. Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) is a Data Centre of Space Applications Centre (SAC) and has facility for satellite data reception, processing, analysis and dissemination. MOSDAC is operationally supplying earth observation data from Indian meteorology and oceanography satellites, to cater to national and international research requirements.
    """
    
    print("Sample Text:")
    print(sample_text)
    print("\n" + "="*50)
    
    triplets = extractor.extract_triplets(sample_text)
    print(extractor.format_triplets(triplets))