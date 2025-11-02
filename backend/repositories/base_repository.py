"""
Base repository class with common database operations
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from backend.models.database import get_db_connection, execute_query, execute_insert, execute_update

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository class with common CRUD operations"""

    def __init__(self, table_name: str):
        self.table_name = table_name

    def find_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find all records"""
        query = f"SELECT * FROM {self.table_name}"
        params = []

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        if offset:
            query += " OFFSET ?"
            params.append(offset)

        try:
            return execute_query(query, tuple(params))
        except Exception as e:
            logger.error(f"Error finding all records in {self.table_name}: {e}")
            return []

    def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Find record by ID"""
        try:
            results = execute_query(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error finding record by ID in {self.table_name}: {e}")
            return None

    def find_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """Find records by field value"""
        try:
            return execute_query(f"SELECT * FROM {self.table_name} WHERE {field} = ?", (value,))
        except Exception as e:
            logger.error(f"Error finding records by field in {self.table_name}: {e}")
            return []

    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """Create new record"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = tuple(data.values())

            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            return execute_insert(query, values)
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}: {e}")
            return None

    def update(self, id: int, data: Dict[str, Any]) -> bool:
        """Update record by ID"""
        try:
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            values = tuple(data.values()) + (id,)

            query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
            affected_rows = execute_update(query, values)
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error updating record in {self.table_name}: {e}")
            return False

    def delete(self, id: int) -> bool:
        """Delete record by ID"""
        try:
            affected_rows = execute_update(f"DELETE FROM {self.table_name} WHERE id = ?", (id,))
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error deleting record in {self.table_name}: {e}")
            return False

    def count(self) -> int:
        """Count total records"""
        try:
            results = execute_query(f"SELECT COUNT(*) as count FROM {self.table_name}")
            return results[0]['count'] if results else 0
        except Exception as e:
            logger.error(f"Error counting records in {self.table_name}: {e}")
            return 0

    def exists(self, id: int) -> bool:
        """Check if record exists"""
        try:
            results = execute_query(f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1", (id,))
            return len(results) > 0
        except Exception as e:
            logger.error(f"Error checking existence in {self.table_name}: {e}")
            return False

    @abstractmethod
    def to_dict(self, record: Any) -> Dict[str, Any]:
        """Convert record to dictionary"""
        pass
