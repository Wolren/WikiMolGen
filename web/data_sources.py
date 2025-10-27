"""
web/data_sources.py
====================

Abstract data source interface and concrete implementations for fetching 
compound metadata from various sources (PubChem, Wikipedia, KEGG, etc.).

This module provides a modular, extensible architecture for aggregating 
chemical compound data from multiple sources with intelligent fallback 
and deduplication.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Set
from enum import Enum
import warnings

try:
    import pubchempy as pcp
except ImportError:
    pcp = None

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Enumeration of supported data sources."""
    PUBCHEM = "pubchem"
    WIKIPEDIA = "wikipedia"
    KEGG = "kegg"
    CHEMSPIDER = "chemspider"
    DRUGBANK = "drugbank"


@dataclass
class CompoundData:
    """
    Comprehensive compound metadata container.
    
    Uses lazy loading for expensive operations and provides
    automatic field validation and deduplication.
    """
    
    # Core Identifiers
    cid: Optional[str] = None  # PubChem CID
    iupac_name: Optional[str] = None
    common_names: List[str] = field(default_factory=list)
    trade_names: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    
    # Chemical Identifiers
    cas_number: Optional[str] = None
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchikey: Optional[str] = None
    chemspider_id: Optional[str] = None
    kegg_id: Optional[str] = None
    chebi_id: Optional[str] = None
    chembl_id: Optional[str] = None
    drugbank_id: Optional[str] = None
    unii_code: Optional[str] = None
    wikidata_qid: Optional[str] = None
    
    # Physical Properties
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    exact_mass: Optional[float] = None
    density: Optional[float] = None
    melting_point: Optional[str] = None  # Can have units/ranges
    boiling_point: Optional[str] = None
    appearance: Optional[str] = None
    color: Optional[str] = None
    odor: Optional[str] = None
    
    # Solubility & pH
    solubility: Optional[str] = None
    ph: Optional[float] = None
    pka_values: List[float] = field(default_factory=list)
    
    # Pharmaceutical Data
    drug_class: List[str] = field(default_factory=list)
    atc_code: Optional[str] = None
    mechanism_of_action: Optional[str] = None
    indications: List[str] = field(default_factory=list)
    routes_of_administration: List[str] = field(default_factory=list)
    half_life: Optional[str] = None
    bioavailability: Optional[str] = None
    protein_binding: Optional[str] = None
    metabolism: Optional[str] = None
    
    # Safety & Hazards
    hazards: Dict[str, str] = field(default_factory=dict)  # GHS classifications
    ld50: Optional[str] = None
    storage_conditions: Optional[str] = None
    
    # Additional Data
    description: Optional[str] = None
    wikipedia_url: Optional[str] = None
    pubchem_url: Optional[str] = None
    
    # Metadata
    sources: Set[DataSourceType] = field(default_factory=set)
    last_updated: Optional[str] = None
    confidence_score: float = 0.0  # How confident are we in this data?
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, filtering None values and converting sets."""
        data = asdict(self)
        data['sources'] = [s.value for s in self.sources]
        return {k: v for k, v in data.items() if v is not None and v != []}
    
    def merge(self, other: 'CompoundData') -> 'CompoundData':
        """
        Merge another CompoundData instance, preferring non-None values.
        
        Parameters
        ----------
        other : CompoundData
            Another instance to merge
            
        Returns
        -------
        CompoundData
            Merged instance with deduplicated lists
        """
        merged = CompoundData()
        
        # Handle simple fields - prefer current if set
        for field_name in ['cid', 'iupac_name', 'cas_number', 'smiles', 'inchi', 
                          'inchikey', 'molecular_formula', 'molecular_weight']:
            current = getattr(self, field_name)
            other_val = getattr(other, field_name)
            setattr(merged, field_name, current or other_val)
        
        # Handle list fields - deduplicate and merge
        for field_name in ['common_names', 'trade_names', 'synonyms', 'drug_class',
                          'indications', 'routes_of_administration', 'pka_values']:
            current_list = getattr(self, field_name) or []
            other_list = getattr(other, field_name) or []
            merged_list = list(set(current_list) | set(other_list))
            setattr(merged, field_name, merged_list)
        
        # Handle dictionary fields - merge
        merged.hazards = {**self.hazards, **other.hazards}
        
        # Combine sources
        merged.sources = self.sources | other.sources
        
        return merged
    
    def validate(self) -> bool:
        """
        Validate that essential fields are populated.
        
        Returns
        -------
        bool
            True if basic data is present
        """
        return bool(self.cid or self.iupac_name or self.inchi or self.smiles)


class DataSource(ABC):
    """Abstract base class for compound data sources."""
    
    @abstractmethod
    def fetch(self, identifier: str) -> Optional[CompoundData]:
        """
        Fetch compound data from this source.
        
        Parameters
        ----------
        identifier : str
            Compound identifier (CID, name, SMILES, etc.)
            
        Returns
        -------
        Optional[CompoundData]
            Compound data or None if not found
        """
        pass
    
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """Return the source type."""
        pass


class PubChemSource(DataSource):
    """PubChem data source implementation."""
    
    MAX_RETRIES = 3
    TIMEOUT = 10
    
    def __init__(self):
        if pcp is None:
            raise ImportError("pubchempy is required for PubChemSource")
        self.logger = logging.getLogger(__name__)
    
    def source_type(self) -> DataSourceType:
        return DataSourceType.PUBCHEM
    
    def fetch(self, identifier: str) -> Optional[CompoundData]:
        """
        Fetch extended compound data from PubChem.
        
        Parameters
        ----------
        identifier : str
            PubChem CID, compound name, or SMILES
            
        Returns
        -------
        Optional[CompoundData]
            Comprehensive compound metadata
        """
        try:
            compounds = self._search_pubchem(identifier)
            if not compounds:
                return None
            
            compound = compounds[0]
            return self._extract_compound_data(compound)
            
        except Exception as e:
            self.logger.warning(f"PubChem fetch failed for {identifier}: {e}")
            return None
    
    def _search_pubchem(self, identifier: str) -> Optional[List]:
        """Search PubChem with fallback strategy."""
        try:
            # Try CID first
            if identifier.isdigit():
                return pcp.get_compounds(identifier, 'cid')
            
            # Try name
            compounds = pcp.get_compounds(identifier, 'name')
            if compounds:
                return compounds
            
            # Try SMILES
            return pcp.get_compounds(identifier, 'smiles')
            
        except Exception as e:
            self.logger.debug(f"PubChem search error: {e}")
            return None
    
    def _extract_compound_data(self, compound) -> CompoundData:
        """Extract comprehensive data from PubChem compound object."""
        data = CompoundData(sources={self.source_type()})
        
        # Core identifiers
        data.cid = str(compound.cid) if hasattr(compound, 'cid') else None
        data.iupac_name = getattr(compound, 'iupac_name', None)
        data.synonyms = self._extract_names(compound)
        data.cas_number = self._extract_cas(compound)
        
        # Chemical identifiers
        data.smiles = getattr(compound, 'smiles', None) or \
                     getattr(compound, 'canonical_smiles', None)
        data.inchi = getattr(compound, 'inchi', None)
        data.inchikey = getattr(compound, 'inchikey', None)
        
        # Physical properties
        data.molecular_formula = getattr(compound, 'molecular_formula', None)
        data.molecular_weight = getattr(compound, 'molecular_weight', None)
        data.exact_mass = getattr(compound, 'exact_mass', None)
        data.appearance = self._extract_appearance(compound)
        
        # External IDs
        data.chemspider_id = self._get_property(compound, 'ChemSpider ID')
        data.kegg_id = self._get_property(compound, 'KEGG')
        data.chebi_id = self._get_property(compound, 'ChEBI')
        data.chembl_id = self._get_property(compound, 'ChEMBL')
        data.drugbank_id = self._get_property(compound, 'DrugBank ID')
        data.unii_code = self._get_property(compound, 'UNII')
        
        # URLs
        if data.cid:
            data.pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{data.cid}"
        
        return data
    
    def _extract_names(self, compound) -> List[str]:
        """Extract and deduplicate compound names."""
        names = set()
        
        if hasattr(compound, 'synonyms') and compound.synonyms:
            names.update(compound.synonyms[:10])  # Limit to first 10
        
        if hasattr(compound, 'iupac_name') and compound.iupac_name:
            names.add(compound.iupac_name)
        
        return list(names)
    
    def _extract_cas(self, compound) -> Optional[str]:
        """Extract CAS number from compound properties."""
        try:
            if hasattr(compound, 'cid'):
                # CAS numbers are in the 'CAS' property
                cas = self._get_property(compound, 'CAS')
                return cas if cas else None
        except Exception:
            pass
        return None
    
    def _extract_appearance(self, compound) -> Optional[str]:
        """Extract appearance information."""
        try:
            return self._get_property(compound, 'Physical Description')
        except Exception:
            return None
    
    def _get_property(self, compound, prop_name: str) -> Optional[str]:
        """Safely extract a specific property from compound object."""
        try:
            if hasattr(compound, 'to_dict'):
                props = compound.to_dict()
                return props.get(prop_name)
        except Exception:
            pass
        return None


class WikipediaSource(DataSource):
    """Wikipedia data source for compound infobox parsing."""
    
    def __init__(self):
        if requests is None or BeautifulSoup is None:
            raise ImportError("requests and beautifulsoup4 required for WikipediaSource")
        self.logger = logging.getLogger(__name__)
        self.timeout = 10
    
    def source_type(self) -> DataSourceType:
        return DataSourceType.WIKIPEDIA
    
    def fetch(self, identifier: str) -> Optional[CompoundData]:
        """
        Fetch compound data from Wikipedia infobox.
        
        Parameters
        ----------
        identifier : str
            Compound name or identifier
            
        Returns
        -------
        Optional[CompoundData]
            Compound data extracted from Wikipedia
        """
        try:
            # Search for article
            article_title = self._search_wikipedia(identifier)
            if not article_title:
                return None
            
            # Fetch infobox data
            infobox_data = self._extract_infobox(article_title)
            if not infobox_data:
                return None
            
            return self._parse_infobox_to_compound_data(infobox_data, article_title)
            
        except Exception as e:
            self.logger.warning(f"Wikipedia fetch failed for {identifier}: {e}")
            return None
    
    def _search_wikipedia(self, identifier: str) -> Optional[str]:
        """Search for a Wikipedia article about the compound."""
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'srsearch': identifier,
                'srnamespace': 0,
                'srlimit': 1
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            if data.get('query', {}).get('search'):
                return data['query']['search'][0]['title']
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Wikipedia search error: {e}")
            return None
    
    def _extract_infobox(self, article_title: str) -> Optional[Dict]:
        """Extract infobox data from Wikipedia article."""
        try:
            url = "https://en.wikipedia.org/wiki/" + article_title.replace(' ', '_')
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            infobox = soup.find('table', {'class': 'infobox'})
            
            if not infobox:
                return None
            
            data = {}
            for row in infobox.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        data[key] = value
            
            return data if data else None
            
        except Exception as e:
            self.logger.debug(f"Infobox extraction error: {e}")
            return None
    
    def _parse_infobox_to_compound_data(
        self, 
        infobox_data: Dict, 
        article_title: str
    ) -> CompoundData:
        """Parse infobox data into CompoundData structure."""
        data = CompoundData(sources={self.source_type()})
        
        # Common infobox field mappings
        field_map = {
            'IUPAC name': 'iupac_name',
            'Molecular formula': 'molecular_formula',
            'Molar mass': 'molecular_weight',
            'Appearance': 'appearance',
            'Density': 'density',
            'Melting point': 'melting_point',
            'Boiling point': 'boiling_point',
            'CAS Number': 'cas_number',
        }
        
        for wiki_field, data_field in field_map.items():
            if wiki_field in infobox_data:
                try:
                    value = infobox_data[wiki_field]
                    if data_field == 'molecular_weight':
                        # Try to extract numeric value
                        numeric_val = ''.join(c for c in value.split()[0] if c.isdigit() or c == '.')
                        setattr(data, data_field, float(numeric_val))
                    else:
                        setattr(data, data_field, value)
                except (ValueError, IndexError):
                    pass
        
        data.wikipedia_url = f"https://en.wikipedia.org/wiki/{article_title.replace(' ', '_')}"
        return data


class DataAggregator:
    """
    Aggregates compound data from multiple sources with intelligent
    fallback, deduplication, and confidence scoring.
    """
    
    def __init__(self, sources: Optional[List[DataSource]] = None):
        """
        Initialize aggregator with data sources.
        
        Parameters
        ----------
        sources : Optional[List[DataSource]]
            List of data sources to use. If None, uses PubChem by default.
        """
        self.logger = logging.getLogger(__name__)
        
        if sources is None:
            sources = []
            try:
                sources.append(PubChemSource())
            except ImportError:
                self.logger.warning("pubchempy not available")
            
            try:
                sources.append(WikipediaSource())
            except ImportError:
                self.logger.warning("requests/beautifulsoup4 not available")
        
        self.sources = sources
    
    def fetch_compound(
        self, 
        identifier: str,
        use_caching: bool = True
    ) -> Optional[CompoundData]:
        """
        Fetch compound data from all available sources and aggregate results.
        
        Parameters
        ----------
        identifier : str
            Compound identifier
        use_caching : bool
            Whether to cache results
            
        Returns
        -------
        Optional[CompoundData]
            Aggregated compound data or None if not found
        """
        if not self.sources:
            self.logger.error("No data sources configured")
            return None
        
        results = []
        
        for source in self.sources:
            try:
                data = source.fetch(identifier)
                if data and data.validate():
                    results.append(data)
                    self.logger.debug(f"Successfully fetched from {source.source_type().value}")
            except Exception as e:
                self.logger.warning(f"Error fetching from {source.source_type().value}: {e}")
        
        if not results:
            return None
        
        # Merge results
        merged = results[0]
        for result in results[1:]:
            merged = merged.merge(result)
        
        # Calculate confidence
        merged.confidence_score = len(merged.sources) / len(self.sources)
        
        return merged


# Convenience function
def get_default_aggregator() -> DataAggregator:
    """Get aggregator with default sources."""
    return DataAggregator()
