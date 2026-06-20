"""
wikimolgen.sources - External chemical data source clients
==========================================================

Standalone API clients for enriching compound data from multiple
public chemical databases.  All functions are pure — no Streamlit
or web-UI dependencies — so they work from CLI or web equally.

Currently supported sources
--------------------------
* **Wikidata Query Service** — QID, Wikipedia titles, cross-references
  (ChEMBL, ChEBI, DrugBank, KEGG, CAS, ChemSpider, UNII)
* **PubChem PUG REST** — computed physicochemical properties
* **PubChem full record** — experimental data (melting/boiling point, etc.)
* **Wikipedia API** — infobox pharmacology data (ATC, legal status, etc.)
"""

from wikimolgen.sources.dailymed import fetch_dailymed_id
from wikimolgen.sources.pubchem_experimental import fetch_experimental_data
from wikimolgen.sources.pubchem_props import fetch_properties
from wikimolgen.sources.pubchem_substance import fetch_substances
from wikimolgen.sources.wikidata import query_wikidata
from wikimolgen.sources.wikipedia_infobox import fetch_infobox

__all__ = [
    "fetch_dailymed_id",
    "fetch_experimental_data",
    "fetch_infobox",
    "fetch_properties",
    "fetch_substances",
    "query_wikidata",
]
