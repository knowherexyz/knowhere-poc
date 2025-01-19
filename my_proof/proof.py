import hashlib
import json
import logging
import os

from my_proof.models.db import Contributions, Contributors
from my_proof.models.proof_response import ProofResponse
from my_proof.utils import scoring
from my_proof.utils.blockchain import BlockchainClient
from my_proof.utils.db import db
from my_proof.utils.google import extract_coordinates, get_google_user
from my_proof.utils.schema import validate_schema
from my_proof.config import settings


class Proof:
    def __init__(self):
        self.proof_response = ProofResponse(dlp_id=settings.DLP_ID)
        self.blockchain_client = BlockchainClient()

    def generate(self) -> ProofResponse:
        """Generate proofs for all input files."""
        logging.info("Starting proof generation")
        errors = []

        storage_user_hash = None
        if settings.GOOGLE_TOKEN:
            google_user = get_google_user()
            if google_user:
                storage_user_hash = hashlib.sha256(google_user.id.encode()).hexdigest()
                if not google_user.verified_email:
                    errors.append("UNVERIFIED_STORAGE_EMAIL")
            else:
                errors.append("UNVERIFIED_STORAGE_USER")
        else:
            errors.append("MISSING_STORAGE_TOKEN")

        # Get existing file count from blockchain
        existing_file_count = self.blockchain_client.get_contributor_file_count()
        if existing_file_count > 0:
            errors.append(f"DUPLICATE_CONTRIBUTION")

        # Iterate through files and calculate data validity
        for input_filename in os.listdir(settings.INPUT_DIR):
            logging.info(f"Checking file: {input_filename}")
            input_file = os.path.join(settings.INPUT_DIR, input_filename)

            if os.path.splitext(input_file)[1].lower() == '.json':
                with open(input_file, 'r') as f:
                    json_content = f.read()
                    logging.info(f"Validating file: {json_content[:50]}...")
                    input_data = json.loads(json_content)
                    schema_type, schema_matches = validate_schema(input_data)
                    if not schema_matches:
                        errors.append(f"INVALID_SCHEMA")
                        break
                    
                    coordinates = extract_coordinates(input_data, schema_type)
                    if len(coordinates) < scoring.MIN_COORDINATES:
                        errors.append(f"NOT_ENOUGH_DATA")
                        
                    # Save the contributor and coordinates to the database
                    with db.session() as session:
                        contributor = Contributors(
                            wallet_address=settings.OWNER_ADDRESS,
                            ip_address_hash=None, # TODO: Add ip address hash
                            storage_source="google-drive",
                            storage_user_id_hash=storage_user_hash
                        )
                        session.add(contributor)
                        session.commit()
                        unique_coordinates, duplicate_coordinates = db.batch_insert_coordinates(session, coordinates, contributor.id)

                        # Calculate proof-of-contribution scores
                        self.proof_response.ownership = 0
                        self.proof_response.quality = scoring.calculate_quality_score(len(coordinates)) if schema_matches else 0.0
                        self.proof_response.authenticity = 0
                        self.proof_response.uniqueness = unique_coordinates / (unique_coordinates + duplicate_coordinates)

                        # Calculate overall score. If uniqueness is high, give more weight to quality.
                        if self.proof_response.uniqueness > 0.5:
                            self.proof_response.score = 0.5 * self.proof_response.quality + 0.5 * self.proof_response.uniqueness
                        else:
                            self.proof_response.score = 0.005 * self.proof_response.quality + 0.995 * self.proof_response.uniqueness

                        # Additional (public) properties to include in the proof about the data
                        self.proof_response.attributes = {
                            'schema_type': schema_type,
                            'coordinates': len(coordinates),
                            'unique_coordinates': unique_coordinates,
                        }
                        
                        # Additional metadata about the proof, written onchain
                        self.proof_response.metadata = {
                            'schema_type': schema_type,
                        }
                        
                        self.proof_response.valid = len(errors) == 0
                        
                        # Save contribution to the database
                        contribution = Contributions(
                            contributor_id=contributor.id,
                            score=self.proof_response.score,
                            quality=self.proof_response.quality,
                            uniqueness=self.proof_response.uniqueness,
                            authenticity=self.proof_response.authenticity,
                            ownership=self.proof_response.ownership,
                            valid=self.proof_response.valid,
                            file_id=settings.FILE_ID,
                            coordinates=len(coordinates),
                            unique_coordinates=unique_coordinates,
                            errors=errors if len(errors) > 0 else None
                        )
                        session.add(contribution)
                        session.commit()
        
        # Only include errors if there are any
        if len(errors) > 0:
            self.proof_response.attributes['errors'] = errors

        return self.proof_response

