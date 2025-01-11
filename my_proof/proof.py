import json
import logging
import os
from typing import Dict, Any
import jsonschema

from my_proof.models.proof_response import ProofResponse


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        """Generate proofs for all input files."""
        logging.info("Starting proof generation")

        schema_matches = False
        # Iterate through files and calculate data validity
        for input_filename in os.listdir(self.config['input_dir']):
            logging.info(f"Checking file: {input_filename}")
            input_file = os.path.join(self.config['input_dir'], input_filename)

            if os.path.splitext(input_file)[1].lower() == '.json':
                with open(input_file, 'r') as f:
                    json_content = f.read()
                    logging.info(f"Validating file: {json_content[:50]}...")
                    input_data = json.loads(json_content)
                    schema_type, schema_matches = self.validate_schema(input_data)

        # Calculate proof-of-contribution scores: https://docs.vana.org/vana/core-concepts/key-elements/proof-of-contribution/example-implementation
        self.proof_response.ownership = 0  # Does the data belong to the user? Or is it fraudulent?
        self.proof_response.quality = 1.0 if schema_matches else 0.0  # How high quality is the data?
        self.proof_response.authenticity = 0  # How authentic is the data is (ie: not tampered with)? (Not implemented here)
        self.proof_response.uniqueness = 0  # How unique is the data relative to other datasets? (Not implemented here)

        # Calculate overall score and validity
        self.proof_response.score = self.proof_response.quality
        self.proof_response.valid = self.proof_response.score >= 0.9

        # Additional (public) properties to include in the proof about the data
        self.proof_response.attributes = {
            'schema_type': schema_type,
            'schema_matches': schema_matches,
        }

        # Additional metadata about the proof, written onchain
        self.proof_response.metadata = {
            'dlp_id': self.config['dlp_id'],
        }

        return self.proof_response

    def validate_schema(self, input_data: Dict[str, Any]) -> tuple[str, bool]:
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
            schema_path = os.path.join(os.path.dirname(__file__), 'schemas', schema_type)
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

