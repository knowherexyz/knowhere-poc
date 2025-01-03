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

        # Iterate through files and calculate data validity
        for input_filename in os.listdir(self.config['input_dir']):
            input_file = os.path.join(self.config['input_dir'], input_filename)
            if os.path.splitext(input_file)[1].lower() == '.json':
                with open(input_file, 'r') as f:
                    input_data = json.load(f)
                    schema_matches = self.validate_schema(input_data)

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
            'schema_matches': schema_matches,
        }

        # Additional metadata about the proof, written onchain
        self.proof_response.metadata = {
            'dlp_id': self.config['dlp_id'],
        }

        return self.proof_response

    def validate_schema(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data against the google-timeline schema using jsonschema.
        
        Args:
            input_data: The JSON data to validate
            
        Returns:
            bool: True if schema matches, False otherwise
        """
        try:
            # Load the schema
            schema_path = os.path.join(os.path.dirname(__file__), 'schemas', 'google-timeline.json')
            with open(schema_path, 'r') as f:
                schema = json.load(f)
                
            # Validate against schema
            jsonschema.validate(instance=input_data, schema=schema)
            return True
            
        except jsonschema.exceptions.ValidationError as e:
            logging.error(f"Schema validation error: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Schema validation failed")
            return False

