"""
Dataset Exploration Script
Analyzes Dataset 1 and Dataset 2 to understand structure and prepare for integration
"""

import pandas as pd
import numpy as np

def explore_dataset_1():
    """Explore Dataset 1 (Global Personal Finance)"""
    print("="*70)
    print("DATASET 1: Global Personal Finance (32,424 records)")
    print("="*70)
    
    try:
        df = pd.read_csv('data/personal_finance_global.csv')
        
        print(f"\n📊 Shape: {df.shape}")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        
        print("\n📋 Columns:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        print("\n🔍 Sample Data (first 3 rows):")
        print(df.head(3).to_string())
        
        print("\n📈 Loan-Related Columns:")
        loan_cols = [col for col in df.columns if 'loan' in col.lower() or 'emi' in col.lower()]
        for col in loan_cols:
            print(f"   - {col}: {df[col].dtype}")
            if df[col].dtype in ['int64', 'float64']:
                print(f"     Range: {df[col].min()} to {df[col].max()}")
                print(f"     Mean: {df[col].mean():.2f}")
        
        print("\n✅ Dataset 1 loaded successfully!")
        return df
        
    except FileNotFoundError:
        print("\n❌ Dataset 1 not found!")
        print("   Please download from Kaggle and save to: data/personal_finance_global.csv")
        return None

def explore_dataset_2():
    """Explore Dataset 2 (India Personal Finance)"""
    print("\n" + "="*70)
    print("DATASET 2: India Personal Finance (20,000 records)")
    print("="*70)
    
    try:
        # Try both possible filenames
        try:
            df = pd.read_csv('data/india_personal_finance.csv')
        except FileNotFoundError:
            df = pd.read_csv('data/indian_personal_finance.csv')
        
        print(f"\n📊 Shape: {df.shape}")
        print(f"   Rows: {df.shape[0]:,}")
        print(f"   Columns: {df.shape[1]}")
        
        print("\n📋 Columns:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        print("\n🔍 Sample Data (first 3 rows):")
        print(df.head(3).to_string())
        
        print("\n📈 Financial Columns:")
        financial_cols = ['Income', 'Rent', 'Groceries', 'Transport', 'Eating_Out', 
                         'Entertainment', 'Loan_Repayment', 'Disposable_Income']
        for col in financial_cols:
            if col in df.columns:
                print(f"   - {col}: {df[col].dtype}")
                if df[col].dtype in ['int64', 'float64']:
                    print(f"     Range: {df[col].min()} to {df[col].max()}")
                    print(f"     Mean: {df[col].mean():.2f}")
        
        print("\n✅ Dataset 2 loaded successfully!")
        return df
        
    except FileNotFoundError:
        print("\n❌ Dataset 2 not found!")
        print("   Please download from Kaggle and save to: data/india_personal_finance.csv")
        return None

def compare_datasets(df1, df2):
    """Compare both datasets"""
    if df1 is None or df2 is None:
        return
    
    print("\n" + "="*70)
    print("DATASET COMPARISON")
    print("="*70)
    
    print(f"\n📊 Size Comparison:")
    print(f"   Dataset 1: {df1.shape[0]:,} rows")
    print(f"   Dataset 2: {df2.shape[0]:,} rows")
    print(f"   Combined: {df1.shape[0] + df2.shape[0]:,} rows")
    
    print(f"\n📋 Column Comparison:")
    print(f"   Dataset 1: {df1.shape[1]} columns")
    print(f"   Dataset 2: {df2.shape[1]} columns")
    
    print("\n🔗 Integration Strategy:")
    print("   1. Dataset 1: Extract loan data (type, amount, tenure, interest, payments)")
    print("   2. Dataset 2: Extract financial data (income, expenses, savings)")
    print("   3. Combine: 52,424 total records with complete data")

if __name__ == '__main__':
    print("\n🚀 Starting Dataset Exploration...\n")
    
    df1 = explore_dataset_1()
    df2 = explore_dataset_2()
    compare_datasets(df1, df2)
    
    print("\n" + "="*70)
    print("✅ Exploration Complete!")
    print("="*70)
    print("\nNext Steps:")
    print("1. If datasets are missing, download them from Kaggle")
    print("2. Run this script again to verify")
    print("3. Proceed to data integration script")
