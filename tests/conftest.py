import sys
from pathlib import Path

# put the project folder on the search path so "import app..." works in the tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
