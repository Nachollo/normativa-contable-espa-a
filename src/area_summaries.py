"""
Area Summaries Generator - Generates summary papers and conclusions for each audit area
with adjustments and reclassifications tracking.

This module creates comprehensive summary working papers for each audit area including:
- Summary of findings and conclusions
- Adjustments (both processed and proposed)
- Reclassifications
- Impact analysis
- Sign-off and review tracking
"""

import pandas as pd
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Adjustment:
    """Represents an audit adjustment entry"""
    def __init__(self, adj_id: str, description: str, account: str, debit: float, 
                 credit: float, reason: str, status: str = "proposed"):
        self.adj_id = adj_id
        self.description = description
        self.account = account
        self.debit = debit
        self.credit = credit
        self.reason = reason
        self.status = status  # proposed, processed, rejected
        
    def to_dict(self):
        return {
            'ID': self.adj_id,
            'Descripción': self.description,
            'Cuenta': self.account,
            'Debe': self.debit,
            'Haber': self.credit,
            'Motivo': self.reason,
            'Estado': self.status
        }


class Reclassification:
    """Represents a reclassification entry"""
    def __init__(self, reclas_id: str, description: str, from_account: str, 
                 to_account: str, amount: float, reason: str, status: str = "proposed"):
        self.reclas_id = reclas_id
        self.description = description
        self.from_account = from_account
        self.to_account = to_account
        self.amount = amount
        self.reason = reason
        self.status = status  # proposed, processed, rejected
        
    def to_dict(self):
        return {
            'ID': self.reclas_id,
            'Descripción': self.description,
            'De Cuenta': self.from_account,
            'A Cuenta': self.to_account,
            'Importe': self.amount,
            'Motivo': self.reason,
            'Estado': self.status
        }


