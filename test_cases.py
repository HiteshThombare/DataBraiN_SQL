import pandas as pd
from merchant_classifier import MerchantClassifier
import unittest


class TestMerchantClassifier(unittest.TestCase):
    """
    Unit tests for MerchantClassifier
    """
    
    def setUp(self):
        """Initialize classifier for each test"""
        self.classifier = MerchantClassifier()
    
    def test_exact_match_uppercase(self):
        """Test exact matching with uppercase input"""
        cleaned, strategy = self.classifier.classify_merchant('ADANI POWER LTD')
        self.assertEqual(cleaned, 'Adani Power Ltd')
        self.assertEqual(strategy.value, 'exact')
    
    def test_exact_match_mixed_case(self):
        """Test exact matching with mixed case"""
        cleaned, strategy = self.classifier.classify_merchant('Adani Total Gas')
        self.assertEqual(cleaned, 'Adani Total Gas')
        self.assertEqual(strategy.value, 'exact')
    
    def test_keyword_match_adani_power(self):
        """Test keyword matching for Adani Power"""
        cleaned, strategy = self.classifier.classify_merchant('Adani power station')
        self.assertEqual(cleaned, 'Adani Power Ltd')
        self.assertEqual(strategy.value, 'keyword')
    
    def test_keyword_match_adani_gas(self):
        """Test keyword matching for Adani Gas"""
        cleaned, strategy = self.classifier.classify_merchant('Adani gas CNG')
        self.assertEqual(cleaned, 'Adani Total Gas')
        self.assertEqual(strategy.value, 'keyword')
    
    def test_keyword_match_fortune_oil(self):
        """Test keyword matching for Fortune Oil/Adani Wilmar"""
        cleaned, strategy = self.classifier.classify_merchant('Fortune Oil')
        self.assertEqual(cleaned, 'Adani Wilmar (Fortune)')
        self.assertEqual(strategy.value, 'keyword')
    
    def test_keyword_match_adani_ports(self):
        """Test keyword matching for Adani Ports"""
        cleaned, strategy = self.classifier.classify_merchant('Adani Ports SEZ')
        self.assertEqual(cleaned, 'Adani Ports & SEZ')
        self.assertEqual(strategy.value, 'keyword')
    
    def test_keyword_match_grt_jewellers(self):
        """Test keyword matching for GRT Jewellers with variations"""
        variations = ['G R T Jewellers', 'GRT Mumbai', 'G R Thangamalai']
        for variant in variations:
            cleaned, strategy = self.classifier.classify_merchant(variant)
            self.assertEqual(cleaned, 'GRT Jewellers')
            self.assertEqual(strategy.value, 'keyword')
    
    def test_keyword_match_ajio(self):
        """Test keyword matching for Ajio"""
        cleaned, strategy = self.classifier.classify_merchant('AJIO online')
        self.assertEqual(cleaned, 'Ajio Brand')
        self.assertEqual(strategy.value, 'keyword')
    
    def test_keyword_match_balaji_opticals(self):
        """Test keyword matching for Balaji Opticals"""
        cleaned, strategy = self.classifier.classify_merchant('Balaji Optical')
        self.assertEqual(cleaned, 'Balaji Opticals')
        self.assertEqual(strategy.value, 'keyword')
    
    def test_fuzzy_match(self):
        """Test fuzzy matching with typos"""
        # This tests fuzzy matching capability
        classifier = MerchantClassifier(fuzzy_threshold=0.70)
        cleaned, strategy = classifier.classify_merchant('ADNI PWR')
        # Should match to Adani Power Ltd via fuzzy matching
        self.assertIn(strategy.value, ['fuzzy', 'keyword'])
    
    def test_unknown_merchant(self):
        """Test handling of unknown merchants"""
        cleaned, strategy = self.classifier.classify_merchant('Completely Unknown Shop')
        self.assertEqual(cleaned, 'Unknown / Manual Review')
        self.assertEqual(strategy.value, 'unknown')
    
    def test_empty_string(self):
        """Test handling of empty string"""
        cleaned, strategy = self.classifier.classify_merchant('')
        self.assertEqual(cleaned, 'Unknown / Manual Review')
        self.assertEqual(strategy.value, 'unknown')
    
    def test_none_input(self):
        """Test handling of None input"""
        cleaned, strategy = self.classifier.classify_merchant(None)
        self.assertEqual(cleaned, 'Unknown / Manual Review')
        self.assertEqual(strategy.value, 'unknown')
    
    def test_dataframe_processing(self):
        """Test DataFrame processing"""
        df = pd.DataFrame({
            'Termownername': ['ADANI POWER', 'Adani gas', 'Unknown Retailer']
        })
        result_df = self.classifier.process_dataframe(df)
        
        # Check columns exist
        self.assertIn('Cleaned_Ownername', result_df.columns)
        self.assertIn('Match_Strategy', result_df.columns)
        
        # Check results
        self.assertEqual(result_df.iloc[0]['Cleaned_Ownername'], 'Adani Power Ltd')
        self.assertEqual(result_df.iloc[1]['Cleaned_Ownername'], 'Adani Total Gas')
        self.assertEqual(result_df.iloc[2]['Cleaned_Ownername'], 'Unknown / Manual Review')
    
    def test_report_generation(self):
        """Test classification report generation"""
        df = pd.DataFrame({
            'Termownername': ['ADANI POWER', 'Adani gas', 'Unknown']
        })
        self.classifier.process_dataframe(df)
        report = self.classifier.get_report()
        
        self.assertEqual(report['total_records'], 3)
        self.assertEqual(report['matched_records'], 2)
        self.assertEqual(report['unmatched_records'], 1)
        self.assertIn('match_rate', report)
    
    def test_normalization(self):
        """Test text normalization"""
        test_cases = [
            ('ADANI POWER', 'adani power'),
            ('Adani-Power_Ltd!', 'adani power ltd'),
            ('  Extra   Spaces  ', 'extra spaces'),
        ]
        
        for input_text, expected in test_cases:
            normalized = self.classifier._normalize_text(input_text)
            self.assertEqual(normalized, expected)
    
    def test_special_characters_handling(self):
        """Test handling of special characters"""
        variations = [
            'Adani & Ports @ SEZ',
            'Adani|Ports|SEZ',
            'Adani-Ports/SEZ',
        ]
        
        for variant in variations:
            cleaned, strategy = self.classifier.classify_merchant(variant)
            # Should still match to Adani Ports & SEZ
            self.assertNotEqual(strategy.value, 'unknown')
    
    def test_abbreviation_matching(self):
        """Test abbreviation matching"""
        abbreviations = {
            'ATG': 'Adani Total Gas',
            'APSEZ': 'Adani Ports & SEZ',
            'APL': 'Adani Power Ltd',
            'GRT': 'GRT Jewellers',
        }
        
        for abbr, expected_brand in abbreviations.items():
            cleaned, strategy = self.classifier.classify_merchant(abbr)
            self.assertEqual(cleaned, expected_brand)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
