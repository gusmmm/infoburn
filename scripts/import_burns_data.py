"""
Burns Data Import Script

Command-line script to import burns data from JSON files to MongoDB.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Now we can import from backend
from backend.app.tools.import_burns_json_to_db import main

if __name__ == "__main__":
    asyncio.run(main())