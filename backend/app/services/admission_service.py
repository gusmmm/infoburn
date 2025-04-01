from typing import List, Optional
from ..config.database import db_connection
from ..models.admission import AdmissionModel
from rich.console import Console

console = Console()

class AdmissionService:
    """
    Service class for handling admission-related operations.
    
    This class provides methods for CRUD operations on admission records
    and implements business logic related to patient admissions.
    """
    
    @staticmethod
    async def create_admission(admission: AdmissionModel) -> AdmissionModel:
        """
        Creates a new admission record in the database.
        
        Args:
            admission: AdmissionModel instance containing admission data
            
        Returns:
            AdmissionModel: The created admission record
        """
        try:
            result = await db_connection.db.admission_data.insert_one(admission.dict(by_alias=True))
            admission.id = result.inserted_id
            return admission
        except Exception as e:
            console.print(f"[red]Error creating admission: {str(e)}[/red]")
            raise

    @staticmethod
    async def get_admission(admission_id: str) -> Optional[AdmissionModel]:
        """
        Retrieves an admission record by ID.
        
        Args:
            admission_id: String representation of the admission ObjectId
            
        Returns:
            Optional[AdmissionModel]: The admission record if found, None otherwise
        """
        try:
            if (admission := await db_connection.db.admission_data.find_one({"_id": admission_id})):
                return AdmissionModel(**admission)
            return None
        except Exception as e:
            console.print(f"[red]Error retrieving admission: {str(e)}[/red]")
            raise