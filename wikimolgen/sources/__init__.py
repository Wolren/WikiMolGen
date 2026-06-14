"""
wikimolgen.sources - External chemical data source clients
==========================================================

Standalone API clients for enriching compound data from multiple
public chemical databases.  All functions are pure — no Streamlit
or web-UI dependencies — so they work from CLI or web equally.

Currently supported sources
--------------------------
* **UniChem** — cross-reference identifier resolution
* **Wikidata Query Service** — QID, Wikipedia titles, property data
* **PubChem PUG REST** — physicochemical property enrichment
"""

from wikimolgen.sources.pubchem_props import fetch_properties
from wikimolgen.sources.unichem import resolve_unichem
from wikimolgen.sources.wikidata import query_wikidata

__all__ = ["fetch_properties", "resolve_unichem", "query_wikidata"]
