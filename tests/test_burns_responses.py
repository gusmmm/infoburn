"""
Unit tests for burns response models.
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from backend.app.models.burns import BurnMechanism, AccidentType, BurnInjury, BurnLocation, BurnDepth, Laterality
from backend.app.models.burns_responses import BurnsPatientResponse, BurnsStatisticsResponse


class TestBurnsPatientResponse(unittest.TestCase):
    """Test cases for BurnsPatientResponse model."""
    
    def test_valid_response(self):
        """Test creation of a valid BurnsPatientResponse object."""
        # Create a sample burn injury
        burn_injury = BurnInjury(
            location=BurnLocation.TRUNK,
            laterality=Laterality.BILATERAL,
            depth=BurnDepth.SECOND_DEGREE_PARTIAL
        )
        
        # Create a valid response object
        response = BurnsPatientResponse(
            id="507f1f77bcf86cd799439011",  # Changed from _id to id
            ID="12345",
            tbsa=15.5,
            mechanism=BurnMechanism.HEAT,
            type_of_accident=AccidentType.DOMESTIC,
            agent="hot water",
            associated_trauma=["head injury"],
            burns=[burn_injury],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Verify the object was created correctly
        self.assertEqual(response.ID, "12345")
        self.assertEqual(response.tbsa, 15.5)
        self.assertEqual(response.mechanism, BurnMechanism.HEAT)
        self.assertEqual(len(response.burns), 1)
        self.assertEqual(response.burns[0].location, BurnLocation.TRUNK)
    
    def test_default_values(self):
        """Test default values in BurnsPatientResponse."""
        # Create minimal response
        response = BurnsPatientResponse(
            id="507f1f77bcf86cd799439011",  # Changed from _id to id
            ID="12345"
        )
        
        # Verify defaults
        self.assertFalse(response.wildfire)
        self.assertFalse(response.bonfire)
        self.assertFalse(response.fireplace)
        self.assertFalse(response.violence)
        self.assertFalse(response.suicide_attempt)
        self.assertFalse(response.escharotomy)
        self.assertIsNone(response.associated_trauma)
        self.assertIsNone(response.burns)


class TestBurnsStatisticsResponse(unittest.TestCase):
    """Test cases for BurnsStatisticsResponse model."""
    
    def test_valid_statistics(self):
        """Test creation of a valid BurnsStatisticsResponse object."""
        # Create a valid statistics response
        stats = BurnsStatisticsResponse(
            total_count=150,
            mechanism_distribution={
                "Heat": 120,
                "Chemicals": 15,
                "Electrical discharge": 10,
                "Friction": 5
            },
            accident_type_distribution={
                "domestic": 100,
                "workplace": 40,
                "other": 10
            },
            average_tbsa=17.3,
            domestic_accident_percentage=66.7,
            violence_count=5
        )
        
        # Verify the object was created correctly
        self.assertEqual(stats.total_count, 150)
        self.assertEqual(stats.mechanism_distribution["Heat"], 120)
        self.assertEqual(stats.accident_type_distribution["domestic"], 100)
        self.assertEqual(stats.average_tbsa, 17.3)
        self.assertEqual(stats.domestic_accident_percentage, 66.7)
        self.assertEqual(stats.violence_count, 5)
    
    def test_default_values(self):
        """Test default values in BurnsStatisticsResponse."""
        # Create minimal statistics
        stats = BurnsStatisticsResponse(
            total_count=10,
            mechanism_distribution={},
            accident_type_distribution={}
        )
        
        # Verify defaults
        self.assertIsNone(stats.average_tbsa)
        self.assertIsNone(stats.domestic_accident_percentage)
        self.assertEqual(stats.violence_count, 0)


if __name__ == "__main__":
    unittest.main()