"""
Admission-Burns Document Linking Script

Command-line script to establish references from admission documents to burns documents.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# Now we can import from backend
from backend.app.tools.link_admission_to_burns import main

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))