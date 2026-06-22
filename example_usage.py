import pandas as pd
from merchant_classifier import MerchantClassifier


def example_1_basic_classification():
    """
    Example 1: Basic merchant classification with default parameters
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: BASIC CLASSIFICATION")
    print("="*80)
    
    classifier = MerchantClassifier()
    
    test_merchants = [
        'ADANI POWER',
        'Adani Total Gas Limited',
        'Fortune Edible Oil',
        'APSEZ',
        'GRT Jewellery',
        'Ajio Online',
        'Balaji Spectacles',
    ]
    
    for merchant in test_merchants:
        cleaned, strategy = classifier.classify_merchant(merchant)
        print(f"{merchant:.<40} → {cleaned:.<35} [{strategy.value}]")


def example_2_dataframe_processing():
    """
    Example 2: Process entire DataFrame and export results
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: DATAFRAME PROCESSING & EXPORT")
    print("="*80)
    
    # Create sample transaction data
    transactions = {
        'Transaction_ID': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008],
        'Termownername': [
            'ADANI POWER LIMITED',
            'Adani gas station branch',
            'FORTUNE OIL PVT',
            'Adani Ports SEZ',
            'G R T Jewellers Mumbai',
            'AJIO retail outlet',
            'Balaji Optical Store',
            'Random Shop XYZ'
        ],
        'Amount': [5000, 1500, 2000, 10000, 3500, 1200, 800, 500]
    }
    
    df = pd.DataFrame(transactions)
    classifier = MerchantClassifier()
    result_df = classifier.process_dataframe(df)
    
    # Display results
    print("\nProcessed Transactions:")
    print(result_df[['Transaction_ID', 'Termownername', 'Cleaned_Ownername', 'Match_Strategy']].to_string(index=False))
    
    # Export
    result_df.to_csv('classified_merchants.csv', index=False)
    print("\n✓ Results saved to 'classified_merchants.csv'")
    
    # Show report
    report = classifier.get_report()
    print("\nClassification Report:")
    print(f"  Total Records: {report['total_records']}")
    print(f"  Matched: {report['matched_records']}")
    print(f"  Unmatched: {report['unmatched_records']}")
    print(f"  Success Rate: {report['match_rate']}")


def example_3_typo_and_variation_handling():
    """
    Example 3: Demonstrate typo and structural variation handling
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: TYPO & VARIATION HANDLING")
    print("="*80)
    
    classifier = MerchantClassifier(fuzzy_threshold=0.70)
    
    variations = {
        'Adani Power': ['ADANI POWER', 'Adni Power', 'ADANI PWR', 'adanipower'],
        'Adani Total Gas': ['ADANI GAS', 'Adani Totak Gas', 'adani gas', 'ATG'],
        'Adani Wilmar (Fortune)': ['FORTUNE', 'Fortune Oil', 'FORTUNE OIL PVT', 'wilmar'],
        'GRT Jewellers': ['GRT', 'G R T', 'G R T Jewellers', 'grthangamalai']
    }
    
    print("\nTesting variation handling:")
    for brand, variants in variations.items():
        print(f"\n{brand}:")
        for variant in variants:
            cleaned, strategy = classifier.classify_merchant(variant)
            status = '✓' if cleaned == brand else '✗'
            print(f"  {status} {variant:.<35} → {cleaned} [{strategy.value}]")


def example_4_custom_fuzzy_threshold():
    """
    Example 4: Adjust fuzzy matching threshold for sensitivity
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: CUSTOM FUZZY THRESHOLD TUNING")
    print("="*80)
    
    test_merchant = 'ADNI PWR'  # Typo: should be ADANI POWER
    
    for threshold in [0.50, 0.65, 0.75, 0.85]:
        classifier = MerchantClassifier(fuzzy_threshold=threshold)
        cleaned, strategy = classifier.classify_merchant(test_merchant)
        print(f"Threshold {threshold}: {test_merchant} → {cleaned} [{strategy.value}]")


def example_5_bulk_processing_with_stats():
    """
    Example 5: Bulk processing with detailed statistics
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: BULK PROCESSING WITH STATISTICS")
    print("="*80)
    
    # Create larger sample dataset
    import random
    merchants = [
        'ADANI POWER LTD',
        'adani power',
        'Adani Total Gas',
        'ATG Station',
        'Fortune Oil Co',
        'Adani Ports',
        'GRT Jewels',
        'G R T Mumbai',
        'AJIO Store',
        'ajio',
        'Balaji Opticals',
        'Unknown Retailer',
        'XYZ Shop',
    ] * 10  # Repeat for bulk processing
    
    df = pd.DataFrame({'Termownername': merchants})
    classifier = MerchantClassifier()
    result_df = classifier.process_dataframe(df)
    
    # Detailed statistics
    report = classifier.get_report()
    print(f"\nProcessing Summary:")
    print(f"  Total Records Processed: {report['total_records']}")
    print(f"  Successfully Matched: {report['matched_records']} ({report['match_rate']})")
    print(f"  Requiring Manual Review: {report['unmatched_records']}")
    
    # Category-wise breakdown
    print(f"\nCleanup Results by Brand:")
    cleaned_counts = result_df['Cleaned_Ownername'].value_counts()
    for brand, count in cleaned_counts.items():
        print(f"  {brand}: {count}")


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# MERCHANT CLASSIFIER - COMPREHENSIVE EXAMPLES")
    print("#"*80)
    
    example_1_basic_classification()
    example_2_dataframe_processing()
    example_3_typo_and_variation_handling()
    example_4_custom_fuzzy_threshold()
    example_5_bulk_processing_with_stats()
    
    print("\n" + "#"*80)
    print("# ALL EXAMPLES COMPLETED")
    print("#"*80)
