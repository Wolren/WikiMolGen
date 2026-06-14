import os
import sys

# Ensure web/ is on sys.path so that imports like ``from template.utils import ...``
# or ``from ui.icons import ...`` resolve correctly.
_web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
if _web_dir not in sys.path:
    sys.path.insert(0, _web_dir)
