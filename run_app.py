"""SSL-patched launcher for Streamlit (fixes Windows cert store crash).

On Windows, ``ssl.create_default_context()`` loads the system certificate
store, which can contain corrupted certificates that trigger::

    ssl.SSLError: [ASN1: NOT_ENOUGH_DATA]

The fix: monkey-patch ``ssl.create_default_context`` **before** any
Tornado / Streamlit import, replacing the Windows store with ``certifi``'s
curated CA bundle.
"""

import logging
import os
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patch ssl.create_default_context BEFORE any downstream import
# ---------------------------------------------------------------------------

try:
    import certifi

    _CA_BUNDLE = certifi.where()

    def _patched_create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None
    ):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(_CA_BUNDLE)
        return ctx

    logger.info("SSL: using certifi CA bundle from %s", _CA_BUNDLE)

except ImportError:
    logger.warning(
        "certifi not installed; Windows cert store may crash, install: pip install certifi"
    )

    _original_create_default_context = ssl.create_default_context

    def _patched_create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH, *, cafile=None, capath=None, cadata=None
    ):
        try:
            return _original_create_default_context(
                purpose, cafile=cafile, capath=capath, cadata=cadata
            )
        except ssl.SSLError:
            logger.warning("Windows certificate store corrupted — SSL verification DISABLED")
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx


ssl.create_default_context = _patched_create_default_context

# Also hint requests / urllib3 to bypass the Windows store
try:
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except (ImportError, NameError):
    pass

# ---------------------------------------------------------------------------
# Streamlit boot
# ---------------------------------------------------------------------------

import sys

import streamlit.web.cli

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "run", "web/app.py"]
    sys.exit(streamlit.web.cli.main())
