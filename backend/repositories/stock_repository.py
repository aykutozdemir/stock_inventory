"""
Stock repository for stock data operations
"""
import logging
from typing import List, Dict, Any, Optional
from backend.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class StockRepository(BaseRepository):
    """Repository for stock operations"""

    def __init__(self):
        super().__init__('stocks')

    def find_by_category(self, category_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Find stocks by category"""
        try:
            query = """
                SELECT s.*, c.name as category_name
                FROM stocks s
                LEFT JOIN categories c ON s.category_id = c.id
                WHERE s.category_id = ?
                ORDER BY s.name
            """
            params = [category_id]

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            return self.execute_query(query, tuple(params))
        except Exception as e:
            logger.error(f"Error finding stocks by category: {e}")
            return []

    def search_by_name(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search stocks by name with category information"""
        try:
            query = """
                SELECT s.*, c.name as category_name
                FROM stocks s
                LEFT JOIN categories c ON s.category_id = c.id
                WHERE s.name LIKE ?
                ORDER BY s.name
                LIMIT ?
            """
            return self.execute_query(query, (f'%{search_term}%', limit))
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []

    def get_all_with_categories(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all stocks with category information"""
        try:
            query = """
                SELECT s.*, c.name as category_name
                FROM stocks s
                LEFT JOIN categories c ON s.category_id = c.id
                ORDER BY s.name
            """

            if limit:
                query += " LIMIT ?"
                return self.execute_query(query, (limit,))
            else:
                return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting stocks with categories: {e}")
            return []

    def get_low_stock(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """Get stocks with low quantity"""
        try:
            query = """
                SELECT s.*, c.name as category_name
                FROM stocks s
                LEFT JOIN categories c ON s.category_id = c.id
                WHERE s.quantity <= ?
                ORDER BY s.quantity ASC
            """
            return self.execute_query(query, (threshold,))
        except Exception as e:
            logger.error(f"Error getting low stock items: {e}")
            return []

    def get_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Get stocks by location"""
        try:
            query = """
                SELECT s.*, c.name as category_name
                FROM stocks s
                LEFT JOIN categories c ON s.category_id = c.id
                WHERE s.location LIKE ?
                ORDER BY s.name
            """
            return self.execute_query(query, (f'%{location}%',))
        except Exception as e:
            logger.error(f"Error getting stocks by location: {e}")
            return []

    def update_quantity(self, stock_id: int, new_quantity: int) -> bool:
        """Update stock quantity"""
        try:
            data = {'quantity': new_quantity}
            return self.update(stock_id, data)
        except Exception as e:
            logger.error(f"Error updating stock quantity: {e}")
            return False

    def update_image_path(self, stock_id: int, image_path: str) -> bool:
        """Update stock image path"""
        try:
            data = {'image_path': image_path}
            return self.update(stock_id, data)
        except Exception as e:
            logger.error(f"Error updating stock image path: {e}")
            return False

    def get_stock_summary(self) -> Dict[str, Any]:
        """Get stock summary statistics"""
        try:
            # Total items count
            total_query = "SELECT COUNT(*) as total FROM stocks"
            total_result = self.execute_query(total_query)
            total_items = total_result[0]['total'] if total_result else 0

            # Total quantity sum
            quantity_query = "SELECT SUM(quantity) as total_quantity FROM stocks"
            quantity_result = self.execute_query(quantity_query)
            total_quantity = quantity_result[0]['total_quantity'] or 0 if quantity_result else 0

            # Categories count
            categories_query = "SELECT COUNT(DISTINCT category_id) as categories FROM stocks"
            categories_result = self.execute_query(categories_query)
            total_categories = categories_result[0]['categories'] if categories_result else 0

            # Low stock items (quantity <= 5)
            low_stock_query = "SELECT COUNT(*) as low_stock FROM stocks WHERE quantity <= 5"
            low_stock_result = self.execute_query(low_stock_query)
            low_stock_count = low_stock_result[0]['low_stock'] if low_stock_result else 0

            return {
                'total_items': total_items,
                'total_quantity': total_quantity,
                'total_categories': total_categories,
                'low_stock_count': low_stock_count
            }
        except Exception as e:
            logger.error(f"Error getting stock summary: {e}")
            return {
                'total_items': 0,
                'total_quantity': 0,
                'total_categories': 0,
                'low_stock_count': 0
            }

    def to_dict(self, record: Any) -> Dict[str, Any]:
        """Convert stock record to dictionary"""
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
