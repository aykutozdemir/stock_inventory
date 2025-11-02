"""
Datasheet repository for datasheet data operations
"""
import logging
from typing import List, Dict, Any, Optional
from backend.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class DatasheetRepository(BaseRepository):
    """Repository for datasheet operations"""

    def __init__(self):
        super().__init__('datasheets')

    def find_by_component(self, component_name: str) -> List[Dict[str, Any]]:
        """Find datasheets by component name"""
        try:
            query = """
                SELECT * FROM datasheets
                WHERE component_name = ?
                ORDER BY created_at DESC
            """
            return self.execute_query(query, (component_name,))
        except Exception as e:
            logger.error(f"Error finding datasheets by component: {e}")
            return []

    def search_by_component(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search datasheets by component name"""
        try:
            query = """
                SELECT * FROM datasheets
                WHERE component_name LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            return self.execute_query(query, (f'%{search_term}%', limit))
        except Exception as e:
            logger.error(f"Error searching datasheets: {e}")
            return []

    def create_datasheet(self, component_name: str, original_filename: str,
                        source_url: str, pdf_data: bytes, summary: str = None,
                        extracted_specs: str = None, key_specifications: str = None,
                        manufacturer: str = None, package_type: str = None,
                        voltage_rating: str = None, current_rating: str = None,
                        power_rating: str = None, temperature_range: str = None,
                        tolerance: str = None) -> Optional[int]:
        """Create new datasheet"""
        try:
            data = {
                'component_name': component_name,
                'original_filename': original_filename,
                'source_url': source_url,
                'pdf_data': pdf_data,
                'file_size': len(pdf_data),
                'summary': summary,
                'extracted_specs': extracted_specs,
                'key_specifications': key_specifications,
                'manufacturer': manufacturer,
                'package_type': package_type,
                'voltage_rating': voltage_rating,
                'current_rating': current_rating,
                'power_rating': power_rating,
                'temperature_range': temperature_range,
                'tolerance': tolerance
            }
            return self.create(data)
        except Exception as e:
            logger.error(f"Error creating datasheet: {e}")
            return None

    def get_pdf_data(self, datasheet_id: int) -> Optional[bytes]:
        """Get PDF data for a datasheet"""
        try:
            query = "SELECT pdf_data FROM datasheets WHERE id = ?"
            results = self.execute_query(query, (datasheet_id,))
            if results:
                return results[0]['pdf_data']
            return None
        except Exception as e:
            logger.error(f"Error getting PDF data: {e}")
            return None

    def get_datasheet_info(self, datasheet_id: int) -> Optional[Dict[str, Any]]:
        """Get datasheet information without PDF data"""
        try:
            query = """
                SELECT id, component_name, original_filename, source_url, file_size, summary,
                       manufacturer, package_type, voltage_rating, current_rating, power_rating,
                       temperature_range, tolerance, key_specifications, extracted_specs,
                       created_at, updated_at
                FROM datasheets WHERE id = ?
            """
            results = self.execute_query(query, (datasheet_id,))
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting datasheet info: {e}")
            return None

    def get_recent_datasheets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently added datasheets"""
        try:
            query = """
                SELECT id, component_name, original_filename, source_url, file_size, created_at
                FROM datasheets
                ORDER BY created_at DESC
                LIMIT ?
            """
            return self.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error getting recent datasheets: {e}")
            return []

    def update_summary(self, datasheet_id: int, summary: str) -> bool:
        """Update the summary for a datasheet"""
        try:
            query = """
                UPDATE datasheets
                SET summary = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            rows_affected = self.execute_update(query, (summary, datasheet_id))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating datasheet summary: {e}")
            return False

    def update_extracted_specs(self, datasheet_id: int, extracted_specs: str = None,
                              key_specifications: str = None, manufacturer: str = None,
                              package_type: str = None, voltage_rating: str = None,
                              current_rating: str = None, power_rating: str = None,
                              temperature_range: str = None, tolerance: str = None) -> bool:
        """Update extracted specifications for a datasheet"""
        try:
            query = """
                UPDATE datasheets
                SET extracted_specs = ?, key_specifications = ?, manufacturer = ?,
                    package_type = ?, voltage_rating = ?, current_rating = ?,
                    power_rating = ?, temperature_range = ?, tolerance = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            params = (extracted_specs, key_specifications, manufacturer, package_type,
                     voltage_rating, current_rating, power_rating, temperature_range,
                     tolerance, datasheet_id)
            rows_affected = self.execute_update(query, params)
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating datasheet specs: {e}")
            return False

    def search_by_summary(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search datasheets by summary content"""
        try:
            query = """
                SELECT id, component_name, original_filename, source_url, file_size, summary, created_at, updated_at
                FROM datasheets
                WHERE summary LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            return self.execute_query(query, (f'%{search_term}%', limit))
        except Exception as e:
            logger.error(f"Error searching datasheets by summary: {e}")
            return []

    def get_datasheets_with_summaries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get datasheets that have summaries"""
        try:
            query = """
                SELECT id, component_name, original_filename, source_url, file_size, summary, created_at, updated_at
                FROM datasheets
                WHERE summary IS NOT NULL AND summary != ''
                ORDER BY updated_at DESC
                LIMIT ?
            """
            return self.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error getting datasheets with summaries: {e}")
            return []

    def get_datasheets_with_specs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get datasheets that have extracted specifications"""
        try:
            query = """
                SELECT id, component_name, manufacturer, package_type, voltage_rating,
                       current_rating, power_rating, temperature_range, tolerance,
                       key_specifications, created_at
                FROM datasheets
                WHERE key_specifications IS NOT NULL AND key_specifications != ''
                ORDER BY updated_at DESC
                LIMIT ?
            """
            return self.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error getting datasheets with specs: {e}")
            return []

    def find_similar_components(self, voltage_min: float = None, voltage_max: float = None,
                               current_min: float = None, current_max: float = None,
                               power_min: float = None, power_max: float = None,
                               temp_min: float = None, temp_max: float = None,
                               component_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find components with similar specifications for comparison"""
        try:
            conditions = []
            params = []

            if voltage_min is not None:
                conditions.append("CAST(voltage_rating AS REAL) >= ?")
                params.append(voltage_min)
            if voltage_max is not None:
                conditions.append("CAST(voltage_rating AS REAL) <= ?")
                params.append(voltage_max)

            if current_min is not None:
                conditions.append("CAST(current_rating AS REAL) >= ?")
                params.append(current_min)
            if current_max is not None:
                conditions.append("CAST(current_rating AS REAL) <= ?")
                params.append(current_max)

            if power_min is not None:
                conditions.append("CAST(power_rating AS REAL) >= ?")
                params.append(power_min)
            if power_max is not None:
                conditions.append("CAST(power_rating AS REAL) <= ?")
                params.append(power_max)

            if component_type:
                conditions.append("LOWER(component_name) LIKE LOWER(?)")
                params.append(f"%{component_type}%")

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT id, component_name, manufacturer, package_type, voltage_rating,
                       current_rating, power_rating, temperature_range, tolerance,
                       key_specifications
                FROM datasheets
                WHERE {where_clause}
                ORDER BY component_name
                LIMIT ?
            """
            params.append(limit)

            return self.execute_query(query, params)

        except Exception as e:
            logger.error(f"Error finding similar components: {e}")
            return []

    def get_component_count(self) -> int:
        """Get count of unique components with datasheets"""
        try:
            query = "SELECT COUNT(DISTINCT component_name) as count FROM datasheets"
            results = self.execute_query(query)
            return results[0]['count'] if results else 0
        except Exception as e:
            logger.error(f"Error getting component count: {e}")
            return 0

    def to_dict(self, record: Any) -> Dict[str, Any]:
        """Convert datasheet record to dictionary"""
        if isinstance(record, dict):
            return record
        return dict(record) if hasattr(record, 'keys') else {}

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute custom query (helper method)"""
        from backend.models.database import execute_query
        return execute_query(query, params)

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute update query (helper method)"""
        from backend.models.database import execute_update
        return execute_update(query, params)

    def execute_insert(self, query: str, params: tuple = ()) -> Optional[int]:
        """Execute insert query (helper method)"""
        from backend.models.database import execute_insert
        return execute_insert(query, params)
