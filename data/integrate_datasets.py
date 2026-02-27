"""
Dataset Integration Script
Combines Dataset 1 (Global Personal Finance) with Dataset 2 (India Personal Finance)
Creates unified dataset with 52,424 records for ML training
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_dataset_1():
    """Load Dataset 1 (Global Personal Finance - 32,424 records)"""
    print("📂 Loading Dataset 1 (Global Personal Finance)...")
    df = pd.read_csv('data/personal_finance_global.csv')
    print(f"   ✓ Loaded {len(df):,} records")
    return df

def load_dataset_2():
    """Load Dataset 2 (India Personal Finance - 20,000 records)"""
    print("📂 Loading Dataset 2 (India Personal Finance)...")
    try:
        df = pd.read_csv('data/india_personal_finance.csv')
    except FileNotFoundError:
        df = pd.read_csv('data/indian_personal_finance.csv')
    print(f"   ✓ Loaded {len(df):,} records")
    return df

def extract_loan_data_from_dataset1(df1):
    """Extract loan information from Dataset 1"""
    print("\n🔍 Extracting loan data from Dataset 1...")
    
    # Filter only records with loans
    df_with_loans = df1[df1['has_loan'] == 'Yes'].copy()
    print(f"   ✓ Found {len(df_with_loans):,} records with loans")
    
    # Extract loan features
    loan_data = pd.DataFrame({
        'user_id': df_with_loans['user_id'],
        'loan_type': df_with_loans['loan_type'],
        'loan_amount': df_with_loans['loan_amount_usd'],
        'loan_tenure_months': df_with_loans['loan_term_months'],
        'monthly_emi': df_with_loans['monthly_emi_usd'],
        'interest_rate': df_with_loans['loan_interest_rate_pct'],
        'has_loan': True
    })
    
    return loan_data

def extract_financial_data_from_dataset1(df1):
    """Extract financial data from Dataset 1"""
    print("\n🔍 Extracting financial data from Dataset 1...")
    
    financial_data = pd.DataFrame({
        'user_id': df1['user_id'],
        'income': df1['monthly_income_usd'],
        'expenses': df1['monthly_expenses_usd'],
        'savings': df1['savings_usd'],
        'emi': df1['monthly_emi_usd'],
        'age': df1['age'],
        'credit_score': df1['credit_score'],
        'source': 'dataset1'
    })
    
    print(f"   ✓ Extracted financial data for {len(financial_data):,} records")
    return financial_data

def extract_financial_data_from_dataset2(df2):
    """Extract financial data from Dataset 2"""
    print("\n🔍 Extracting financial data from Dataset 2...")
    
    financial_data = pd.DataFrame({
        'user_id': ['IND_' + str(i) for i in range(len(df2))],  # Generate unique IDs
        'income': df2['Income'],
        'rent': df2['Rent'],
        'food': df2['Groceries'],
        'travel': df2['Transport'],
        'shopping': df2['Eating_Out'] + df2['Entertainment'],
        'emi': df2['Loan_Repayment'],
        'savings': df2['Disposable_Income'],
        'age': df2['Age'],
        'expenses': (df2['Rent'] + df2['Loan_Repayment'] + df2['Insurance'] + 
                    df2['Groceries'] + df2['Transport'] + df2['Eating_Out'] + 
                    df2['Entertainment'] + df2['Utilities'] + df2['Healthcare'] + 
                    df2['Education'] + df2['Miscellaneous']),
        'source': 'dataset2'
    })
    
    print(f"   ✓ Extracted financial data for {len(financial_data):,} records")
    return financial_data

def combine_datasets(df1_financial, df2_financial, df1_loans):
    """Combine both datasets into unified format"""
    print("\n🔗 Combining datasets...")
    
    # Combine financial data from both datasets
    combined_financial = pd.concat([df1_financial, df2_financial], ignore_index=True)
    print(f"   ✓ Combined financial data: {len(combined_financial):,} records")
    
    # Merge loan data with Dataset 1 financial data
    df1_with_loans = df1_financial.merge(df1_loans, on='user_id', how='left')
    df1_with_loans['has_loan'] = df1_with_loans['has_loan'].fillna(False)
    
    # Dataset 2 doesn't have detailed loan data, so we'll use basic EMI
    df2_financial['has_loan'] = df2_financial['emi'] > 0
    df2_financial['loan_type'] = None
    df2_financial['loan_amount'] = None
    df2_financial['loan_tenure_months'] = None
    df2_financial['monthly_emi'] = df2_financial['emi']
    df2_financial['interest_rate'] = None
    
    # Combine all data
    combined = pd.concat([df1_with_loans, df2_financial], ignore_index=True)
    
    print(f"   ✓ Final combined dataset: {len(combined):,} records")
    return combined

def validate_combined_data(df):
    """Validate the combined dataset"""
    print("\n✅ Validating combined dataset...")
    
    # Check for missing values in critical columns
    critical_cols = ['income', 'expenses', 'savings', 'emi']
    missing = df[critical_cols].isnull().sum()
    
    if missing.sum() > 0:
        print("   ⚠️  Missing values found:")
        for col, count in missing[missing > 0].items():
            print(f"      - {col}: {count} missing")
    else:
        print("   ✓ No missing values in critical columns")
    
    # Check data ranges
    print(f"\n   📊 Data Ranges:")
    print(f"      Income: ${df['income'].min():.2f} to ${df['income'].max():.2f}")
    print(f"      Expenses: ${df['expenses'].min():.2f} to ${df['expenses'].max():.2f}")
    print(f"      Savings: ${df['savings'].min():.2f} to ${df['savings'].max():.2f}")
    print(f"      EMI: ${df['emi'].min():.2f} to ${df['emi'].max():.2f}")
    
    # Check loan distribution
    loan_count = df['has_loan'].sum()
    print(f"\n   💰 Loan Distribution:")
    print(f"      Records with loans: {loan_count:,} ({loan_count/len(df)*100:.1f}%)")
    print(f"      Records without loans: {len(df)-loan_count:,} ({(len(df)-loan_count)/len(df)*100:.1f}%)")
    
    return True

def save_combined_dataset(df, filename='data/combined_dataset.csv'):
    """Save the combined dataset"""
    print(f"\n💾 Saving combined dataset to {filename}...")
    df.to_csv(filename, index=False)
    print(f"   ✓ Saved {len(df):,} records")
    print(f"   ✓ File size: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

def main():
    """Main integration process"""
    print("="*70)
    print("DATASET INTEGRATION PROCESS")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Load datasets
        df1 = load_dataset_1()
        df2 = load_dataset_2()
        
        # Extract data
        df1_loans = extract_loan_data_from_dataset1(df1)
        df1_financial = extract_financial_data_from_dataset1(df1)
        df2_financial = extract_financial_data_from_dataset2(df2)
        
        # Combine
        combined = combine_datasets(df1_financial, df2_financial, df1_loans)
        
        # Validate
        validate_combined_data(combined)
        
        # Save
        save_combined_dataset(combined)
        
        print("\n" + "="*70)
        print("✅ INTEGRATION COMPLETE!")
        print("="*70)
        print(f"\nNext Steps:")
        print("1. Review combined_dataset.csv")
        print("2. Proceed to ML model training")
        print("3. Implement backend services")
        
    except Exception as e:
        print(f"\n❌ Error during integration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
