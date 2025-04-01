# let's create a pydantic model for the Google Sheets extraction
# the goal is to extract the data from the Google Sheets and convert it into a pydantic model
# so that it can be saved as a typed json file

from typing import Optional, List
from datetime import datetime
import logfire
from core_tools.key_manager import KeyManager
from pydantic import BaseModel

key_manager = KeyManager()
PYDANTIC_API_KEY = key_manager.get_key("PYDANTIC_API_KEY")

logfire.configure(token=PYDANTIC_API_KEY)
logfire.info('Hello, {place}!', place='World')
logfire.instrument_pydantic()  


