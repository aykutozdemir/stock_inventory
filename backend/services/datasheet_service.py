"""
Datasheet service for datasheet operations
"""
import logging
from typing import List, Dict, Any, Optional
from backend.repositories.datasheet_repository import DatasheetRepository

logger = logging.getLogger(__name__)

class DatasheetService:
    """Service for datasheet operations"""

    def __init__(self):
        self.repository = DatasheetRepository()

    def get_datasheet(self, datasheet_id: int) -> Optional[bytes]:
        """Get PDF data for datasheet"""
        try:
            return self.repository.get_pdf_data(datasheet_id)
        except Exception as e:
            logger.error(f"Error getting datasheet: {e}")
            return None

    def get_datasheet_info(self, datasheet_id: int) -> Optional[Dict[str, Any]]:
        """Get datasheet information"""
        try:
            return self.repository.get_datasheet_info(datasheet_id)
        except Exception as e:
            logger.error(f"Error getting datasheet info: {e}")
            return None

    def save_datasheet(self, component_name: str, pdf_data: bytes, source_url: str, filename: str, summary: str = None,
                      extracted_specs: str = None, key_specifications: str = None, manufacturer: str = None,
                      package_type: str = None, voltage_rating: str = None, current_rating: str = None,
                      power_rating: str = None, temperature_range: str = None, tolerance: str = None) -> Optional[int]:
        """Save datasheet to database"""
        try:
            return self.repository.create_datasheet(component_name, filename, source_url, pdf_data, summary,
                                                   extracted_specs, key_specifications, manufacturer, package_type,
                                                   voltage_rating, current_rating, power_rating, temperature_range, tolerance)
        except Exception as e:
            logger.error(f"Error saving datasheet: {e}")
            return None

    def find_by_component(self, component_name: str) -> List[Dict[str, Any]]:
        """Find datasheets by component name"""
        try:
            return self.repository.find_by_component(component_name)
        except Exception as e:
            logger.error(f"Error finding datasheets by component: {e}")
            return []

    def update_summary(self, datasheet_id: int, summary: str) -> bool:
        """Update the summary for a datasheet"""
        try:
            return self.repository.update_summary(datasheet_id, summary)
        except Exception as e:
            logger.error(f"Error updating datasheet summary: {e}")
            return False

    def search_by_summary(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search datasheets by summary content"""
        try:
            return self.repository.search_by_summary(search_term, limit)
        except Exception as e:
            logger.error(f"Error searching datasheets by summary: {e}")
            return []

    def get_datasheets_with_summaries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get datasheets that have summaries"""
        try:
            return self.repository.get_datasheets_with_summaries(limit)
        except Exception as e:
            logger.error(f"Error getting datasheets with summaries: {e}")
            return []

    def update_extracted_specs(self, datasheet_id: int, extracted_specs: str = None,
                              key_specifications: str = None, manufacturer: str = None,
                              package_type: str = None, voltage_rating: str = None,
                              current_rating: str = None, power_rating: str = None,
                              temperature_range: str = None, tolerance: str = None) -> bool:
        """Update extracted specifications for a datasheet"""
        try:
            return self.repository.update_extracted_specs(datasheet_id, extracted_specs, key_specifications,
                                                        manufacturer, package_type, voltage_rating, current_rating,
                                                        power_rating, temperature_range, tolerance)
        except Exception as e:
            logger.error(f"Error updating extracted specs: {e}")
            return False

    def get_datasheets_with_specs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get datasheets that have extracted specifications"""
        try:
            return self.repository.get_datasheets_with_specs(limit)
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
            return self.repository.find_similar_components(voltage_min, voltage_max, current_min, current_max,
                                                         power_min, power_max, temp_min, temp_max,
                                                         component_type, limit)
        except Exception as e:
            logger.error(f"Error finding similar components: {e}")
            return []
