import os
import sys
import json

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "HACKATHON", "SE", "BE"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from app.modules.ai_alerts.router import DecisionEventPayload
    
    schema = DecisionEventPayload.model_json_schema()
    
    output_file = os.path.join(os.path.dirname(__file__), "..", "03_decision_schema", "real_decision_event.schema.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
        
    print(f"Real schema exported to {output_file}")
except Exception as e:
    print(f"Error exporting schema: {e}")
