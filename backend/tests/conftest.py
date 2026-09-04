import sys
from pathlib import Path


backend_directory = Path(__file__).parents[1]
if str(backend_directory) not in sys.path:
    sys.path.insert(0, str(backend_directory))
