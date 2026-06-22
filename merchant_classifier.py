import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from typing import Dict, List, Tuple
import re
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MatchStrategy(Enum):
    """Strategies for matching merchant names"""
    EXACT = "exact"
    KEYWORD = "keyword"
    FUZZY = "fuzzy"
    UNKNOWN = "unknown"


@dataclass
class MasterBrand:
    """Represents a master brand with metadata"""
    name: str
    keywords: List[str]
    industry_modifiers: List[str]
    abbreviations: List[str]
    parent_company: str = None
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return self.name == other.name


class MerchantClassifier:
    """
    Enterprise-grade merchant name classifier for financial transaction data.
    
    Features:
    - Hierarchical matching (exact → keyword → fuzzy)
    - Typo handling and structural variations
    - Parent-child brand distinction
    - Configurable fuzzy matching threshold
    - Audit trail logging
    """
    
    def __init__(self, fuzzy_threshold: float = 0.75):
        """
        Initialize the classifier with master brands.
        
        Args:
            fuzzy_threshold: Similarity score threshold for fuzzy matching (0-1)
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.master_brands: Dict[str, MasterBrand] = {}
        self.matched_records = []
        self.unmatched_records = []
        self._initialize_master_brands()
    
    def _initialize_master_brands(self):
        """
        Initialize master brand definitions with keywords and modifiers.
        This is the single source of truth for brand hierarchies.
        """
        brands = [
            MasterBrand(
                name="Adani Power Ltd",
                keywords=["adani", "power"],
                industry_modifiers=["power", "energy", "electricity"],
                abbreviations=["apl", "adanipower"],
                parent_company="Adani Group"
            ),
            MasterBrand(
                name="Adani Total Gas",
                keywords=["adani", "gas"],
                industry_modifiers=["gas", "cng", "lng", "fuel"],
                abbreviations=["atg", "adanigas"],
                parent_company="Adani Group"
            ),
            MasterBrand(
                name="Adani Wilmar (Fortune)",
                keywords=["adani", "wilmar", "fortune"],
                industry_modifiers=["oil", "food", "edible", "fortune"],
                abbreviations=["fortune", "aw", "adaniwilmar"],
                parent_company="Adani Group"
            ),
            MasterBrand(
                name="Adani Ports & SEZ",
                keywords=["adani", "ports", "sez"],
                industry_modifiers=["port", "logistics", "sez", "shipping"],
                abbreviations=["apsez", "adaniports"],
                parent_company="Adani Group"
            ),
            MasterBrand(
                name="GRT Jewellers",
                keywords=["grt", "jeweller", "jewellery"],
                industry_modifiers=["jewel", "gold", "silver", "diamond"],
                abbreviations=["grt", "grjewel", "thangamalai"],
                parent_company=None
            ),
            MasterBrand(
                name="Ajio Brand",
                keywords=["ajio"],
                industry_modifiers=["retail", "fashion", "ecommerce"],
                abbreviations=["ajio"],
                parent_company="Reliance"
            ),
            MasterBrand(
                name="Balaji Opticals",
                keywords=["balaji", "optical"],
                industry_modifiers=["optical", "eyewear", "spectacles"],
                abbreviations=["balaji", "boptical"],
                parent_company=None
            ),
        ]
        
        for brand in brands:
            self.master_brands[brand.name] = brand
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize merchant name for comparison.
        - Convert to lowercase
        - Remove special characters
        - Remove extra whitespace
        - Handle common abbreviations
        """
        if not isinstance(text, str):
            return ""
        
        text = text.lower().strip()
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-z0-9\s]', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _exact_match(self, merchant_name: str, normalized_name: str) -> Tuple[bool, str]:
        """
        Check for exact match against master brands.
        """
        normalized_merchant = normalized_name
        
        for brand_name, brand in self.master_brands.items():
            normalized_brand = self._normalize_text(brand_name)
            
            if normalized_merchant == normalized_brand:
                return True, brand_name
        
        return False, None
    
    def _keyword_match(self, merchant_name: str, normalized_name: str) -> Tuple[bool, str]:
        """
        Match based on primary keywords and industry modifiers.
        
        Priority:
        1. Parent brand + industry modifier (e.g., "Adani" + "Gas")
        2. Abbreviation match
        3. Single keyword match (fallback)
        """
        tokens = normalized_name.split()
        
        best_matches = []
        
        for brand_name, brand in self.master_brands.items():
            match_score = 0
            
            # Check for abbreviation matches
            for abbr in brand.abbreviations:
                if abbr in normalized_name:
                    match_score += 10
            
            # Check for parent brand + industry modifier combination
            brand_tokens = self._normalize_text(brand_name).split()
            parent_keyword = brand_tokens[0] if brand_tokens else ""
            
            has_parent = any(parent_keyword in token for token in tokens)
            has_modifier = any(mod in normalized_name for mod in brand.industry_modifiers)
            
            if has_parent and has_modifier:
                match_score += 100
            elif has_parent:
                match_score += 50
            elif has_modifier:
                match_score += 30
            
            # Check for keyword presence
            for keyword in brand.keywords:
                if keyword in normalized_name:
                    match_score += 5
            
            if match_score > 0:
                best_matches.append((match_score, brand_name))
        
        if best_matches:
            best_matches.sort(reverse=True, key=lambda x: x[0])
            return True, best_matches[0][1]
        
        return False, None
    
    def _fuzzy_match(self, merchant_name: str, normalized_name: str) -> Tuple[bool, str]:
        """
        Fuzzy matching using sequence similarity as fallback.
        Returns highest matching score above threshold.
        """
        best_match = None
        best_score = 0
        
        for brand_name, brand in self.master_brands.items():
            normalized_brand = self._normalize_text(brand_name)
            
            # Calculate similarity
            similarity = SequenceMatcher(None, normalized_name, normalized_brand).ratio()
            
            if similarity > best_score and similarity >= self.fuzzy_threshold:
                best_score = similarity
                best_match = brand_name
        
        if best_match:
            return True, best_match
        
        return False, None
    
    def classify_merchant(self, merchant_name: str) -> Tuple[str, MatchStrategy]:
        """
        Classify a single merchant name using hierarchical strategy.
        
        Hierarchy:
        1. Exact Match
        2. Keyword Match (with parent-child logic)
        3. Fuzzy Match
        4. Unknown / Manual Review
        
        Args:
            merchant_name: Raw merchant name from transaction data
        
        Returns:
            Tuple of (cleaned_name, match_strategy)
        """
        if not merchant_name or not isinstance(merchant_name, str):
            return "Unknown / Manual Review", MatchStrategy.UNKNOWN
        
        normalized = self._normalize_text(merchant_name)
        
        if not normalized:
            return "Unknown / Manual Review", MatchStrategy.UNKNOWN
        
        # Strategy 1: Exact Match
        matched, result = self._exact_match(merchant_name, normalized)
        if matched:
            logger.debug(f"EXACT MATCH: '{merchant_name}' → '{result}'")
            return result, MatchStrategy.EXACT
        
        # Strategy 2: Keyword Match (Smart parent-child distinction)
        matched, result = self._keyword_match(merchant_name, normalized)
        if matched:
            logger.debug(f"KEYWORD MATCH: '{merchant_name}' → '{result}'")
            return result, MatchStrategy.KEYWORD
        
        # Strategy 3: Fuzzy Match
        matched, result = self._fuzzy_match(merchant_name, normalized)
        if matched:
            logger.debug(f"FUZZY MATCH: '{merchant_name}' → '{result}' (score: {self.fuzzy_threshold})")
            return result, MatchStrategy.FUZZY
        
        # Strategy 4: Unknown
        logger.warning(f"NO MATCH: '{merchant_name}' → Unknown / Manual Review")
        return "Unknown / Manual Review", MatchStrategy.UNKNOWN
    
    def process_dataframe(self, df: pd.DataFrame, column_name: str = "Termownername") -> pd.DataFrame:
        """
        Process entire DataFrame of merchant names.
        
        Args:
            df: DataFrame containing merchant names
            column_name: Name of the column containing raw merchant names
        
        Returns:
            DataFrame with added 'Cleaned_Ownername' and 'Match_Strategy' columns
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")
        
        results = []
        
        for idx, merchant_name in df[column_name].items():
            cleaned_name, strategy = self.classify_merchant(merchant_name)
            results.append({
                'Original_Ownername': merchant_name,
                'Cleaned_Ownername': cleaned_name,
                'Match_Strategy': strategy.value,
                'Index': idx
            })
            
            if strategy == MatchStrategy.UNKNOWN:
                self.unmatched_records.append(merchant_name)
            else:
                self.matched_records.append(cleaned_name)
        
        result_df = pd.DataFrame(results)
        # Merge with original dataframe
        output_df = df.copy()
        output_df['Cleaned_Ownername'] = result_df['Cleaned_Ownername']
        output_df['Match_Strategy'] = result_df['Match_Strategy']
        
        return output_df
    
    def get_report(self) -> Dict:
        """
        Generate classification report with statistics.
        """
        total = len(self.matched_records) + len(self.unmatched_records)
        matched_count = len(self.matched_records)
        unmatched_count = len(self.unmatched_records)
        
        return {
            'total_records': total,
            'matched_records': matched_count,
            'unmatched_records': unmatched_count,
            'match_rate': f"{(matched_count/total*100):.2f}%" if total > 0 else "0%",
            'unmatched_merchants': list(set(self.unmatched_records))
        }
    
    def export_results(self, output_df: pd.DataFrame, filepath: str):
        """
        Export classification results to CSV.
        """
        output_df.to_csv(filepath, index=False)
        logger.info(f"Results exported to {filepath}")


if __name__ == "__main__":
    # Example usage
    classifier = MerchantClassifier(fuzzy_threshold=0.75)
    
    # Test with sample data
    test_data = {
        'Termownername': [
            'ADANI POWER LTD',
            'Adani gas station',
            'FORTUNE OIL',
            'Adani ports',
            'G R T Jewellers',
            'GRT Mumbai',
            'AJIO store',
            'Balaji Opticals',
            'Unknown Merchant',
            'adanipower'
        ]
    }
    
    df = pd.DataFrame(test_data)
    result_df = classifier.process_dataframe(df)
    
    print("\n" + "="*80)
    print("MERCHANT CLASSIFICATION RESULTS")
    print("="*80)
    print(result_df[['Termownername', 'Cleaned_Ownername', 'Match_Strategy']].to_string())
    
    print("\n" + "="*80)
    print("CLASSIFICATION REPORT")
    print("="*80)
    report = classifier.get_report()
    for key, value in report.items():
        if key != 'unmatched_merchants':
            print(f"{key}: {value}")
    
    if report['unmatched_merchants']:
        print(f"\nMerchants Requiring Manual Review:")
        for merchant in report['unmatched_merchants']:
            print(f"  - {merchant}")
