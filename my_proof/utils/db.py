"""Database connection and session management"""
import logging
from contextlib import contextmanager
from typing import Generator, List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert

from my_proof.models.db import Base, Coordinates
from my_proof.config import settings

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager"""
    def __init__(self):
        self._engine = None
        self._session_local = None
        self.init()

    def init(self) -> None:
        """Initialize database connection and create tables"""
        try:
            self._engine = create_engine(settings.POSTGRES_URL)
            Base.metadata.create_all(self._engine)
            self._session_local = sessionmaker(bind=self._engine)
            logger.info("Database initialized successfully")
        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations"""
        if not self._session_local:
            raise RuntimeError("Database not initialized. Call init() first.")

        session = self._session_local()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """Get a new database session"""
        if not self._session_local:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._session_local()

    def batch_insert_coordinates(self, session: Session, coordinates: List[Tuple[float, float]], contributor_id: int) -> Tuple[int, int]:
        """
        Batch insert coordinates with conflict handling.
        
        Args:
            session: SQLAlchemy session
            coordinates: List of (latitude, longitude) tuples
            contributor_id: ID of the contributor
            
        Returns:
            Tuple[int, int]: (successful inserts, duplicates skipped)
        """
        if not coordinates:
            return 0, 0
            
        # Prepare batch insert statement
        stmt = insert(Coordinates).values([
            {
                'latitude': lat,
                'longitude': lng,
                'contributor_id': contributor_id
            }
            for lat, lng in coordinates
        ])
        
        # Add ON CONFLICT DO NOTHING clause
        stmt = stmt.on_conflict_do_nothing(
            index_elements=['latitude', 'longitude']
        )
        
        # Execute and get results
        result = session.execute(stmt)
        inserted = result.rowcount
        skipped = len(coordinates) - inserted
        
        return inserted, skipped

# Global database instance
db = Database()