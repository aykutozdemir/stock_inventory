"""
Category repository for category data operations
"""
import logging
from typing import List, Dict, Any, Optional
from backend.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class CategoryRepository(BaseRepository):
    """Repository for category operations"""

    def __init__(self):
        super().__init__('categories')

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find category by name"""
        try:
            results = self.find_by_field('name', name)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error finding category by name: {e}")
            return None

    def search_by_name(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search categories by name (case-insensitive)"""
        try:
            query = "SELECT * FROM categories WHERE name LIKE ? ORDER BY name LIMIT ?"
            return self.execute_query(query, (f'%{search_term}%', limit))
        except Exception as e:
            logger.error(f"Error searching categories: {e}")
            return []

    def get_with_stock_count(self) -> List[Dict[str, Any]]:
        """Get all categories with their stock counts"""
        try:
            query = """
                SELECT c.*, COUNT(s.id) as stock_count
                FROM categories c
                LEFT JOIN stocks s ON c.id = s.category_id
                GROUP BY c.id
                ORDER BY c.name
            """
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting categories with stock count: {e}")
            return []

    def update_updated_at(self, category_id: int) -> bool:
        """Update the updated_at timestamp for a category"""
        try:
            query = "UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            return self.execute_update(query, (category_id,)) > 0
        except Exception as e:
            logger.error(f"Error updating category timestamp: {e}")
            return False

    def to_dict(self, record: Any) -> Dict[str, Any]:
        """Convert category record to dictionary"""
        if isinstance(record, dict):
            return record
        # If it's a sqlite3.Row object, convert to dict
        return dict(record) if hasattr(record, 'keys') else {}

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute custom query (helper method)"""
        from backend.models.database import execute_query
        return execute_query(query, params)

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute update query (helper method)"""
        from backend.models.database import execute_update
        return execute_update(query, params)
