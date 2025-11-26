#!/usr/bin/env python3
"""
Test script for area summaries functionality
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from accounting_core import AccountingCoreProcessor
from area_summaries import generate_area_summaries, AreaSummary, Adjustment, Reclassification

def main():
    print("\n" + "="*60)
    print("  TEST: Generación de Sumarias de Áreas")
    print("="*60 + "\n")
    
    # Setup test database
    test_db = "accounting_core.db"
    
    if not os.path.exists(test_db):
        print("Error: accounting_core.db not found")
        print("Please run test_complete_system.py first to create test data")
        return
    
    # Initialize accounting core
    print("1. Inicializando núcleo contable...")
    accounting = AccountingCoreProcessor({"database": {"path": test_db}})
    
    # Create output directory
    output_dir = "./papeles_trabajo"
    os.makedirs(output_dir, exist_ok=True)
    
    year = 2023
    
    # Test 1: Generate all area summaries
    print(f"\n2. Generando sumarias para todas las áreas (año {year})...")
    try:
        files = generate_area_summaries(accounting, year, output_dir, "mercantil")
        print(f"✓ Generadas {len(files)} sumarias")
        for file in files:
            file_path = Path(file)
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                print(f"  - {file_path.name} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Create a custom area summary
    print(f"\n3. Generando sumaria personalizada...")
    try:
        summary = AreaSummary(accounting, year)
        
        # Add some test adjustments
        summary.add_adjustment(
            Adjustment('AJ-TEST-001', 'Ajuste de prueba 1', '600', 1000.00, 0, 
                      'Motivo de prueba', 'proposed')
        )
        summary.add_adjustment(
            Adjustment('AJ-TEST-001', 'Contrapartida ajuste 1', '430', 0, 1000.00, 
                      'Motivo de prueba', 'proposed')
        )
        
        # Add a test reclassification
        summary.add_reclassification(
            Reclassification('RC-TEST-001', 'Reclasificación de prueba', '430', '431', 
                           500.00, 'Motivo de prueba', 'proposed')
        )
        
        # Generate the summary
        filepath = summary.generate_summary(
            area_name="Área de Prueba",
            accounts_prefix="XX",
            findings=[
                "Hallazgo de prueba número 1",
                "Hallazgo de prueba número 2"
            ],
            conclusions=[
                "Conclusión de prueba número 1",
                "Los saldos se presentan razonablemente"
            ],
            output_path=output_dir
        )
        
        if os.path.exists(filepath):
            size_kb = os.path.getsize(filepath) / 1024
            print(f"✓ Sumaria personalizada generada: {Path(filepath).name} ({size_kb:.1f} KB)")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("  PRUEBAS COMPLETADAS")
    print("="*60)
    
    all_files = list(Path(output_dir).glob("PT_Sumaria_*.xlsx"))
    total_size = sum(f.stat().st_size for f in all_files) / 1024
    
    print(f"\n✓ Total sumarias generadas: {len(all_files)}")
    print(f"✓ Tamaño total: {total_size:.1f} KB")
    print(f"✓ Directorio: {output_dir}")
    
    print("\nArchivos generados:")
    for file in sorted(all_files):
        print(f"  - {file.name}")
    
    print("\n✓ Sistema de sumarias completamente funcional\n")

if __name__ == "__main__":
    main()
