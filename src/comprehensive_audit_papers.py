"""
Comprehensive Audit Working Papers Generator
Generates all required audit working papers for Spanish audits
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from src.materiality_calculator import MaterialityCalculator
from src.statistical_sampling import StatisticalSamplingGenerator

try:
    from src.accounting_core import AccountingPeriod, BalanceAccount, JournalEntry
except ImportError:
    AccountingPeriod = None
    BalanceAccount = None
    JournalEntry = None


class ComprehensiveAuditPapers:
    """Generates comprehensive audit working papers"""
    
    def __init__(self, config: Dict, accounting_processor):
        self.config = config
        self.accounting = accounting_processor
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(config.get('working_papers', {}).get('output_dir', './papeles_trabajo'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize sub-modules
        self.materiality_calc = MaterialityCalculator(config, accounting_processor)
        self.sampling_gen = StatisticalSamplingGenerator(config, accounting_processor)
        
        # Define audit areas with account mappings
        self.audit_areas = {
            'inmovilizado': {
                'name': 'Inmovilizado Material e Intangible',
                'accounts': ['20', '21', '22', '23', '28'],
                'columns': ['Cuenta', 'Descripción', 'Saldo Inicial', 'Altas', 'Bajas', 'Saldo Final', 'Amortización', 'Valor Neto']
            },
            'tesoreria': {
                'name': 'Tesorería y Bancos',
                'accounts': ['57'],
                'columns': ['Cuenta', 'Entidad', 'Saldo Contable', 'Saldo Bancario', 'Conciliado', 'Diferencia']
            },
            'pasivos_financieros': {
                'name': 'Pasivos Financieros',
                'accounts': ['16', '17', '52'],
                'columns': ['Cuenta', 'Acreedor', 'Saldo Inicial', 'Incrementos', 'Pagos', 'Saldo Final', 'C/P', 'L/P']
            },
            'existencias': {
                'name': 'Existencias',
                'accounts': ['30', '31', '32', '33', '34', '35', '36'],
                'columns': ['Cuenta', 'Tipo', 'Saldo Contable', 'Inventario Físico', 'Diferencia', 'Ajuste']
            },
            'gastos_personal': {
                'name': 'Gastos de Personal',
                'accounts': ['64'],
                'columns': ['Cuenta', 'Concepto', 'Importe', 'Media Mensual', '% s/Total']
            },
            'servicios_exteriores': {
                'name': 'Servicios Exteriores',
                'accounts': ['62'],
                'columns': ['Cuenta', 'Concepto', 'Importe', 'Variación']
            },
            'resultados_excepcionales': {
                'name': 'Resultados Excepcionales',
                'accounts': ['67', '77'],
                'columns': ['Cuenta', 'Concepto', 'Naturaleza', 'Importe', 'Recurrente']
            },
            'impuestos': {
                'name': 'Impuestos',
                'accounts': ['47', '62'],  # Deuda tributaria y gastos
                'columns': ['Concepto', 'Base Imponible', 'Tipo', 'Cuota', 'Pagado', 'Pendiente']
            }
        }
    
    def generate_all_working_papers(self, year: int, entity_type: str = 'mercantil') -> Dict[str, Any]:
        """Generate all audit working papers for a year"""
        self.logger.info(f"Generating all audit working papers for year {year}")
        
        generated_files = []
        results = {'year': year, 'entity_type': entity_type, 'files': []}
        
        try:
            # 1. Materialidad
            mat_file = self.materiality_calc.generate_materiality_working_paper(year, entity_type)
            if mat_file:
                generated_files.append(('Materialidad', mat_file))
            
            # 2. Muestreo de compras y ventas
            purchases_sample = self.sampling_gen.generate_purchases_sample(year, 25, 'systematic')
            sales_sample = self.sampling_gen.generate_sales_sample(year, 25, 'systematic')
            
            if 'error' not in purchases_sample and 'error' not in sales_sample:
                sampling_file = self.sampling_gen.generate_sampling_working_paper(purchases_sample, sales_sample)
                generated_files.append(('Muestreo Compras/Ventas', sampling_file))
            
            # 3-11. Papeles de trabajo por área
            for area_key, area_config in self.audit_areas.items():
                area_file = self._generate_area_working_paper(year, area_key, area_config)
                if area_file:
                    generated_files.append((area_config['name'], area_file))
            
            # 12. Circularización
            circ_file = self._generate_circularization_paper(year)
            if circ_file:
                generated_files.append(('Circularización', circ_file))
            
            # 13. Partes vinculadas
            related_file = self._generate_related_parties_paper(year)
            if related_file:
                generated_files.append(('Partes Vinculadas', related_file))
            
            results['files'] = generated_files
            results['count'] = len(generated_files)
            
            self.logger.info(f"Generated {len(generated_files)} working papers")
            
        except Exception as e:
            self.logger.error(f"Error generating working papers: {e}", exc_info=True)
            results['error'] = str(e)
        
        return results
    
    def _generate_area_working_paper(self, year: int, area_key: str, area_config: Dict) -> Optional[Path]:
        """Generate working paper for a specific audit area"""
        try:
            period = self.accounting.session.query(AccountingPeriod).filter_by(year=year).first()
            
            if not period:
                return None
            
            wb = Workbook()
            ws = wb.active
            ws.title = area_config['name'][:31]  # Excel limit
            
            # Header
            ws['A1'] = f"PAPEL DE TRABAJO - {area_config['name'].upper()}"
            ws['A1'].font = Font(size=14, bold=True)
            ws.merge_cells('A1:H1')
            
            ws['A3'] = 'Ejercicio:'
            ws['B3'] = year
            
            # Column headers
            headers = area_config['columns']
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(5, col, header)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.alignment = Alignment(horizontal='center', wrap_text=True)
            
            # Get accounts for this area
            row = 6
            for account_prefix in area_config['accounts']:
                accounts = self.accounting.session.query(BalanceAccount).filter_by(period_id=period.id).filter(
                    BalanceAccount.account_code.like(f'{account_prefix}%'),
                    BalanceAccount.account_level >= 4
                ).order_by(BalanceAccount.account_code).all()
                
                for acc in accounts:
                    ws.cell(row, 1, acc.account_code)
                    ws.cell(row, 2, acc.account_name[:40])
                    ws.cell(row, 3, abs(acc.saldo_final)).number_format = '#,##0.00'
                    
                    # Fill remaining columns with placeholders
                    for col in range(4, len(headers) + 1):
                        ws.cell(row, col, 0).number_format = '#,##0.00' if col <= 8 else ''
                    
                    row += 1
            
            # Adjust columns
            for i in range(1, len(headers) + 1):
                ws.column_dimensions[get_column_letter(i)].width = 20 if i <= 2 else 15
            
            # Save
            filename = f"PT_{area_key.title()}_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            output_path = self.output_dir / filename
            wb.save(output_path)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating {area_key} paper: {e}")
            return None
    
    def _generate_circularization_paper(self, year: int) -> Optional[Path]:
        """Generate circularization working paper"""
        try:
            wb = Workbook()
            
            for entity_type, prefix in [('Clientes', '43'), ('Proveedores', '40'), ('Bancos', '57')]:
                ws = wb.create_sheet(entity_type)
                
                ws['A1'] = f'CIRCULARIZACIÓN - {entity_type.upper()}'
                ws['A1'].font = Font(size=12, bold=True)
                
                headers = ['Código', 'Nombre', 'Saldo Contable', 'Fecha Envío', 'Respuesta', 'Saldo Confirmado', 'Diferencia']
                for col, header in enumerate(headers, start=1):
                    ws.cell(3, col, header).font = Font(bold=True)
                
                # Get accounts
                period = self.accounting.session.query(AccountingPeriod).filter_by(year=year).first()
                
                if period:
                    accounts = self.accounting.session.query(BalanceAccount).filter_by(period_id=period.id).filter(
                        BalanceAccount.account_code.like(f'{prefix}%')
                    ).limit(50).all()
                    
                    for i, acc in enumerate(accounts, start=4):
                        ws.cell(i, 1, acc.account_code)
                        ws.cell(i, 2, acc.account_name)
                        ws.cell(i, 3, abs(acc.saldo_final)).number_format = '#,##0.00'
            
            if 'Sheet' in wb.sheetnames:
                wb.remove(wb['Sheet'])
            
            filename = f"PT_Circularizacion_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            output_path = self.output_dir / filename
            wb.save(output_path)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating circularization paper: {e}")
            return None
    
    def _generate_related_parties_paper(self, year: int) -> Optional[Path]:
        """Generate related parties working paper"""
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Partes Vinculadas"
            
            ws['A1'] = 'PAPEL DE TRABAJO - PARTES VINCULADAS'
            ws['A1'].font = Font(size=14, bold=True)
            
            headers = ['Parte Vinculada', 'Relación', 'Tipo Operación', 'Importe', 'Saldo Pendiente']
            for col, header in enumerate(headers, start=1):
                ws.cell(3, col, header).font = Font(bold=True)
            
            # Sample related parties
            related_parties = [
                ['Socios/Accionistas', 'Propietario', 'Préstamos', 0, 0],
                ['Administradores', 'Gestión', 'Remuneración', 0, 0],
                ['Empresas del grupo', 'Grupo', 'Compras/Ventas', 0, 0]
            ]
            
            for i, party in enumerate(related_parties, start=4):
                for j, value in enumerate(party, start=1):
                    cell = ws.cell(i, j, value)
                    if j >= 4:
                        cell.number_format = '#,##0.00'
            
            filename = f"PT_Partes_Vinculadas_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            output_path = self.output_dir / filename
            wb.save(output_path)
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error generating related parties paper: {e}")
            return None
