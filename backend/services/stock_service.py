"""
Stock service for stock business logic
"""
import logging
import os
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
from backend.repositories.stock_repository import StockRepository
from backend.repositories.category_repository import CategoryRepository
from backend.utils.validation import validate_stock_data, ValidationError
from backend.config import Config

logger = logging.getLogger(__name__)

class StockService:
    """Service for stock business operations"""

    def __init__(self):
        self.repository = StockRepository()
        self.category_repository = CategoryRepository()
        self.config = Config()

    def get_all_stocks(self, category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all stocks, optionally filtered by category"""
        try:
            if category_id:
                return self.repository.find_by_category(category_id)
            else:
                return self.repository.get_all_with_categories()
        except Exception as e:
            logger.error(f"Error getting all stocks: {e}")
            return []

    def get_stock_by_id(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """Get stock by ID with category information"""
        try:
            if not isinstance(stock_id, int) or stock_id <= 0:
                return None

            stocks = self.repository.get_all_with_categories()
            for stock in stocks:
                if stock['id'] == stock_id:
                    return stock

            return None
        except Exception as e:
            logger.error(f"Error getting stock by ID: {e}")
            return None

    def create_stock(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new stock item"""
        try:
            # Validate input data
            validated_data = validate_stock_data(data)

            # Check if category exists
            category = self.category_repository.find_by_id(validated_data['category_id'])
            if not category:
                return {
                    'success': False,
                    'message': 'Category not found',
                    'data': None
                }

            # Create stock
            stock_id = self.repository.create(validated_data)
            if stock_id:
                stock = self.get_stock_by_id(stock_id)
                return {
                    'success': True,
                    'message': 'Stock created successfully',
                    'data': {'id': stock_id, **stock} if stock else None
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create stock',
                    'data': None
                }

        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error creating stock: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def update_stock(self, stock_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update stock item"""
        try:
            # Validate input data
            validated_data = validate_stock_data(data, update=True)

            # Check if stock exists
            existing = self.repository.find_by_id(stock_id)
            if not existing:
                return {
                    'success': False,
                    'message': 'Stock not found',
                    'data': None
                }

            # Check if category exists (if category_id is being updated)
            if 'category_id' in validated_data:
                category = self.category_repository.find_by_id(validated_data['category_id'])
                if not category:
                    return {
                        'success': False,
                        'message': 'Category not found',
                        'data': None
                    }

            # Update stock
            success = self.repository.update(stock_id, validated_data)
            if success:
                stock = self.get_stock_by_id(stock_id)
                return {
                    'success': True,
                    'message': 'Stock updated successfully',
                    'data': stock
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update stock',
                    'data': None
                }

        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def delete_stock(self, stock_id: int) -> Dict[str, Any]:
        """Delete stock item"""
        try:
            # Check if stock exists
            stock = self.repository.find_by_id(stock_id)
            if not stock:
                return {
                    'success': False,
                    'message': 'Stock not found',
                    'data': None
                }

            # Get image path before deletion
            image_path = stock.get('image_path')

            # Delete stock
            success = self.repository.delete(stock_id)
            if success:
                # Delete associated image if exists
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                        logger.info(f"Deleted image file: {image_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete image file: {e}")

                return {
                    'success': True,
                    'message': 'Stock deleted successfully',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to delete stock',
                    'data': None
                }

        except Exception as e:
            logger.error(f"Error deleting stock: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def search_stocks(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search stocks by name"""
        try:
            if not search_term or not search_term.strip():
                return self.get_all_stocks()

            return self.repository.search_by_name(search_term.strip(), limit)
        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []

    def get_low_stock_items(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """Get items with low stock"""
        try:
            return self.repository.get_low_stock(threshold)
        except Exception as e:
            logger.error(f"Error getting low stock items: {e}")
            return []

    def get_stock_summary(self) -> Dict[str, Any]:
        """Get stock summary statistics"""
        try:
            return self.repository.get_stock_summary()
        except Exception as e:
            logger.error(f"Error getting stock summary: {e}")
            return {
                'total_items': 0,
                'total_quantity': 0,
                'total_categories': 0,
                'low_stock_count': 0
            }

    def upload_stock_image(self, stock_id: int, file) -> Dict[str, Any]:
        """Upload image for stock item"""
        try:
            # Check if stock exists
            stock = self.repository.find_by_id(stock_id)
            if not stock:
                return {
                    'success': False,
                    'message': 'Stock not found',
                    'data': None
                }

            # Validate file
            if not file or not file.filename:
                return {
                    'success': False,
                    'message': 'No file provided',
                    'data': None
                }

            if not self._allowed_file(file.filename):
                return {
                    'success': False,
                    'message': 'Invalid file type',
                    'data': None
                }

            # Create upload directory if it doesn't exist
            os.makedirs(self.config.UPLOAD_FOLDER, exist_ok=True)

            # Generate unique filename
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            unique_filename = f'stock_{stock_id}_{os.urandom(8).hex()}{ext}'
            filepath = os.path.join(self.config.UPLOAD_FOLDER, unique_filename)

            # Save file
            file.save(filepath)

            # Update database with new image path
            old_image_path = stock.get('image_path')
            success = self.repository.update_image_path(stock_id, filepath)

            if success:
                # Delete old image if exists
                if old_image_path and os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                        logger.info(f"Deleted old image file: {old_image_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old image file: {e}")

                return {
                    'success': True,
                    'message': 'Image uploaded successfully',
                    'data': {'image_path': filepath}
                }
            else:
                # Delete uploaded file if database update failed
                if os.path.exists(filepath):
                    os.remove(filepath)

                return {
                    'success': False,
                    'message': 'Failed to update database',
                    'data': None
                }

        except Exception as e:
            logger.error(f"Error uploading stock image: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def _allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.config.ALLOWED_EXTENSIONS
