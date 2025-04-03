from pymongo import MongoClient
from pymongo.collection import Collection
from typing import List, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()

def create_burns_admission_aggregation_query() -> List[Dict]:
    """
    Generates a MongoDB aggregation pipeline to join burns data with admission data based on the "ID" field.
    Only returns admission documents that have associated burns data.
    The burns data is embedded within the admission_data document.

    Returns:
        List[Dict]: A list representing the MongoDB aggregation pipeline.
    """
    pipeline = [
        {
            "$lookup": {
                "from": "burns",
                "localField": "ID",
                "foreignField": "ID",
                "as": "burns_array"
            }
        },
        {
            "$match": {
                "burns_array": {"$ne": []}  # Only keep documents with burns
            }
        },
        {
            "$project": {
                "_id": 1,
                "ID": 1,
                "processo": 1,
                "nome": 1,
                "data_ent": 1,
                "data_alta": 1,
                "sexo": 1,
                "data_nasc": 1,
                "destino": 1,
                "origem": 1,
                "burns_array": {
                    "$arrayElemAt": ["$burns_array", 0]  # Take first burns document
                }
            }
        }
    ]
    return pipeline

def count_documents(collection: Collection) -> int:
    """
    Counts the total number of documents in a given MongoDB collection.

    Args:
        collection (Collection): The MongoDB collection to count documents from.

    Returns:
        int: The total number of documents in the collection.
    """
    try:
        count = collection.count_documents({})
        return count
    except Exception as e:
        console.print(f"[red]Error counting documents: {str(e)}[/red]")
        return 0

def count_matching_ids(collection1: Collection, collection2: Collection) -> int:
    """
    Counts the number of documents in two MongoDB collections that have matching "ID" fields.

    Args:
        collection1 (Collection): The first MongoDB collection.
        collection2 (Collection): The second MongoDB collection.

    Returns:
        int: The number of documents with matching "ID" fields in both collections.
    """
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": collection2.name,
                    "localField": "ID",
                    "foreignField": "ID",
                    "as": "matches"
                }
            },
            {
                "$match": {
                    "matches": {"$ne": []}
                }
            },
            {
                "$count": "matching_count"
            }
        ]
        result = list(collection1.aggregate(pipeline))
        if result:
            return result[0]["matching_count"]
        else:
            return 0
    except Exception as e:
        console.print(f"[red]Error counting matching IDs: {str(e)}[/red]")
        return 0

def count_orphaned_documents(main_collection: Collection, related_collection: Collection) -> int:
    """
    Counts the number of documents in a main collection that do not have a corresponding document in a related collection based on the "ID" field.

    Args:
        main_collection (Collection): The main MongoDB collection.
        related_collection (Collection): The related MongoDB collection.

    Returns:
        int: The number of orphaned documents in the main collection.
    """
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": related_collection.name,
                    "localField": "ID",
                    "foreignField": "ID",
                    "as": "matches"
                }
            },
            {
                "$match": {
                    "matches": {"$eq": []}
                }
            },
            {
                "$count": "orphaned_count"
            }
        ]
        result = list(main_collection.aggregate(pipeline))
        if result:
            return result[0]["orphaned_count"]
        else:
            return 0
    except Exception as e:
        console.print(f"[red]Error counting orphaned documents: {str(e)}[/red]")
        return 0

def display_results(total_admission_data: int, total_burns: int, matching_ids: int, orphaned_admission_data: int, orphaned_burns: int) -> None:
    """
    Displays the data validation results in a user-friendly format using the `rich` library.

    Args:
        total_admission_data (int): The total number of documents in the `admission_data` collection.
        total_burns (int): The total number of documents in the `burns` collection.
        matching_ids (int): The number of documents with matching "ID" fields in both collections.
        orphaned_admission_data (int): The number of orphaned documents in the `admission_data` collection.
        orphaned_burns (int): The number of orphaned documents in the `burns` collection.
    """
    table = Table(title="Data Validation Results", title_style="bold blue", border_style="blue")
    table.add_column("Metric", style="cyan", justify="right")
    table.add_column("Value", style="green", justify="left")

    table.add_row("Total Admission Data Documents", str(total_admission_data))
    table.add_row("Total Burns Documents", str(total_burns))
    table.add_row("Documents with Matching IDs", str(matching_ids))
    table.add_row("Orphaned Admission Data Documents", str(orphaned_admission_data))
    table.add_row("Orphaned Burns Documents", str(orphaned_burns))

    console.print(table)

def display_aggregation_results(results: List[Dict]) -> None:
    """
    Displays the first 10 results of the aggregation query in a user-friendly format using the `rich` library.

    Args:
        results (List[Dict]): The list of documents returned by the aggregation query.
    """
    console.print(Panel(Text("Aggregation Query Results (First 10)", justify="center", style="bold blue"), border_style="blue"))
    for i, result in enumerate(results):
        if i >= 10:
            break
        console.print(f"[bold]Result {i + 1}:[/bold]")
        console.print(result)

if __name__ == "__main__":
    # Example Usage (replace with your actual MongoDB connection details)
    mongo_uri = "mongodb://localhost:27017/"  # Replace with your MongoDB URI
    db_name = "infoburn"  # Replace with your database name
    admission_collection_name = "admission_data"
    burns_collection_name = "burns"

    client = MongoClient(mongo_uri)
    db = client[db_name]
    admission_collection: Collection = db[admission_collection_name]
    burns_collection: Collection = db[burns_collection_name]

    # Perform data validation checks
    total_admission_data = count_documents(admission_collection)
    total_burns = count_documents(burns_collection)
    matching_ids = count_matching_ids(admission_collection, burns_collection)
    orphaned_admission_data = count_orphaned_documents(admission_collection, burns_collection)
    orphaned_burns = count_orphaned_documents(burns_collection, admission_collection)

    # Display the results
    display_results(total_admission_data, total_burns, matching_ids, orphaned_admission_data, orphaned_burns)

    # Execute the aggregation query only if there are matching IDs
    if matching_ids > 0:
        aggregation_pipeline = create_burns_admission_aggregation_query()
        results = list(admission_collection.aggregate(aggregation_pipeline))
        display_aggregation_results(results)
    else:
        console.print("[yellow]No matching IDs found. Skipping aggregation query.[/yellow]")

    client.close()