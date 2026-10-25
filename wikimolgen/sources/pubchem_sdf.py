"""wikimolgen.sources.pubchem_sdf - PubChem 3D conformer download
=================================================================

PubChem ships a computed 3D conformer for most CIDs, already
MMFF-optimised.  Downloading it skips ETKDG embedding and force-field
optimisation, which costs seconds on drug-sized molecules.

``record_type=3d`` returns 404 when PubChem has no conformer, so the
caller falls back to local embedding.
"""

from __future__ import annotations

from urllib.parse import quote

from wikimolgen.sources._client import PUG_BASE, get_with_retry, make_headers

__all__ = ["fetch_3d_sdf"]

# Largest 3D record observed is a few hundred KB; past this it is an
# error page or a redirect, not an SDF.
MAX_SDF_BYTES = 4 * 1024 * 1024

NAMESPACES = frozenset({"cid", "name"})


def fetch_3d_sdf(identifier: str | int, *, namespace: str = "cid") -> str | None:
    """Download PubChem's computed 3D SDF for a CID or compound name.

    Parameters
    ----------
    identifier
        PubChem CID or compound name, matching ``namespace``.
    namespace
        ``"cid"`` or ``"name"``.

    Returns
    -------
    str or None
        SDF text with 3D coordinates, or ``None`` when PubChem has no
        3D conformer (404) or the request fails.

    Raises
    ------
    ValueError
        If ``namespace`` is neither ``"cid"`` nor ``"name"``.

    Examples
    --------
    >>> sdf = fetch_3d_sdf(2244)  # aspirin
    >>> sdf is None or "V2000" in sdf
    True
    """
    if namespace not in NAMESPACES:
        raise ValueError(f"namespace must be one of {sorted(NAMESPACES)}, got {namespace!r}")

    url = f"{PUG_BASE}/{namespace}/{quote(str(identifier))}/record/SDF"
    try:
        resp = get_with_retry(
            url,
            params={"record_type": "3d"},
            headers=make_headers(description="3D conformer fetch"),
            timeout=30,
        )
    except Exception:
        return None

    if resp.status_code != 200:
        return None

    text = resp.text
    if not text or len(text) > MAX_SDF_BYTES:
        return None
    return text if ("V2000" in text or "V3000" in text) else None
