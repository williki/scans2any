import sys
from pathlib import Path

# Insert src directory to sys.path to ensure local code is used
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# pytest_plugins = ["syrupy"]
