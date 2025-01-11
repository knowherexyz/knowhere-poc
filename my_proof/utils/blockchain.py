import json
import os
from web3 import Web3
from typing import Dict, Any

class BlockchainClient:
    """Client for interacting with blockchain contracts."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the blockchain client.
        
        Args:
            config: Configuration dictionary containing RPC URL, contract address and owner address
        """
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config['rpc_url']))
        contract_path = os.path.join(os.path.dirname(__file__), '..', 'contracts', 'dlp-contract.json')
        with open(contract_path, 'r') as f:
            contract_abi = json.load(f)
            
        self.contract = self.w3.eth.contract(
            address=config['dlp_contract_address'],
            abi=contract_abi
        )

    def get_contributor_file_count(self) -> int:
        """
        Get the number of files contributed by the configured address.
        
        Returns:
            int: Number of files contributed by the address
        """
        try:
            if self.config['owner_address'] is None:
                raise ValueError("Owner address is not set")
            
            contributor_info = self.contract.functions.contributorInfo(
                Web3.to_checksum_address(self.config['owner_address'])
            ).call()
            return contributor_info[1]  # [contributorAddress, filesListCount]  
            
        except Exception as e:
            print(f"Error getting contributor file count: {str(e)}")
            return 0