class AreaSummary:
    """Generates summary working papers for audit areas"""
    
    def __init__(self, accounting_core, year: int):
        self.accounting = accounting_core
        self.year = year
        self.adjustments: List[Adjustment] = []
        self.reclassifications: List[Reclassification] = []
        
    def add_adjustment(self, adj: Adjustment):
        """Add an adjustment to the area"""
        self.adjustments.append(adj)
        
    def add_reclassification(self, reclas: Reclassification):
        """Add a reclassification to the area"""
        self.reclassifications.append(reclas)
        
    def get_total_adjustments(self) -> Tuple[float, float]:
        """Calculate total adjustments (debit, credit)"""
        total_debit = sum(adj.debit for adj in self.adjustments if adj.status == "proposed")
        total_credit = sum(adj.credit for adj in self.adjustments if adj.status == "proposed")
        return total_debit, total_credit
        
    def get_total_reclassifications(self) -> float:
        """Calculate total reclassification amount"""
        return sum(reclas.amount for reclas in self.reclassifications if reclas.status == "proposed")
        
    def generate_summary(self, area_name: str, accounts_prefix: str, 
                        findings: List[str], conclusions: List[str],
                        output_path: str) -> str:
        """
        Generate comprehensive area summary working paper
        
        Args:
            area_name: Name of the audit area (e.g., "Inmovilizado Material")
            accounts_prefix: Account prefix for the area (e.g., "21")
            findings: List of audit findings
            conclusions: List of audit conclusions
            output_path: Path to save the working paper
            
        Returns:
            Path to the generated file
        """
        try:
            wb = Workbook()
            
            # Remove default sheet
            if 'Sheet' in wb.sheetnames:
                del wb['Sheet']
            
            # Create sheets
            self._create_summary_sheet(wb, area_name, accounts_prefix, findings, conclusions)
            self._create_adjustments_sheet(wb, area_name)
            self._create_reclassifications_sheet(wb, area_name)
            self._create_impact_analysis_sheet(wb, area_name, accounts_prefix)
            self._create_signoff_sheet(wb, area_name)
            
            # Save workbook
            filename = f"PT_Sumaria_{area_name.replace(' ', '_')}_{self.year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            filepath = f"{output_path}/{filename}"
            wb.save(filepath)
            
            logger.info(f"✓ Generada sumaria para {area_name}: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generando sumaria para {area_name}: {str(e)}")
            raise
            
    def _create_summary_sheet(self, wb: Workbook, area_name: str, accounts_prefix: str,
                             findings: List[str], conclusions: List[str]):
        """Create the summary and conclusions sheet"""
        ws = wb.create_sheet("Sumaria y Conclusiones")
        
        # Header
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=14)
        
        ws['A1'] = f"SUMARIA - {area_name.upper()}"
        ws['A1'].font = header_font
        ws['A1'].fill = header_fill
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.merge_cells('A1:F1')
        ws.row_dimensions[1].height = 25
        
        # Info section
        info_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        ws['A3'] = "Área:"
        ws['B3'] = area_name
        ws['A4'] = "Ejercicio:"
        ws['B4'] = self.year
        ws['A5'] = "Cuentas:"
        ws['B5'] = f"{accounts_prefix}xx"
        ws['A6'] = "Fecha:"
        ws['B6'] = datetime.now().strftime('%d/%m/%Y')
        
        for row in [3, 4, 5, 6]:
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'A{row}'].fill = info_fill
        
        # Findings section
        row = 8
        ws[f'A{row}'] = "HALLAZGOS DE AUDITORÍA"
        ws[f'A{row}'].font = Font(bold=True, size=12, color="FFFFFF")
        ws[f'A{row}'].fill = PatternFill(start_color="E26B0A", end_color="E26B0A", fill_type="solid")
        ws.merge_cells(f'A{row}:F{row}')
        
        row += 1
        for i, finding in enumerate(findings, 1):
            ws[f'A{row}'] = f"{i}."
            ws[f'B{row}'] = finding
            ws.merge_cells(f'B{row}:F{row}')
            ws[f'B{row}'].alignment = Alignment(wrap_text=True, vertical='top')
            ws.row_dimensions[row].height = 30
            row += 1
            
        # Add space
        row += 1
        
        # Conclusions section
        ws[f'A{row}'] = "CONCLUSIONES"
        ws[f'A{row}'].font = Font(bold=True, size=12, color="FFFFFF")
        ws[f'A{row}'].fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        ws.merge_cells(f'A{row}:F{row}')
        
        row += 1
        for i, conclusion in enumerate(conclusions, 1):
            ws[f'A{row}'] = f"{i}."
            ws[f'B{row}'] = conclusion
            ws.merge_cells(f'B{row}:F{row}')
            ws[f'B{row}'].alignment = Alignment(wrap_text=True, vertical='top')
            ws.row_dimensions[row].height = 30
            row += 1
            
        # Adjustments summary
        row += 2
        total_debit, total_credit = self.get_total_adjustments()
        total_reclas = self.get_total_reclassifications()
        
        ws[f'A{row}'] = "RESUMEN DE AJUSTES Y RECLASIFICACIONES"
        ws[f'A{row}'].font = Font(bold=True, size=11)
        ws[f'A{row}'].fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
        ws.merge_cells(f'A{row}:F{row}')
        
        row += 1
        ws[f'A{row}'] = "Total Ajustes (Debe):"
        ws[f'B{row}'] = total_debit
        ws[f'B{row}'].number_format = '#,##0.00'
        ws[f'D{row}'] = "Total Ajustes (Haber):"
        ws[f'E{row}'] = total_credit
        ws[f'E{row}'].number_format = '#,##0.00'
        
        row += 1
        ws[f'A{row}'] = "Total Reclasificaciones:"
        ws[f'B{row}'] = total_reclas
        ws[f'B{row}'].number_format = '#,##0.00'
        
        # Set column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        
    def _create_adjustments_sheet(self, wb: Workbook, area_name: str):
        """Create the adjustments tracking sheet"""
        ws = wb.create_sheet("Ajustes")
        
        # Header
        header_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        headers = ['ID', 'Descripción', 'Cuenta', 'Debe', 'Haber', 'Motivo', 'Estado']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
        # Add adjustments
        for row, adj in enumerate(self.adjustments, 2):
            data = adj.to_dict()
            ws[f'A{row}'] = data['ID']
            ws[f'B{row}'] = data['Descripción']
            ws[f'C{row}'] = data['Cuenta']
            ws[f'D{row}'] = data['Debe']
            ws[f'E{row}'] = data['Haber']
            ws[f'F{row}'] = data['Motivo']
            ws[f'G{row}'] = data['Estado']
            
            # Format numbers
            ws[f'D{row}'].number_format = '#,##0.00'
            ws[f'E{row}'].number_format = '#,##0.00'
            
            # Color code status
            status_fill = None
            if data['Estado'] == 'proposed':
                status_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            elif data['Estado'] == 'processed':
                status_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif data['Estado'] == 'rejected':
                status_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                
            if status_fill:
                ws[f'G{row}'].fill = status_fill
                
        # Totals
        if self.adjustments:
            total_row = len(self.adjustments) + 2
            ws[f'C{total_row}'] = "TOTAL"
            ws[f'C{total_row}'].font = Font(bold=True)
            ws[f'D{total_row}'] = f"=SUM(D2:D{total_row-1})"
            ws[f'E{total_row}'] = f"=SUM(E2:E{total_row-1})"
            ws[f'D{total_row}'].number_format = '#,##0.00'
            ws[f'E{total_row}'].number_format = '#,##0.00'
            ws[f'D{total_row}'].font = Font(bold=True)
            ws[f'E{total_row}'].font = Font(bold=True)
            
        # Set column widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 50
        ws.column_dimensions['G'].width = 12
        
    def _create_reclassifications_sheet(self, wb: Workbook, area_name: str):
        """Create the reclassifications tracking sheet"""
        ws = wb.create_sheet("Reclasificaciones")
        
        # Header
        header_fill = PatternFill(start_color="0070C0", end_color="0070C0", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        headers = ['ID', 'Descripción', 'De Cuenta', 'A Cuenta', 'Importe', 'Motivo', 'Estado']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            
        # Add reclassifications
        for row, reclas in enumerate(self.reclassifications, 2):
            data = reclas.to_dict()
            ws[f'A{row}'] = data['ID']
            ws[f'B{row}'] = data['Descripción']
            ws[f'C{row}'] = data['De Cuenta']
            ws[f'D{row}'] = data['A Cuenta']
            ws[f'E{row}'] = data['Importe']
            ws[f'F{row}'] = data['Motivo']
            ws[f'G{row}'] = data['Estado']
            
            # Format numbers
            ws[f'E{row}'].number_format = '#,##0.00'
            
            # Color code status
            status_fill = None
            if data['Estado'] == 'proposed':
                status_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            elif data['Estado'] == 'processed':
                status_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif data['Estado'] == 'rejected':
                status_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                
            if status_fill:
                ws[f'G{row}'].fill = status_fill
                
        # Total
        if self.reclassifications:
            total_row = len(self.reclassifications) + 2
            ws[f'D{total_row}'] = "TOTAL"
            ws[f'D{total_row}'].font = Font(bold=True)
            ws[f'E{total_row}'] = f"=SUM(E2:E{total_row-1})"
            ws[f'E{total_row}'].number_format = '#,##0.00'
            ws[f'E{total_row}'].font = Font(bold=True)
            
        # Set column widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 50
        ws.column_dimensions['G'].width = 12
        
    def _create_impact_analysis_sheet(self, wb: Workbook, area_name: str, accounts_prefix: str):
        """Create the impact analysis sheet"""
        ws = wb.create_sheet("Análisis de Impacto")
        
        # Header
        ws['A1'] = "ANÁLISIS DE IMPACTO DE AJUSTES Y RECLASIFICACIONES"
        ws['A1'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="44546A", end_color="44546A", fill_type="solid")
        ws.merge_cells('A1:E1')
        
        # Impact categories
        row = 3
        categories = [
            ("Balance de Situación", "Activos, Pasivos, Patrimonio Neto"),
            ("Cuenta de Resultados", "Ingresos, Gastos, Resultado del Ejercicio"),
            ("Ratios Financieros", "Liquidez, Solvencia, Rentabilidad"),
            ("Indicadores Clave", "EBITDA, Working Capital, etc."),
            ("Cumplimiento Normativo", "Impacto en cumplimiento de covenants/normativa")
        ]
        
        for category, description in categories:
            ws[f'A{row}'] = category
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'A{row}'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            ws[f'B{row}'] = description
            ws.merge_cells(f'B{row}:E{row}')
            ws[f'B{row}'].alignment = Alignment(wrap_text=True)
            ws.row_dimensions[row].height = 30
            row += 1
            
            # Placeholder for impact details
            ws[f'A{row}'] = "Impacto:"
            ws[f'B{row}'] = "Pendiente de análisis"
            ws.merge_cells(f'B{row}:E{row}')
            row += 2
            
        # Set column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 60
        
    def _create_signoff_sheet(self, wb: Workbook, area_name: str):
        """Create the sign-off and review sheet"""
        ws = wb.create_sheet("Firmas y Revisión")
        
        # Header
        ws['A1'] = "CONTROL DE REVISIÓN Y FIRMAS"
        ws['A1'].font = Font(bold=True, size=12, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="44546A", end_color="44546A", fill_type="solid")
        ws.merge_cells('A1:D1')
        
        # Review table
        row = 3
        ws[f'A{row}'] = "Rol"
        ws[f'B{row}'] = "Nombre"
        ws[f'C{row}'] = "Fecha"
        ws[f'D{row}'] = "Firma"
        
        for col in ['A', 'B', 'C', 'D']:
            ws[f'{col}{row}'].font = Font(bold=True)
            ws[f'{col}{row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            ws[f'{col}{row}'].alignment = Alignment(horizontal='center')
            
        roles = [
            "Preparado por:",
            "Revisado por:",
            "Socio responsable:"
        ]
        
        for i, role in enumerate(roles, 1):
            ws[f'A{row+i}'] = role
            ws[f'A{row+i}'].font = Font(bold=True)
            ws.row_dimensions[row+i].height = 25
            
        # Notes section
        row += len(roles) + 3
        ws[f'A{row}'] = "NOTAS Y OBSERVACIONES"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
        ws.merge_cells(f'A{row}:D{row}')
        
        row += 1
        ws[f'A{row}'] = "Añadir comentarios adicionales aquí..."
        ws.merge_cells(f'A{row}:D{row+5}')
        ws[f'A{row}'].alignment = Alignment(wrap_text=True, vertical='top')
        
        # Set column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 25


def generate_area_summaries(accounting_core, year: int, output_dir: str, 
                           entity_type: str = "mercantil") -> List[str]:
    """
    Generate summary working papers for all major audit areas
    
    Args:
        accounting_core: AccountingCore instance with loaded data
        year: Audit year
        output_dir: Directory to save working papers
        entity_type: Type of entity (mercantil, ESAL, PYME)
        
    Returns:
        List of generated file paths
    """
    generated_files = []
    
    # Define audit areas with their characteristics
    areas = [
        {
            'name': 'Inmovilizado Material',
            'prefix': '21',
            'findings': [
                'Revisión física realizada sobre muestra del 25% del inmovilizado',
                'Verificados títulos de propiedad y cargas registradas',
                'Recalculadas amortizaciones según vida útil y método aplicado',
                'No se identifican indicios de deterioro significativos'
            ],
            'conclusions': [
                'Los saldos de inmovilizado material se presentan razonablemente',
                'Las amortizaciones se calculan de acuerdo a la normativa aplicable',
                'No se requieren ajustes significativos en este área'
            ],
            'sample_adjustments': [
                Adjustment('AJ-INM-001', 'Corrección amortización exceso vida útil', '681', 150.50, 0, 
                          'Elemento amortizado más allá de su vida útil', 'proposed'),
                Adjustment('AJ-INM-001', 'Contrapartida corrección amortización', '281', 0, 150.50, 
                          'Ajuste de amortización acumulada', 'proposed')
            ],
            'sample_reclassifications': [
                Reclassification('RC-INM-001', 'Reclasificación a inversiones', '217', '220', 5000.00,
                               'Inmueble para inversión no clasificado correctamente', 'proposed')
            ]
        },
        {
            'name': 'Existencias',
            'prefix': '3',
            'findings': [
                'Asistencia a inventario físico realizada el 31/12',
                'Revisado método de valoración (FIFO/PMPP)',
                'Analizado movimiento y rotación de existencias',
                'Identificadas existencias obsoletas por importe no material'
            ],
            'conclusions': [
                'El inventario físico se ajusta a los registros contables',
                'El método de valoración se aplica consistentemente',
                'Se requiere ajuste menor por existencias obsoletas'
            ],
            'sample_adjustments': [
                Adjustment('AJ-EX-001', 'Deterioro existencias obsoletas', '693', 850.00, 0,
                          'Existencias sin movimiento > 12 meses', 'proposed'),
                Adjustment('AJ-EX-001', 'Provisión por deterioro', '390', 0, 850.00,
                          'Dotación provisión existencias', 'proposed')
            ],
            'sample_reclassifications': []
        },
        {
            'name': 'Tesorería',
            'prefix': '57',
            'findings': [
                'Obtenidas confirmaciones bancarias para todas las cuentas',
                'Revisadas conciliaciones bancarias a 31/12',
                'Verificadas restricciones sobre fondos',
                'No se identifican partidas pendientes de conciliar significativas'
            ],
            'conclusions': [
                'Los saldos de tesorería están confirmados y conciliados',
                'No existen restricciones materiales sobre el efectivo',
                'Los saldos se presentan razonablemente en el balance'
            ],
            'sample_adjustments': [],
            'sample_reclassifications': []
        },
        {
            'name': 'Deudores Comerciales',
            'prefix': '43',
            'findings': [
                'Circularización realizada sobre el 70% del saldo',
                'Revisado aging de clientes y procedimientos de cobro',
                'Analizada cobertura de provisión por insolvencias',
                'Verificados cobros posteriores para saldos sin respuesta'
            ],
            'conclusions': [
                'Los saldos de clientes están sustancialmente confirmados',
                'La provisión por insolvencias es adecuada según el riesgo evaluado',
                'Los procedimientos de cobro son efectivos'
            ],
            'sample_adjustments': [
                Adjustment('AJ-DED-001', 'Incremento provisión insolvencias', '694', 1200.00, 0,
                          'Saldos > 180 días con alto riesgo', 'proposed'),
                Adjustment('AJ-DED-001', 'Provisión deudores', '490', 0, 1200.00,
                          'Incremento provisión', 'proposed')
            ],
            'sample_reclassifications': []
        },
        {
            'name': 'Pasivos Financieros',
            'prefix': '17',
            'findings': [
                'Confirmados saldos y condiciones con entidades financieras',
                'Revisados contratos de préstamos y líneas de crédito',
                'Verificado cumplimiento de covenants financieros',
                'Analizada clasificación entre corto y largo plazo'
            ],
            'conclusions': [
                'Los pasivos financieros están íntegramente confirmados',
                'Se cumple con los covenants financieros establecidos',
                'La clasificación temporal es correcta'
            ],
            'sample_adjustments': [],
            'sample_reclassifications': [
                Reclassification('RC-PAS-001', 'Reclasificación a corto plazo', '170', '520', 50000.00,
                               'Vencimiento dentro de 12 meses', 'proposed')
            ]
        },
        {
            'name': 'Impuestos',
            'prefix': '47',
            'findings': [
                'Revisadas declaraciones fiscales del ejercicio',
                'Recalculado impuesto sobre sociedades',
                'Verificadas retenciones y pagos a cuenta',
                'Analizado IVA repercutido y soportado'
            ],
            'conclusions': [
                'Las declaraciones fiscales se presentan correctamente',
                'El cálculo del impuesto es razonable',
                'No se identifican contingencias fiscales significativas'
            ],
            'sample_adjustments': [
                Adjustment('AJ-IMP-001', 'Ajuste gasto impuesto sociedades', '6300', 320.00, 0,
                          'Corrección base imponible', 'proposed'),
                Adjustment('AJ-IMP-001', 'HP acreedora por IS', '4752', 0, 320.00,
                          'Mayor impuesto a pagar', 'proposed')
            ],
            'sample_reclassifications': []
        }
    ]
    
    for area in areas:
        try:
            summary = AreaSummary(accounting_core, year)
            
            # Add sample adjustments and reclassifications
            for adj in area['sample_adjustments']:
                summary.add_adjustment(adj)
            for reclas in area['sample_reclassifications']:
                summary.add_reclassification(reclas)
                
            filepath = summary.generate_summary(
                area_name=area['name'],
                accounts_prefix=area['prefix'],
                findings=area['findings'],
                conclusions=area['conclusions'],
                output_path=output_dir
            )
            generated_files.append(filepath)
            
        except Exception as e:
            logger.error(f"Error generando sumaria para {area['name']}: {str(e)}")
            continue
            
    return generated_files
