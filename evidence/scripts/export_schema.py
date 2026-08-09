import os
import json

def generate_placeholder_schema():
    """
    This is a placeholder script for E-03.
    In a real scenario, this script would crawl the backend codebase
    (e.g., FastAPI, Express, or Spring Boot) and export the OpenAPI schema.
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "DecisionEvent",
        "type": "object",
        "properties": {
            "eventId": {
                "type": "string",
                "description": "Unique identifier for the event"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time"
            },
            "tripId": {
                "type": "string"
            },
            "riskScore": {
                "type": "number"
            },
            "actionTaken": {
                "type": "string"
            }
        },
        "required": ["eventId", "timestamp", "tripId"]
    }
    
    output_file = os.path.join(os.path.dirname(__file__), "..", "03_decision_schema", "decision_event.schema.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
        
    print(f"Placeholder schema exported to {output_file}")
    
if __name__ == "__main__":
    generate_placeholder_schema()
