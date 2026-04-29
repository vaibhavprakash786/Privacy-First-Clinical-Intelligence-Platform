import csv
import logging
import os
import re
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PMBJPItem(BaseModel):
    sr_no: str
    drug_code: str
    generic_name: str
    unit_size: str
    mrp: float
    group_name: str

class PMBJPCatalog:
    def __init__(self, csv_path: str = None):
        if not csv_path:
            # Default to the copied data directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            csv_path = os.path.join(base_dir, "data", "pmbjp_list.csv")
            
        self.csv_path = csv_path
        self.catalog: List[PMBJPItem] = []
        self._load_catalog()
        
    def _load_catalog(self):
        """Loads the PMBJP CSV product list into memory."""
        try:
            with open(self.csv_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Parse row safely, turning empty strings into defaults
                    item = PMBJPItem(
                        sr_no=row.get('Sr No', '').strip(),
                        drug_code=row.get('Drug Code', '').strip(),
                        generic_name=row.get('Generic Name', '').strip(),
                        unit_size=row.get('Unit Size', '').strip(),
                        mrp=float(row.get('MRP', '0').strip() or 0),
                        group_name=row.get('Group Name', '').strip()
                    )
                    self.catalog.append(item)
            logger.info(f"Loaded {len(self.catalog)} PMBJP items into catalog.")
        except Exception as e:
            logger.error(f"Failed to load PMBJP catalog from {self.csv_path}: {e}")
            self.catalog = []

    def _normalize_text(self, text: str) -> str:
        """Lowercases, removes special chars, and normalizes spacing for matching."""
        if not text:
            return ""
        text = text.lower()
        
        # Standardize common spelling variations
        text = text.replace('amoxicillin', 'amoxycillin')
        text = text.replace('acetaminophen', 'paracetamol')
        text = text.replace('levocetirizine', 'levocetrizine')
        
        # Remove common dosage forms from the text to focus on composition
        text = re.sub(r'\b(tablets?|capsules?|syrup|suspension|injection|gel|cream|ointment|drops|oral|prolonged release|sustained release|enteric coated|ip|bp|usp|wfi|vial)\b', '', text)
        text = re.sub(r'[^a-z0-9\s+]', ' ', text)
        return ' '.join(text.split())

    def _calculate_score(self, query_tokens: set, target_tokens: set) -> float:
        """Calculates a simple Jaccard-like similarity score."""
        if not query_tokens or not target_tokens:
            return 0.0
        intersection = query_tokens.intersection(target_tokens)
        
        # Compare against the shorter set to boost scores for partial ingredient matches
        min_len = min(len(query_tokens), len(target_tokens))
        return len(intersection) / min_len if min_len > 0 else 0.0

    def find_best_match(self, composition: str) -> Optional[PMBJPItem]:
        """
        Takes a generic composition string (e.g. 'Amoxycillin + Potassium Clavulanate')
        and attempts to fuzzy match it against the official PMBJP catalog.
        Returns the best matching PMBJPItem, or None if no good match is found.
        """
        if not self.catalog:
            return None
            
        best_match = None
        best_score = 0.0
        
        normalized_query = self._normalize_text(composition)
        query_tokens = set(normalized_query.split())
        
        for item in self.catalog:
            normalized_target = self._normalize_text(item.generic_name)
            target_tokens = set(normalized_target.split())
            
            score = self._calculate_score(query_tokens, target_tokens)
            
            if score > best_score:
                best_score = score
                best_match = item
                
        # Lowered threshold to 0.4 and using min_len in Jaccard ensures robust matching for active ingredients.
        if best_score >= 0.4:
            return best_match
            
        return None

# Singleton instance to be imported and used globally
catalog_instance = PMBJPCatalog()

def get_catalog() -> PMBJPCatalog:
    return catalog_instance
