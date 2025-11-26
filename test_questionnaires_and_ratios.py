#!/usr/bin/env python3
"""
Test questionnaires and analytical review modules
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.accounting_core import AccountingCoreProcessor, AccountingPeriod, BalanceAccount, JournalEntry
from src.questionnaires import AuditQuestionnaires
from src.analytical_review import AnalyticalReview

def test_questionnaires_and_ratios():
    """Test the new questionnaires and analytical review modules"""
    
    print("\n" + "="*60)
    print("  TEST: CUESTIONARIOS Y REVISIÓN ANALÍTICA")
    print("="*60 + "\n")
    
    # Load config
    with open('config.json') as f:
        config = json.load(f)
    
    # Initialize accounting core
    print("1. Inicializando núcleo contable...")
    accounting = AccountingCoreProcessor(config)
    
    # Check if we have data, if not create test data
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=accounting.engine)
    session = Session()
    
    period = session.query(AccountingPeriod).filter_by(year=2023).first()
    
    if not period:
        print("   Creando datos de prueba...")
        # Create test period
        period = AccountingPeriod(
            year=2023,
            company_name='Empresa Test SA',
            cif='A12345678',
            start_date='2023-01-01',
            end_date='2023-12-31'
        )
        session.add(period)
        session.commit()
        
        # Add test accounts
        accounts_data = [
            ('100', 'Capital Social', 0, 0, 100000, 0, -100000),
            ('210', 'Inmovilizado Material', 50000, 5000, 0, 45000, 45000),
            ('300', 'Existencias', 15000, 8000, 0, 7000, 7000),
            ('430', 'Clientes', 25000, 10000, 0, 15000, 15000),
            ('572', 'Bancos', 30000, 15000, 0, 15000, 15000),
            ('400', 'Proveedores', 0, 15000, 20000, 0, -20000),
            ('700', 'Ventas', 0, 0, 150000, 0, -150000),
            ('600', 'Compras', 80000, 0, 0, 80000, 80000),
        ]
        
        for code, name, debe, haber, deudor, acreedor, final in accounts_data:
            acc = BalanceAccount(
                period_id=period.id,
                account_code=code,
                account_name=name,
                sumas_debe=debe,
                sumas_haber=haber,
                saldo_deudor=deudor,
                saldo_acreedor=acreedor,
                saldo_final=final
            )
            session.add(acc)
        
        session.commit()
        
        # Add journal entries
        import random
        from datetime import datetime
        
        for i in range(30):
            date = datetime(2023, random.randint(1, 12), random.randint(1, 28))
            amount = random.uniform(1000, 5000)
            
            entry = JournalEntry(
                period_id=period.id,
                entry_number=i+1,
                entry_date=date.strftime('%Y-%m-%d'),
                account_code='600',
                debit_amount=amount,
                credit_amount=0,
                description=f'Compra mercancías {i+1}',
                document_reference=f'FC-{i+1:04d}'
            )
            session.add(entry)
        
        for i in range(30):
            date = datetime(2023, random.randint(1, 12), random.randint(1, 28))
            amount = random.uniform(2000, 7000)
            
            entry = JournalEntry(
                period_id=period.id,
                entry_number=30+i+1,
                entry_date=date.strftime('%Y-%m-%d'),
                account_code='700',
                debit_amount=0,
                credit_amount=amount,
                description=f'Venta {i+1}',
                document_reference=f'FV-{i+1:04d}'
            )
            session.add(entry)
        
        session.commit()
        print(f"   ✓ Datos creados: 8 cuentas, 60 asientos")
    else:
        print(f"   ✓ Usando datos existentes del ejercicio 2023")
    
    session.close()
    
    # Test Questionnaires
    print("\n2. Probando Cuestionarios de Auditoría...")
    questionnaires = AuditQuestionnaires(accounting, config['working_papers']['output_dir'])
    
    # Generate a sample questionnaire with responses
    print("   Generando cuestionario de riesgo general...")
    sample_responses = {
        0: False,  # Not first audit
        1: False,  # No significant changes
        2: False,  # No continuity problems
        3: True,   # Yes, pressure on results
        4: True,   # Yes, related party transactions
        5: False,  # Not highly regulated
        6: False,  # No high volatility
        7: False,  # Not complex systems
        8: False,  # No recent changes
    }
    
    file1 = questionnaires.generate_questionnaire_workpaper(2023, 'general_risk', sample_responses)
    print(f"   ✓ Generado: {Path(file1).name}")
    
    # Generate internal control questionnaire
    print("   Generando cuestionario de control interno...")
    file2 = questionnaires.generate_questionnaire_workpaper(2023, 'internal_control')
    print(f"   ✓ Generado: {Path(file2).name}")
    
    # Generate area-specific questionnaire
    print("   Generando cuestionario de inmovilizado...")
    file3 = questionnaires.generate_questionnaire_workpaper(2023, 'inmovilizado')
    print(f"   ✓ Generado: {Path(file3).name}")
    
    # Test Analytical Review
    print("\n3. Probando Revisión Analítica y Ratios Financieros...")
    analytical = AnalyticalReview(accounting, config['working_papers']['output_dir'])
    
    # Calculate ratios
    print("   Calculando ratios financieros...")
    ratios = analytical.calculate_financial_ratios(2023)
    
    if ratios and '_values' in ratios:
        print(f"\n   Ratios calculados:")
        print(f"     • Ratio de Liquidez: {ratios.get('ratio_liquidez', 0):.2f}")
        print(f"     • Ratio de Endeudamiento: {ratios.get('ratio_endeudamiento', 0):.2%}")
        print(f"     • ROE (Return on Equity): {ratios.get('roe', 0):.2%}")
        print(f"     • Margen Neto: {ratios.get('margen_neto', 0):.2%}")
        print(f"     • Periodo Medio de Cobro: {ratios.get('periodo_medio_cobro', 0):.0f} días")
    
    # Generate comprehensive analytical review
    print("\n   Generando papel de trabajo de revisión analítica...")
    file4 = analytical.generate_analytical_review_workpaper(2023, 'comercio', [2023])
    print(f"   ✓ Generado: {Path(file4).name}")
    
    # Summary
    print("\n" + "="*60)
    print("  RESUMEN DE PRUEBAS")
    print("="*60)
    print(f"\n✓ Cuestionarios generados: 3")
    print(f"   - {Path(file1).name}")
    print(f"   - {Path(file2).name}")
    print(f"   - {Path(file3).name}")
    print(f"\n✓ Revisión analítica: 1")
    print(f"   - {Path(file4).name}")
    print(f"\n✓ Total archivos generados: 4")
    
    # Check file sizes
    total_size = sum([
        Path(file1).stat().st_size,
        Path(file2).stat().st_size,
        Path(file3).stat().st_size,
        Path(file4).stat().st_size
    ]) / 1024  # KB
    
    print(f"✓ Tamaño total: {total_size:.1f} KB")
    print(f"\n{'='*60}\n")
    print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print(f"\n{'='*60}\n")
    
    return {
        'questionnaires': [file1, file2, file3],
        'analytical_review': file4,
        'total_files': 4,
        'total_size_kb': total_size
    }


if __name__ == '__main__':
    test_questionnaires_and_ratios()
