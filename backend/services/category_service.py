"""
Category service for category business logic
"""
import logging
from typing import List, Dict, Any, Optional
from backend.repositories.category_repository import CategoryRepository
from backend.utils.validation import validate_category_data, ValidationError

logger = logging.getLogger(__name__)

class CategoryService:
    """Service for category business operations"""

    def __init__(self):
        self.repository = CategoryRepository()

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        try:
            return self.repository.get_with_stock_count()
        except Exception as e:
            logger.error(f"Error getting all categories: {e}")
            return []

    def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID with detailed statistics"""
        try:
            if not isinstance(category_id, int) or category_id <= 0:
                return None

            category = self.repository.find_by_id(category_id)
            if category:
                # Add detailed stock statistics
                stocks = self._get_stocks_for_category(category_id)
                category['stock_count'] = len(stocks)

                # Calculate comprehensive statistics
                total_quantity = sum(stock['quantity'] for stock in stocks)
                low_stock_items = sum(1 for stock in stocks if stock['quantity'] <= 5)

                # Group by unit for breakdown
                unit_breakdown = {}
                for stock in stocks:
                    unit = stock.get('unit', 'pcs')
                    if unit not in unit_breakdown:
                        unit_breakdown[unit] = {'count': 0, 'quantity': 0}
                    unit_breakdown[unit]['count'] += 1
                    unit_breakdown[unit]['quantity'] += stock['quantity']

                category['statistics'] = {
                    'total_items': len(stocks),
                    'total_quantity': total_quantity,
                    'low_stock_count': low_stock_items,
                    'unit_breakdown': unit_breakdown,
                    'items': stocks  # Include all stock items for detailed view
                }

            return category
        except Exception as e:
            logger.error(f"Error getting category by ID: {e}")
            return None

    def create_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new category"""
        try:
            # Validate input data
            validated_data = validate_category_data(data)

            # Check if category name already exists
            existing = self.repository.find_by_name(validated_data['name'])
            if existing:
                return {
                    'success': False,
                    'message': 'Category name already exists',
                    'data': None
                }

            # Create category
            category_id = self.repository.create(validated_data)
            if category_id:
                category = self.repository.find_by_id(category_id)
                return {
                    'success': True,
                    'message': 'Category created successfully',
                    'data': {'id': category_id, **category} if category else None
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create category',
                    'data': None
                }

        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def update_category(self, category_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update category"""
        try:
            # Validate input data
            validated_data = validate_category_data(data, update=True)

            # Check if category exists
            existing = self.repository.find_by_id(category_id)
            if not existing:
                return {
                    'success': False,
                    'message': 'Category not found',
                    'data': None
                }

            # Check if new name conflicts with existing category
            if 'name' in validated_data:
                name_check = self.repository.find_by_name(validated_data['name'])
                if name_check and name_check['id'] != category_id:
                    return {
                        'success': False,
                        'message': 'Category name already exists',
                        'data': None
                    }

            # Update category
            success = self.repository.update(category_id, validated_data)
            if success:
                # Update timestamp
                self.repository.update_updated_at(category_id)
                category = self.repository.find_by_id(category_id)

                return {
                    'success': True,
                    'message': 'Category updated successfully',
                    'data': category
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update category',
                    'data': None
                }

        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error updating category: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def delete_category(self, category_id: int) -> Dict[str, Any]:
        """Delete category"""
        try:
            # Check if category exists
            category = self.repository.find_by_id(category_id)
            if not category:
                return {
                    'success': False,
                    'message': 'Category not found',
                    'data': None
                }

            # Check if category has stocks
            from backend.repositories.stock_repository import StockRepository
            stock_repo = StockRepository()
            stocks = stock_repo.find_by_category(category_id)
            if stocks:
                return {
                    'success': False,
                    'message': f'Cannot delete category with {len(stocks)} stock item(s)',
                    'data': None
                }

            # Delete category
            success = self.repository.delete(category_id)
            if success:
                return {
                    'success': True,
                    'message': 'Category deleted successfully',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to delete category',
                    'data': None
                }

        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def search_categories(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search categories by name"""
        try:
            if not search_term or not search_term.strip():
                return self.get_all_categories()

            return self.repository.search_by_name(search_term.strip(), limit)
        except Exception as e:
            logger.error(f"Error searching categories: {e}")
            return []

    def _get_stocks_for_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Helper method to get stocks for a category"""
        try:
            from backend.repositories.stock_repository import StockRepository
            stock_repo = StockRepository()
            return stock_repo.find_by_category(category_id)
        except Exception as e:
            logger.error(f"Error getting stocks for category: {e}")
            return []
