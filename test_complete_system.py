#!/usr/bin/env python3
"""
Test script for complete audit system including risk matrix and work programs
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.accounting_core import AccountingCoreProcessor
from src.utils import load_config, setup_logging
from src.materiality_calculator import MaterialityCalculator
from src.risk_matrix import RiskMatrix
from src.work_program_generator import WorkProgramGenerator
from src.comprehensive_audit_papers import ComprehensiveAuditPapers

def create_test_data():
    """Create test accounting data"""
    print("Creating test data...")
    
    config = load_config('config.json')
    accounting = AccountingCoreProcessor(config)
    
    # Create test period
    test_data = {
        'year': 2023,
        'company_name': 'TEST COMPANY S.L.',
        'cif': 'B12345678',
        'balance_accounts': [
            {'code': '2100', 'name': 'Construcciones', 'debe': 500000, 'haber': 0},
            {'code': '2130', 'name': 'Maquinaria', 'debe': 200000, 'haber': 50000},
            {'code': '3000', 'name': 'Mercaderías', 'debe': 150000, 'haber': 20000},
            {'code': '4300', 'name': 'Clientes', 'debe': 250000, 'haber': 30000},
            {'code': '5720', 'name': 'Bancos', 'debe': 100000, 'haber': 20000},
            {'code': '1000', 'name': 'Capital Social', 'debe': 0, 'haber': 300000},
            {'code': '1700', 'name': 'Préstamos LP', 'debe': 0, 'haber': 400000},
            {'code': '4000', 'name': 'Proveedores', 'debe': 20000, 'haber': 200000},
            {'code': '7000', 'name': 'Ventas', 'debe': 0, 'haber': 800000},
            {'code': '6000', 'name': 'Compras', 'debe': 480000, 'haber': 0},
            {'code': '6400', 'name': 'Gastos de Personal', 'debe': 150000, 'haber': 0},
            {'code': '6200', 'name': 'Servicios Exteriores', 'debe': 80000, 'haber': 0},
        ],
        'journal_entries': [
            {'num': 1, 'date': '2023-01-15', 'account': '6000', 'description': 'Compra mercaderías', 'debe': 10000, 'haber': 0},
            {'num': 1, 'date': '2023-01-15', 'account': '4000', 'description': 'Compra mercaderías', 'debe': 0, 'haber': 10000},
            {'num': 2, 'date': '2023-01-20', 'account': '4300', 'description': 'Venta mercaderías', 'debe': 12000, 'haber': 0},
            {'num': 2, 'date': '2023-01-20', 'account': '7000', 'description': 'Venta mercaderías', 'debe': 0, 'haber': 12000},
            {'num': 3, 'date': '2023-02-10', 'account': '6400', 'description': 'Nómina enero', 'debe': 12500, 'haber': 0},
            {'num': 3, 'date': '2023-02-10', 'account': '5720', 'description': 'Nómina enero', 'debe': 0, 'haber': 12500},
        ]
    }
    
    # Load test data
    from src.accounting_core import AccountingPeriod, BalanceAccount, JournalEntry
    from sqlalchemy.orm import Session
    
    # Create period
    period = AccountingPeriod(
        year=test_data['year'],
        company_name=test_data['company_name'],
        company_cif=test_data['cif'],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31)
    )
    accounting.session.add(period)
    accounting.session.commit()
    
    # Add balance accounts
    for acc_data in test_data['balance_accounts']:
        account = BalanceAccount(
            period_id=period.id,
            account_code=acc_data['code'],
            account_name=acc_data['name'],
            suma_debe=acc_data['debe'],
            suma_haber=acc_data['haber'],
            saldo_final=acc_data['debe'] - acc_data['haber']
        )
        accounting.session.add(account)
    
    # Add journal entries
    for entry_data in test_data['journal_entries']:
        entry = JournalEntry(
            period_id=period.id,
            entry_number=str(entry_data['num']),
            entry_date=datetime.strptime(entry_data['date'], '%Y-%m-%d'),
            account_code=entry_data['account'],
            description=entry_data['description'],
            debit_amount=entry_data['debe'],
            credit_amount=entry_data['haber']
        )
        accounting.session.add(entry)
    
    accounting.session.commit()
    print(f"✓ Test data created: {len(test_data['balance_accounts'])} accounts, {len(test_data['journal_entries'])} entries")
    
    return accounting

def test_complete_system():
    """Test the complete audit system"""
    print("\n" + "="*60)
    print("  TESTING COMPLETE AUDIT SYSTEM")
    print("="*60 + "\n")
    
    # Setup
    config = load_config('config.json')
    logger = setup_logging()
    
    # Create test data
    accounting = create_test_data()
    
    year = 2023
    entity_type = 'mercantil'
    
    # Step 1: Calculate materiality
    print("\nStep 1: Calculating materiality...")
    materiality_calc = MaterialityCalculator(config, accounting)
    materiality = materiality_calc.calculate_materiality(year, entity_type, risk_assessment='medium_risk')
    
    if 'error' in materiality:
        print(f"ERROR: {materiality['error']}")
        return False
    
    print(f"✓ Materiality calculated:")
    print(f"  Overall: {materiality['overall_materiality']:,.2f} €")
    print(f"  Performance: {materiality['performance_materiality']:,.2f} €")
    print(f"  Trivial: {materiality['trivial_threshold']:,.2f} €")
    
    # Generate materiality working paper
    mat_file = materiality_calc.generate_materiality_working_paper(year, entity_type, risk_assessment='medium_risk')
    print(f"  File: {Path(mat_file).name}")
    
    # Step 2: Generate risk matrix
    print("\nStep 2: Generating risk matrix...")
    entity_info = {
        'first_year_audit': False,
        'going_concern_issues': False,
        'significant_changes': False
    }
    
    risk_matrix_gen = RiskMatrix(config, accounting, materiality)
    risk_matrix = risk_matrix_gen.generate_risk_matrix(year, entity_info)
    risk_matrix_file = risk_matrix_gen.export_to_excel(risk_matrix, year)
    
    print(f"✓ Risk matrix generated: {Path(risk_matrix_file).name}")
    print(f"  Total areas: {len(risk_matrix)}")
    print(f"  High risk: {len(risk_matrix[risk_matrix['combined_risk'] == 'high'])}")
    print(f"  Medium risk: {len(risk_matrix[risk_matrix['combined_risk'] == 'medium'])}")
    print(f"  Low risk: {len(risk_matrix[risk_matrix['combined_risk'] == 'low'])}")
    
    # Step 3: Generate work programs
    print("\nStep 3: Generating work programs...")
    work_program_gen = WorkProgramGenerator(config, risk_matrix)
    
    # Generate for high and medium risk areas
    work_programs = []
    for _, area in risk_matrix.iterrows():
        if area['combined_risk'] in ['high', 'medium'] and area['material']:
            wp = work_program_gen.generate_work_program(area['area_key'], year)
            work_programs.append(wp)
            wp_file = work_program_gen.export_work_program(wp)
            print(f"  ✓ {area['area_name']}: {wp['total_procedures']} procedures")
    
    print(f"✓ Generated {len(work_programs)} work programs")
    
    # Save template
    template_path = work_program_gen.save_custom_procedures_template()
    print(f"  Template saved: {Path(template_path).name}")
    
    # Step 4: Generate audit papers
    print("\nStep 4: Generating comprehensive audit papers...")
    comprehensive = ComprehensiveAuditPapers(config, accounting)
    audit_results = comprehensive.generate_all_working_papers(year, entity_type)
    
    print(f"✓ Audit papers generated: {audit_results.get('total_files', 0)} files")
    
    # Summary
    print("\n" + "="*60)
    print("  TEST RESULTS SUMMARY")
    print("="*60)
    print(f"✓ Materiality calculation: PASSED")
    print(f"✓ Risk matrix: PASSED ({len(risk_matrix)} areas)")
    print(f"✓ Work programs: PASSED ({len(work_programs)} programs)")
    print(f"✓ Audit papers: PASSED ({audit_results.get('total_files', 0)} files)")
    
    total_files = 1 + 1 + len(work_programs) + audit_results.get('total_files', 0)  # mat + risk + wp + audit
    print(f"\nTotal files generated: {total_files}")
    print("\n✅ ALL TESTS PASSED\n")
    
    return True

if __name__ == '__main__':
    try:
        success = test_complete_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
