# Unit Tests

import unittest
from unittest.mock import MagicMock, patch
from contextlib import contextmanager
from rich.console import Console
from backend.app.tools.document_reference_manager import DocumentReferenceManager, AdmissionBurnsLinker

@contextmanager
def null_console_context():
    """Create a null console context for testing."""
    console = Console(quiet=True)
    try:
        yield console
    finally:
        pass

class TestDocumentReferenceManager(unittest.TestCase):
    """Test cases for DocumentReferenceManager class"""
    
    def setUp(self):
        """Set up test environment"""
        # Use context manager for proper resource handling
        with null_console_context() as console:
            self.null_console = console
            
            # Create a mock db connection
            self.mock_db = MagicMock()
            self.mock_db_connect = MagicMock(return_value=True)
            self.mock_db_close = MagicMock()
            
            # Create a manager for testing
            self.manager = DocumentReferenceManager(
                source_collection="test_source",
                target_collection="test_target",
                source_field="test_field",
                target_field="test_field",
                reference_field="reference",
                dry_run=True,
                console=self.null_console
            )
    
    def test_find_matching_documents(self):
        """Test finding matching documents between collections"""
        with patch('backend.app.tools.document_reference_manager.db_connection') as mock_db:
            # Configure mock
            mock_db.connect.return_value = True
            mock_db.db.get_collection.return_value.distinct.side_effect = [
                ["id1", "id2", "id3"],  # source IDs
                ["id1", "id2", "id4"]   # target IDs
            ]
            mock_db.db.get_collection.return_value.find_one.side_effect = [
                {"_id": "source1", "test_field": "id1"},
                {"_id": "target1", "test_field": "id1"},
                {"_id": "source2", "test_field": "id2"},
                {"_id": "target2", "test_field": "id2"}
            ]
            
            # Call method
            result = self.manager.find_matching_documents()
            
            # Check results
            self.assertEqual(len(result), 2)
            self.assertEqual(len(self.manager.unmatched_source_ids), 1)
            self.assertEqual(len(self.manager.unmatched_target_ids), 1)
            self.assertIn("id1", result)
            self.assertIn("id2", result)
            
    def test_check_existing_references(self):
        """Test checking existing references"""
        with patch('backend.app.tools.document_reference_manager.db_connection') as mock_db:
            # Configure mock
            mock_db.connect.return_value = True
            mock_db.db.get_collection.return_value.find.return_value = [
                {"_id": "doc1", "test_field": "id1"},
                {"_id": "doc2", "test_field": "id2"}
            ]
            
            # Call method
            count, ids = self.manager.check_existing_references()
            
            # Check results
            self.assertEqual(count, 2)
            self.assertEqual(len(ids), 2)
            self.assertIn("id1", ids)
            self.assertIn("id2", ids)
            
    def test_update_references_dry_run(self):
        """Test updating references in dry run mode"""
        with patch('backend.app.tools.document_reference_manager.db_connection') as mock_db:
            # Configure mock
            mock_db.connect.return_value = True
            
            # Populate matched IDs
            self.manager.matched_ids = {
                "id1": {"source_id": "source1", "target_id": "target1", "match_value": "id1"},
                "id2": {"source_id": "source2", "target_id": "target2", "match_value": "id2"}
            }
            
            # Call method (dry run)
            self.manager.dry_run = True
            result = self.manager.update_references()
            
            # Check results
            self.assertTrue(result)
            self.assertEqual(self.manager.success_count, 2)
            self.assertEqual(self.manager.error_count, 0)
            # Verify no database calls were made
            mock_db.db.get_collection.return_value.update_one.assert_not_called()
            
    def test_update_references_actual(self):
        """Test updating references for real"""
        with patch('backend.app.tools.document_reference_manager.db_connection') as mock_db:
            # Configure mock
            mock_db.connect.return_value = True
            mock_db.db.get_collection.return_value.update_one.return_value.modified_count = 1
            
            # Populate matched IDs
            self.manager.matched_ids = {
                "id1": {"source_id": "source1", "target_id": "target1", "match_value": "id1"}
            }
            
            # Call method (not dry run)
            self.manager.dry_run = False
            result = self.manager.update_references()
            
            # Check results
            self.assertTrue(result)
            self.assertEqual(self.manager.success_count, 1)
            self.assertEqual(self.manager.error_count, 0)
            # Verify database call was made
            mock_db.db.get_collection.return_value.update_one.assert_called_once()


class TestAdmissionBurnsLinker(unittest.TestCase):
    """Test cases for AdmissionBurnsLinker class"""
    
    def test_linker_initialization(self):
        """Test linker initialization with correct parameters"""
        with patch('backend.app.tools.document_reference_manager.DocumentReferenceManager') as mock_manager:
            # Create linker with proper resource management
            with null_console_context() as console:
                linker = AdmissionBurnsLinker(dry_run=True, console=console)
                
                # Verify manager was created with correct parameters
                mock_manager.assert_called_once_with(
                    source_collection="admission_data",
                    target_collection="burns",
                    source_field="ID",
                    target_field="ID",
                    reference_field="burns",
                    dry_run=True,
                    console=console
                )
            
    def test_delegation_methods(self):
        """Test that linker methods delegate to the manager"""
        with patch('backend.app.tools.document_reference_manager.DocumentReferenceManager') as mock_manager_class:
            # Create mock manager
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            # Create linker with proper resource management
            with null_console_context() as console:
                linker = AdmissionBurnsLinker(dry_run=True, console=console)
                
                # Call methods
                linker.find_matching_documents()
                linker.check_existing_references()
                linker.update_references()
                linker.run()
                
                # Verify delegation
                mock_manager.find_matching_documents.assert_called_once()
                mock_manager.check_existing_references.assert_called_once()
                mock_manager.update_references.assert_called_once()
                mock_manager.run.assert_called_once()


if __name__ == '__main__':
    unittest.main()