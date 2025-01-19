import json
import os
import logging
from typing import Dict, Any, Tuple

import jsonschema

def validate_schema(input_data: Dict[str, Any]) -> Tuple[str, bool]:
    """
    Validate input data against the google-timeline schema using jsonschema.
    
    Args:
        input_data: The JSON data to validate
        
    Returns:
        tuple[str, bool]: A tuple containing (schema_type, is_valid)
        where schema_type is either 'ios' or 'android'
        and is_valid indicates if the schema validation passed
    """
    try:
        schema_type = 'google-timeline-android.json'
        # iPhones only give the semanticSegments array
        if isinstance(input_data, list):
            schema_type = 'google-timeline-ios.json'
        
        # Load the schema
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', schema_type)
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            
        # Validate against schema
        jsonschema.validate(instance=input_data, schema=schema)
        return schema_type, True
        
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Schema validation error: {str(e)}")
        return schema_type, False
    except Exception as e:
        logging.error(f"Schema validation failed: {str(e)}")
        return schema_type, False
