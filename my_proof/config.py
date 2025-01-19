from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """Global settings configuration using environment variables"""
    
    DLP_ID: int = Field(
        default=16,
        description="Data Liquidity Pool ID"
    )
    
    DLP_CONTRACT_ADDRESS: str = Field(
        default="0x3B826122C4EBc127cba30f1d69417743FE652B15",
        description="Ethereum address of the DLP contract",
        pattern="^0x[a-fA-F0-9]{40}$"
    )
    
    FILE_ID: Optional[int] = Field(
        default=0,
        description="File ID in the Vana data registry"
    )
    
    OWNER_ADDRESS: Optional[str] = Field(
        default=None,
        description="Ethereum address of the data owner",
        pattern="^0x[a-fA-F0-9]{40}$"
    )
    
    RPC_URL: str = Field(
        default="https://rpc.vana.org",
        description="Ethereum RPC endpoint URL",
        pattern="^https?://.*$"
    )
    
    INPUT_DIR: str = Field(
        default="/input",
        description="Directory containing input files to process"
    )
    
    OUTPUT_DIR: str = Field(
        default="/output",
        description="Directory where output files will be written"
    )
    
    # Database settings
    POSTGRES_URL: str = Field(
        default=None,
        description="PostgreSQL connection URL",
        pattern="^postgresql://.*$"
    )
    
    # Google OAuth
    GOOGLE_TOKEN: Optional[str] = Field(
        default=None,
        description="Google OAuth2 access token for user authentication",
        min_length=20
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings() 