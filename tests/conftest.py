from pathlib import Path
import sys

# Ensure web/ is on sys.path so that imports like ``from template.utils import ...``
# or ``from ui.icons import ...`` resolve correctly.
_web_dir = str(Path(__file__).resolve().parent.parent / "web")
if _web_dir not in sys.path:
    sys.path.insert(0, _web_dir)
