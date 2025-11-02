"""
Basic tests for the electronic component inventory system
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.config import Config, get_config
from backend.models.database import init_database, get_db_connection
from backend.services.category_service import CategoryService

class TestConfig:
    """Test configuration setup"""

    def test_config_creation(self):
        """Test config object creation"""
        config = Config()
        assert config.DATABASE is not None
        assert config.SECRET_KEY is not None

    def test_get_config(self):
        """Test get_config function"""
        config = get_config('testing')
        assert hasattr(config, 'DEBUG')
        assert hasattr(config, 'TESTING')

class TestDatabase:
    """Test database operations"""

    def test_database_init(self, tmp_path):
        """Test database initialization"""
        db_path = tmp_path / "test.db"
        result_path = init_database(str(db_path))
        assert os.path.exists(result_path)

    def test_db_connection(self, tmp_path):
        """Test database connection context manager"""
        db_path = tmp_path / "test.db"
        init_database(str(db_path))

        with get_db_connection(db_path=str(db_path)) as conn:
            cursor = conn.execute("SELECT 1 as test")
            result = cursor.fetchone()
            assert result['test'] == 1

class TestCategoryService:
    """Test category service"""

    @pytest.fixture
    def service(self, tmp_path):
        """Create category service with test database"""
        db_path = tmp_path / "test.db"
        init_database(str(db_path))
        # Override database path in service
        service = CategoryService()
        # This would need more setup in real implementation
        return service

    def test_service_creation(self, service):
        """Test service object creation"""
        assert service is not None
        assert hasattr(service, 'repository')

if __name__ == "__main__":
    pytest.main([__file__])
