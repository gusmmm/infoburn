import asyncio
from backend.app.tools.link_admission_to_burns import AdmissionBurnsLinker

async def test_admission_burns_linker():
    """Test the AdmissionBurnsLinker class."""
    # Create a test linker with dry run mode
    linker = AdmissionBurnsLinker(dry_run=True)
    
    # Test finding matching documents
    matching_docs = await linker.find_matching_documents()
    assert isinstance(matching_docs, dict)
    
    # Test checking existing references
    count, ids = await linker.check_existing_references()
    assert isinstance(count, int)
    assert isinstance(ids, list)
    
    # Test creating tables
    matching_table = linker.create_matching_table()
    assert matching_table is not None
    
    # Test running full process
    await linker.run()
    
    # Validate results
    results_table = linker.create_results_table()
    assert results_table is not None
    
    print("All tests passed")


if __name__ == "__main__":
    # Run tests if the module is executed directly
    asyncio.run(test_admission_burns_linker())