import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def reload_module(module_name: str):
    """Reload a module so tests can reset module-level configuration."""
    module = importlib.import_module(module_name)
    return importlib.reload(module)
