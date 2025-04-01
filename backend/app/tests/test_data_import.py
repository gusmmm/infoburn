import pytest
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from ..models.admission import AdmissionModel
from ..config.database import db_connection
from pydantic import ValidationError

console = Console()

class TestAdmissionImport:
    """Test suite for admission data import functionality"""
    
    @pytest.fixture(scope="class")
    async def setup_database(self):
        """Setup test database connection"""
        try:
            await db_connection.connect()
            yield
        finally:
            await db_connection.close()
    
    @pytest.fixture
    def test_data_path(self) -> Path:
        """Provide test data directory path"""
        return Path(__file__).parent / "test_data"
    
    @pytest.mark.asyncio
    async def test_admission_model_validation(self, test_data_path: Path):
        """Test admission data validation"""
        test_data = {
            "ID": "12345",
            "processo": 987654,
            "nome": "Test Patient",
            "data_ent": "2023-06-15",
            "data_alta": "2023-06-30",
            "sexo": "M",
            "data_nasc": "1980-01-01",
            "destino": "Home",
            "origem": "Emergency"
        }
        
        admission = AdmissionModel(**test_data)
        assert admission.ID == "12345"
        assert admission.processo == 987654
    
    @pytest.mark.asyncio
    async def test_database_operations(self, setup_database):
        """Test database operations with admission data"""
        test_data = {
            "ID": "12345",
            "processo": 987654,
            "nome": "Test Patient",
            "data_ent": "2023-06-15",
            "data_alta": "2023-06-30",
            "sexo": "M",
            "data_nasc": "1980-01-01",
            "destino": "Home",
            "origem": "Emergency"
        }
        
        # Insert test data
        collection = db_connection.db.admission_data
        result = await collection.insert_one(test_data)
        assert result.inserted_id is not None
        
        # Retrieve and verify
        retrieved = await collection.find_one({"ID": "12345"})
        assert retrieved is not None
        assert retrieved["processo"] == 987654
        
        # Cleanup
        await collection.delete_one({"ID": "12345"})

if __name__ == "__main__":
    pytest.main([__file__, "-v"])