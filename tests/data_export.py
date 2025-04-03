from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection
from rich.console import Console
from rich.progress import Progress
from datetime import datetime

# Import models for type hints
from pydantic_classifier.admission_data_model import AdmissionDataPatient
from pydantic_classifier.burns_model import BurnsModel, BurnLocation  # Add this import

console = Console()

class DataExporter:
    """
    Handles the export of MongoDB data to CSV files.
    """
    
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017/", 
                 db_name: str = "infoburn"):
        """
        Initialize the DataExporter with MongoDB connection details.
        
        Args:
            mongo_uri (str): MongoDB connection URI
            db_name (str): Name of the database
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.client = None
        self.db = None
        
    def connect(self) -> bool:
        """
        Establish connection to MongoDB.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            return True
        except Exception as e:
            console.print(f"[red]Error connecting to MongoDB: {str(e)}[/red]")
            return False
            
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            
    def get_combined_data(self) -> List[Dict]:
        """
        Retrieve admission data with corresponding burns using aggregation pipeline.
        
        Returns:
            List[Dict]: List of combined admission and burns documents
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "burns",
                    "localField": "ID",
                    "foreignField": "ID",
                    "as": "burns_data"
                }
            },
            {
                "$match": {
                    "burns_data": {"$ne": []}
                }
            },
            {
                "$project": {
                    "ID": 1,
                    "processo": 1,
                    "nome": 1,
                    "data_ent": 1,
                    "data_alta": 1,
                    "sexo": 1,
                    "data_nasc": 1,
                    "destino": 1,
                    "origem": 1,
                    "burns_data": {"$arrayElemAt": ["$burns_data", 0]}
                }
            }
        ]
        
        return list(self.db.admission_data.aggregate(pipeline))
    
    def flatten_burns_data(self, data: List[Dict]) -> pd.DataFrame:
        """
        Flatten the nested burns data structure into a pandas DataFrame with predefined columns
        for each possible burn location.
        
        Args:
            data (List[Dict]): List of combined admission and burns documents
            
        Returns:
            pd.DataFrame: Flattened data in a DataFrame with consistent columns for all burn locations
        """
        flattened_records = []
        
        # Define burn locations columns structure
        burn_locations = {
            BurnLocation.HEAD.value: ["head", "head_laterality", "head_depth", "head_circumferencial"],
            BurnLocation.NECK.value: ["neck", "neck_laterality", "neck_depth", "neck_circumferencial"],
            BurnLocation.FACE.value: ["face", "face_laterality", "face_depth", "face_circumferencial"],
            BurnLocation.UPPER_EXTREMITY.value: ["upper extremity", "upper extremity_laterality", "upper extremity_depth", "upper extremity_circumferencial"],
            BurnLocation.HAND.value: ["hand", "hand_laterality", "hand_depth", "hand_circumferencial"],
            BurnLocation.TRUNK.value: ["trunk", "trunk_laterality", "trunk_depth", "trunk_circumferencial"],
            BurnLocation.THORAX.value: ["thorax", "thorax_laterality", "thorax_depth", "thorax_circumferencial"],
            BurnLocation.ABDOMEN.value: ["abdomen", "abdomen_laterality", "abdomen_depth", "abdomen_circumferencial"],
            BurnLocation.BACK.value: ["back of trunk", "back of trunk_laterality", "back of trunk_depth", "back of trunk_circumferencial"],
            BurnLocation.PERINEUM.value: ["perineum", "perineum_laterality", "perineum_depth", "perineum_circumferencial"],
            BurnLocation.LOWER_EXTREMITY.value: ["lower extremity", "lower extremity_laterality", "lower extremity_depth", "lower extremity_circumferencial"],
            BurnLocation.FOOT.value: ["foot", "foot_laterality", "foot_depth", "foot_circumferencial"]
        }
        
        for record in data:
            burns_data = record.pop('burns_data', {})
            # Initialize base record with admission data
            flat_record = {
                # Admission data fields
                'ID': record.get('ID'),
                'processo': record.get('processo'),
                'nome': record.get('nome'),
                'data_ent': record.get('data_ent'),
                'data_alta': record.get('data_alta'),
                'sexo': record.get('sexo'),
                'data_nasc': record.get('data_nasc'),
                'destino': record.get('destino'),
                'origem': record.get('origem'),
                
                # Burns data fields
                'tbsa': burns_data.get('tbsa'),
                'mechanism': burns_data.get('mechanism'),
                'type_of_accident': burns_data.get('type_of_accident'),
                'agent': burns_data.get('agent'),
                'wildfire': burns_data.get('wildfire', False),
                'bonfire': burns_data.get('bonfire', False),
                'fireplace': burns_data.get('fireplace', False),
                'violence': burns_data.get('violence', False),
                'suicide_attempt': burns_data.get('suicide_attempt', False),
                'escharotomy': burns_data.get('escharotomy', False),
                'associated_trauma': ','.join(burns_data.get('associated_trauma', [])),
            }
            
            # Initialize all burn location fields with default values
            for location, columns in burn_locations.items():
                flat_record[columns[0]] = False  # existence
                flat_record[columns[1]] = None   # laterality
                flat_record[columns[2]] = None   # depth
                flat_record[columns[3]] = False  # circumferencial
            
            # Update burn location fields based on actual burns data
            burns = burns_data.get('burns', [])
            for burn in burns:
                location = burn.get('location')
                if location and location in burn_locations:
                    columns = burn_locations[location]
                    flat_record[columns[0]] = True  # existence
                    flat_record[columns[1]] = burn.get('laterality')
                    flat_record[columns[2]] = burn.get('depth')
                    flat_record[columns[3]] = burn.get('circumferencial', False)
            
            flattened_records.append(flat_record)
        
        return pd.DataFrame(flattened_records)
    
    def export_to_csv(self) -> Optional[Path]:
        """
        Export combined admission and burns data to CSV.
        
        Returns:
            Optional[Path]: Path to the generated CSV file if successful, None otherwise
        """
        try:
            if not self.connect():
                return None
                
            with Progress() as progress:
                task1 = progress.add_task("[cyan]Retrieving data...", total=None)
                data = self.get_combined_data()
                progress.update(task1, completed=True)
                
                task2 = progress.add_task("[cyan]Processing data...", total=None)
                df = self.flatten_burns_data(data)
                progress.update(task2, completed=True)
                
                # Create reports directory if it doesn't exist
                reports_dir = Path("reports")
                reports_dir.mkdir(exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = reports_dir / f"admission_burns_report_{timestamp}.csv"
                
                task3 = progress.add_task("[cyan]Saving to CSV...", total=None)
                df.to_csv(filename, index=False)
                progress.update(task3, completed=True)
                
                console.print(f"[green]Report saved successfully to: {filename}[/green]")
                return filename
                
        except Exception as e:
            console.print(f"[red]Error exporting data: {str(e)}[/red]")
            return None
            
        finally:
            self.close()

if __name__ == "__main__":
    exporter = DataExporter()
    exporter.export_to_csv()