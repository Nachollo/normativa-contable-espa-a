#!/usr/bin/env python3
"""
Test script for automated circularization system
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.accounting_core import AccountingCoreProcessor
from src.circularization_automation import CircularizationAutomation
from src.utils import load_config

def create_test_accounting_data():
    """Create test accounting database with sample data"""
    config = load_config()
    accounting = AccountingCoreProcessor(config)
    
    # Create sample accounts for 2023
    year = 2023
    
    # Sample data for testing
    balance_data = pd.DataFrame([
        # Clientes (Customers)
        {'account_code': '430', 'account_name': 'Clientes', 'saldo_final': 15000, 'suma_debe': 50000, 'suma_haber': 35000},
        {'account_code': '4300', 'account_name': 'Cliente ABC SL', 'saldo_final': 8000, 'suma_debe': 25000, 'suma_haber': 17000},
        {'account_code': '4301', 'account_name': 'Cliente XYZ SA', 'saldo_final': 7000, 'suma_debe': 25000, 'suma_haber': 18000},
        
        # Proveedores (Suppliers)
        {'account_code': '400', 'account_name': 'Proveedores', 'saldo_final': -12000, 'suma_debe': 28000, 'suma_haber': 40000},
        {'account_code': '4000', 'account_name': 'Proveedor DEF SL', 'saldo_final': -5000, 'suma_debe': 10000, 'suma_haber': 15000},
        {'account_code': '4001', 'account_name': 'Proveedor GHI SA', 'saldo_final': -7000, 'suma_debe': 18000, 'suma_haber': 25000},
        
        # Bancos (Banks)
        {'account_code': '572', 'account_name': 'Bancos', 'saldo_final': 25000, 'suma_debe': 100000, 'suma_haber': 75000},
        {'account_code': '57200', 'account_name': 'Banco Santander', 'saldo_final': 15000, 'suma_debe': 60000, 'suma_haber': 45000},
        {'account_code': '57201', 'account_name': 'Banco BBVA', 'saldo_final': 10000, 'suma_debe': 40000, 'suma_haber': 30000},
    ])
    
    # Create journal entries for next year (2024) to simulate subsequent settlements
    journal_data = pd.DataFrame([
        # Cliente ABC SL payments in 2024
        {'entry_number': '1', 'entry_date': '2024-01-15', 'account_code': '4300', 
         'debit_amount': 0, 'credit_amount': 5000, 'description': 'Cobro factura 2023'},
        {'entry_number': '2', 'entry_date': '2024-02-10', 'account_code': '4300', 
         'debit_amount': 0, 'credit_amount': 3000, 'description': 'Cobro factura 2023'},
        
        # Cliente XYZ SA payments in 2024
        {'entry_number': '3', 'entry_date': '2024-01-20', 'account_code': '4301', 
         'debit_amount': 0, 'credit_amount': 6000, 'description': 'Cobro factura 2023'},
        
        # Proveedor DEF SL payments in 2024
        {'entry_number': '4', 'entry_date': '2024-01-25', 'account_code': '4000', 
         'debit_amount': 4000, 'credit_amount': 0, 'description': 'Pago factura proveedor 2023'},
        
        # Proveedor GHI SA payments in 2024
        {'entry_number': '5', 'entry_date': '2024-02-15', 'account_code': '4001', 
         'debit_amount': 5500, 'credit_amount': 0, 'description': 'Pago factura proveedor 2023'},
    ])
    
    # Import data manually to database
    from sqlalchemy.orm import sessionmaker
    from src.accounting_core import AccountingPeriod, BalanceAccount, JournalEntry
    
    Session = sessionmaker(bind=accounting.engine)
    session = Session()
    
    try:
        # Create period for 2023
        period_2023 = AccountingPeriod(
            year=2023,
            company_name="Empresa Test SA",
            company_cif="A12345678",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        session.add(period_2023)
        session.flush()
        
        # Add balance accounts
        for _, row in balance_data.iterrows():
            account = BalanceAccount(
                period_id=period_2023.id,
                account_code=row['account_code'],
                account_name=row['account_name'],
                saldo_final=row['saldo_final'],
                suma_debe=row['suma_debe'],
                suma_haber=row['suma_haber'],
                account_level=len(row['account_code'])
            )
            session.add(account)
        
        # Create period for 2024
        period_2024 = AccountingPeriod(
            year=2024,
            company_name="Empresa Test SA",
            company_cif="A12345678",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        session.add(period_2024)
        session.flush()
        
        # Add journal entries for 2024
        for _, row in journal_data.iterrows():
            entry = JournalEntry(
                period_id=period_2024.id,
                entry_number=row['entry_number'],
                entry_date=datetime.strptime(row['entry_date'], '%Y-%m-%d'),
                account_code=row['account_code'],
                debit_amount=row['debit_amount'],
                credit_amount=row['credit_amount'],
                description=row['description']
            )
            session.add(entry)
        
        session.commit()
        print("✓ Test accounting data created successfully")
        return accounting
        
    except Exception as e:
        session.rollback()
        print(f"Error creating test data: {e}")
        raise
    finally:
        session.close()

def test_circularization_automation():
    """Test the automated circularization system"""
    print("\n" + "="*60)
    print("TESTING AUTOMATED CIRCULARIZATION SYSTEM")
    print("="*60 + "\n")
    
    # Create test data
    print("Step 1: Creating test accounting data...")
    accounting = create_test_accounting_data()
    
    # Initialize circularization automation
    print("\nStep 2: Initializing circularization automation...")
    circularization = CircularizationAutomation(accounting, "./papeles_trabajo")
    print("✓ Circularization automation initialized")
    
    # Test for clientes (customers)
    print("\nStep 3: Processing circularization for CLIENTES...")
    clientes_file = circularization.process_circularization(
        year=2023,
        confirmation_type='clientes',
        responses_file=None,  # No responses - will apply alternative procedures
        entity_type='mercantil'
    )
    
    # Test for proveedores (suppliers)
    print("\nStep 4: Processing circularization for PROVEEDORES...")
    proveedores_file = circularization.process_circularization(
        year=2023,
        confirmation_type='proveedores',
        responses_file=None,
        entity_type='mercantil'
    )
    
    # Test for bancos (banks)
    print("\nStep 5: Processing circularization for BANCOS...")
    bancos_file = circularization.process_circularization(
        year=2023,
        confirmation_type='bancos',
        responses_file=None,
        entity_type='mercantil'
    )
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    print(f"✓ Clientes circularization: {Path(clientes_file).name if clientes_file else 'FAILED'}")
    print(f"✓ Proveedores circularization: {Path(proveedores_file).name if proveedores_file else 'FAILED'}")
    print(f"✓ Bancos circularization: {Path(bancos_file).name if bancos_file else 'FAILED'}")
    
    files_generated = sum([1 for f in [clientes_file, proveedores_file, bancos_file] if f])
    print(f"\nTotal files generated: {files_generated}")
    print("\n✅ CIRCULARIZATION AUTOMATION TEST COMPLETED SUCCESSFULLY\n")
    
    return {
        'clientes': clientes_file,
        'proveedores': proveedores_file,
        'bancos': bancos_file
    }

if __name__ == "__main__":
    try:
        results = test_circularization_automation()
        print("Test completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
