"""
Materiality Calculator Module
Calculates materiality according to ISA/NIA standards based on financial analysis,
sector benchmarks, questionnaires, and analytical procedures
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

try:
    from src.accounting_core import AccountingPeriod, BalanceAccount
except ImportError:
    AccountingPeriod = None
    BalanceAccount = None


class MaterialityCalculator:
    """Calculates audit materiality according to ISA/NIA standards"""
    
    def __init__(self, config: Dict, accounting_processor):
        """Initialize materiality calculator"""
        self.config = config
        self.accounting = accounting_processor
        self.logger = logging.getLogger(__name__)
        
        # NIA/ISA standard benchmarks (percentages)
        self.benchmarks = {
            'resultado_neto': {'min': 0.05, 'max': 0.10, 'typical': 0.05},  # 5-10% of net income
            'ingresos': {'min': 0.005, 'max': 0.01, 'typical': 0.005},      # 0.5-1% of revenues
            'activo_total': {'min': 0.01, 'max': 0.02, 'typical': 0.01},    # 1-2% of total assets
            'patrimonio_neto': {'min': 0.01, 'max': 0.05, 'typical': 0.03}, # 1-5% of equity
            'gastos_totales': {'min': 0.01, 'max': 0.02, 'typical': 0.02}   # 1-2% of total expenses
        }
        
        # Risk factors questionnaire weights
        self.risk_weights = {
            'high_risk': 0.5,     # Reduce materiality by 50% for high risk
            'medium_risk': 0.75,  # Reduce materiality by 25% for medium risk
            'low_risk': 1.0       # No adjustment for low risk
        }
    
    def calculate_materiality(self, year: int, entity_type: str = 'mercantil',
                            risk_assessment: Optional[str] = None,
                            sector_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Calculate overall and performance materiality
        
        Args:
            year: Audit year
            entity_type: 'mercantil', 'esal', 'pyme'
            risk_assessment: 'low_risk', 'medium_risk', 'high_risk'
            sector_data: Optional sector benchmark data
            
        Returns:
            Dictionary with materiality calculations and justification
        """
        self.logger.info(f"Calculating materiality for year {year}")
        
        # Get accounting period
        period = self.accounting.session.query(
            AccountingPeriod
        ).filter_by(year=year).first()
        
        if not period:
            self.logger.error(f"Period {year} not found")
            return {'error': 'Period not found'}
        
        # Get key financial figures
        financial_figures = self._get_financial_figures(period)
        
        # Calculate materiality using different bases
        materiality_calculations = self._calculate_by_multiple_bases(financial_figures, entity_type)
        
        # Apply risk adjustment
        if risk_assessment:
            risk_factor = self.risk_weights.get(risk_assessment, 1.0)
        else:
            risk_factor = self._assess_inherent_risk(financial_figures)
        
        # Select most appropriate base
        selected_materiality = self._select_appropriate_materiality(
            materiality_calculations,
            financial_figures,
            entity_type
        )
        
        # Apply risk adjustment
        overall_materiality = selected_materiality * risk_factor
        
        # Calculate performance materiality (typically 50-75% of overall)
        performance_materiality = overall_materiality * 0.75
        
        # Calculate trivial threshold (typically 3-5% of overall)
        trivial_threshold = overall_materiality * 0.05
        
        # Sector comparison
        sector_comparison = None
        if sector_data:
            sector_comparison = self._compare_with_sector(
                overall_materiality,
                financial_figures,
                sector_data
            )
        
        result = {
            'year': year,
            'entity_type': entity_type,
            'financial_figures': financial_figures,
            'materiality_by_base': materiality_calculations,
            'selected_base': selected_materiality,
            'risk_assessment': risk_assessment or 'auto_assessed',
            'risk_factor': risk_factor,
            'overall_materiality': round(overall_materiality, 2),
            'performance_materiality': round(performance_materiality, 2),
            'trivial_threshold': round(trivial_threshold, 2),
            'sector_comparison': sector_comparison,
            'calculation_date': datetime.now().isoformat(),
            'justification': self._generate_justification(
                selected_materiality,
                overall_materiality,
                materiality_calculations,
                risk_assessment,
                entity_type
            )
        }
        
        return result
    
    def _get_financial_figures(self, period) -> Dict[str, float]:
        """Extract key financial figures from accounting data"""
        
        accounts = self.accounting.session.query(
            BalanceAccount
        ).filter_by(period_id=period.id).all()
        
        # Calculate key figures
        activo_total = sum(acc.saldo_final for acc in accounts if acc.account_code.startswith(('2', '3', '4', '5')) and acc.saldo_final > 0)
        
        pasivo_total = sum(abs(acc.saldo_final) for acc in accounts if acc.account_code.startswith(('1', '4', '5')) and acc.saldo_final < 0)
        
        patrimonio_neto = sum(abs(acc.saldo_final) for acc in accounts if acc.account_code.startswith('10'))
        
        ingresos = sum(abs(acc.saldo_final) for acc in accounts if acc.account_code.startswith('7'))
        
        gastos = sum(abs(acc.saldo_final) for acc in accounts if acc.account_code.startswith('6'))
        
        resultado_neto = ingresos - gastos
        
        return {
            'activo_total': activo_total,
            'pasivo_total': pasivo_total,
            'patrimonio_neto': patrimonio_neto,
            'ingresos': ingresos,
            'gastos': gastos,
            'resultado_neto': resultado_neto,
            'resultado_absoluto': abs(resultado_neto)
        }
    
    def _calculate_by_multiple_bases(self, figures: Dict[str, float], entity_type: str) -> Dict[str, float]:
        """Calculate materiality using multiple bases"""
        
        calculations = {}
        
        # Revenue base (most common for profitable entities)
        if figures['ingresos'] > 0:
            calculations['por_ingresos'] = figures['ingresos'] * self.benchmarks['ingresos']['typical']
        
        # Result base (if stable and positive)
        if figures['resultado_absoluto'] > 0 and figures['resultado_neto'] > 0:
            calculations['por_resultado'] = figures['resultado_absoluto'] * self.benchmarks['resultado_neto']['typical']
        
        # Asset base (for asset-intensive entities)
        if figures['activo_total'] > 0:
            calculations['por_activo'] = figures['activo_total'] * self.benchmarks['activo_total']['typical']
        
        # Equity base (for financial entities or when equity is significant)
        if figures['patrimonio_neto'] > 0:
            calculations['por_patrimonio'] = figures['patrimonio_neto'] * self.benchmarks['patrimonio_neto']['typical']
        
        # Expense base (for non-profit entities)
        if entity_type == 'esal' and figures['gastos'] > 0:
            calculations['por_gastos'] = figures['gastos'] * self.benchmarks['gastos_totales']['typical']
        
        return calculations
    
    def _select_appropriate_materiality(self, calculations: Dict[str, float],
                                       figures: Dict[str, float],
                                       entity_type: str) -> float:
        """Select the most appropriate materiality base"""
        
        if not calculations:
            # Fallback to 1% of total assets
            return figures['activo_total'] * 0.01
        
        # For ESAL entities, prioritize expenses
        if entity_type == 'esal' and 'por_gastos' in calculations:
            return calculations['por_gastos']
        
        # For profitable entities, prioritize result or revenue
        if figures['resultado_neto'] > 0 and 'por_resultado' in calculations:
            # Check if result is stable (not volatile)
            if calculations['por_resultado'] <= calculations.get('por_ingresos', float('inf')):
                return calculations['por_resultado']
        
        # Otherwise, use revenue base
        if 'por_ingresos' in calculations:
            return calculations['por_ingresos']
        
        # Fallback to median of all calculations
        return sorted(calculations.values())[len(calculations) // 2]
    
    def _assess_inherent_risk(self, figures: Dict[str, float]) -> float:
        """Assess inherent risk based on financial indicators"""
        
        risk_score = 0
        risk_factors = 0
        
        # Check profitability
        if figures['resultado_neto'] < 0:
            risk_score += 2
            risk_factors += 1
        elif figures['resultado_neto'] < figures['ingresos'] * 0.03:  # Less than 3% margin
            risk_score += 1
            risk_factors += 1
        
        # Check liquidity
        if figures['activo_total'] > 0:
            leverage = figures['pasivo_total'] / figures['activo_total']
            if leverage > 0.7:  # High leverage
                risk_score += 2
                risk_factors += 1
            elif leverage > 0.5:
                risk_score += 1
                risk_factors += 1
        
        # Average risk score
        if risk_factors > 0:
            avg_risk = risk_score / risk_factors
            if avg_risk >= 1.5:
                return self.risk_weights['high_risk']
            elif avg_risk >= 0.8:
                return self.risk_weights['medium_risk']
        
        return self.risk_weights['low_risk']
    
    def _compare_with_sector(self, materiality: float, figures: Dict[str, float],
                            sector_data: Dict) -> Dict[str, Any]:
        """Compare calculated materiality with sector benchmarks"""
        
        # Calculate materiality as percentage of revenue
        if figures['ingresos'] > 0:
            materiality_pct = (materiality / figures['ingresos']) * 100
            
            sector_avg = sector_data.get('avg_materiality_pct', 0.5)
            sector_min = sector_data.get('min_materiality_pct', 0.3)
            sector_max = sector_data.get('max_materiality_pct', 1.0)
            
            return {
                'materiality_pct_revenue': round(materiality_pct, 3),
                'sector_average': sector_avg,
                'sector_min': sector_min,
                'sector_max': sector_max,
                'within_range': sector_min <= materiality_pct <= sector_max,
                'comparison': 'above' if materiality_pct > sector_avg else 'below' if materiality_pct < sector_avg else 'aligned'
            }
        
        return None
    
    def _generate_justification(self, selected_base: float, final_materiality: float,
                               calculations: Dict[str, float], risk: Optional[str],
                               entity_type: str) -> str:
        """Generate written justification for materiality calculation"""
        
        # Find which base was selected
        selected_method = None
        for method, value in calculations.items():
            if abs(value - selected_base) < 0.01:
                selected_method = method
                break
        
        justification = f"""
JUSTIFICACIÓN DEL CÁLCULO DE MATERIALIDAD

1. BASE DE CÁLCULO SELECCIONADA:
   Se ha utilizado la base '{selected_method or "mixta"}' por ser la más apropiada para el tipo de entidad ({entity_type}).
   Materialidad calculada: {selected_base:,.2f} €

2. BASES CONSIDERADAS:
"""
        
        for method, value in calculations.items():
            justification += f"   - {method}: {value:,.2f} €\n"
        
        if risk:
            justification += f"""
3. AJUSTE POR RIESGO:
   Se ha aplicado un ajuste por riesgo '{risk}' resultando en una materialidad final de {final_materiality:,.2f} €
"""
        
        justification += f"""
4. CONCLUSIÓN:
   La materialidad global se establece en {final_materiality:,.2f} €, cumpliendo con los parámetros de las NIA.
   Esta cifra representa aproximadamente el {(final_materiality / calculations.get('por_ingresos', 1)) * 100:.2f}% de los ingresos.
"""
        
        return justification
    
    def generate_materiality_working_paper(self, year: int, entity_type: str = 'mercantil',
                                          risk_assessment: Optional[str] = None) -> Path:
        """Generate materiality working paper in Excel format"""
        
        self.logger.info(f"Generating materiality working paper for {year}")
        
        # Calculate materiality
        materiality_data = self.calculate_materiality(year, entity_type, risk_assessment)
        
        if 'error' in materiality_data:
            return None
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Materialidad"
        
        # Header
        ws['A1'] = 'PAPEL DE TRABAJO - DETERMINACIÓN DE LA MATERIALIDAD'
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:F1')
        
        ws['A3'] = 'Ejercicio:'
        ws['B3'] = year
        ws['A4'] = 'Tipo de entidad:'
        ws['B4'] = entity_type.upper()
        ws['A5'] = 'Fecha cálculo:'
        ws['B5'] = datetime.now().strftime('%d/%m/%Y')
        
        # Financial figures section
        ws['A7'] = 'MAGNITUDES FINANCIERAS BASE'
        ws['A7'].font = Font(bold=True)
        
        figures = materiality_data['financial_figures']
        row = 8
        for key, value in figures.items():
            ws.cell(row, 1, key.replace('_', ' ').title() + ':')
            ws.cell(row, 2, value).number_format = '#,##0.00 €'
            row += 1
        
        # Materiality calculations
        ws[f'A{row+1}'] = 'CÁLCULOS DE MATERIALIDAD POR DIFERENTES BASES'
        ws[f'A{row+1}'].font = Font(bold=True)
        
        row += 2
        ws.cell(row, 1, 'Base de Cálculo')
        ws.cell(row, 2, 'Importe')
        ws.cell(row, 3, 'Porcentaje Aplicado')
        
        for col in [1, 2, 3]:
            ws.cell(row, col).font = Font(bold=True, color="FFFFFF")
            ws.cell(row, col).fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        row += 1
        for base, amount in materiality_data['materiality_by_base'].items():
            ws.cell(row, 1, base.replace('_', ' ').title())
            ws.cell(row, 2, amount).number_format = '#,##0.00 €'
            
            # Calculate percentage used
            if 'ingresos' in base:
                pct = self.benchmarks['ingresos']['typical'] * 100
            elif 'resultado' in base:
                pct = self.benchmarks['resultado_neto']['typical'] * 100
            elif 'activo' in base:
                pct = self.benchmarks['activo_total']['typical'] * 100
            elif 'patrimonio' in base:
                pct = self.benchmarks['patrimonio_neto']['typical'] * 100
            else:
                pct = self.benchmarks['gastos_totales']['typical'] * 100
            
            ws.cell(row, 3, f"{pct}%")
            row += 1
        
        # Risk adjustment
        ws[f'A{row+2}'] = 'AJUSTE POR RIESGO'
        ws[f'A{row+2}'].font = Font(bold=True)
        
        row += 3
        ws.cell(row, 1, 'Evaluación de riesgo:')
        ws.cell(row, 2, materiality_data['risk_assessment'].upper())
        row += 1
        ws.cell(row, 1, 'Factor de ajuste:')
        ws.cell(row, 2, f"{materiality_data['risk_factor'] * 100:.0f}%")
        
        # Final materiality
        row += 2
        ws[f'A{row}'] = 'MATERIALIDAD DETERMINADA'
        ws[f'A{row}'].font = Font(size=12, bold=True)
        
        row += 1
        ws.cell(row, 1, 'Materialidad Global:')
        ws.cell(row, 2, materiality_data['overall_materiality']).number_format = '#,##0.00 €'
        ws.cell(row, 2).font = Font(bold=True, size=12)
        
        row += 1
        ws.cell(row, 1, 'Materialidad de Ejecución (75%):')
        ws.cell(row, 2, materiality_data['performance_materiality']).number_format = '#,##0.00 €'
        ws.cell(row, 2).font = Font(bold=True)
        
        row += 1
        ws.cell(row, 1, 'Umbral de Trivialidad (5%):')
        ws.cell(row, 2, materiality_data['trivial_threshold']).number_format = '#,##0.00 €'
        ws.cell(row, 2).font = Font(bold=True)
        
        # Justification
        row += 3
        ws[f'A{row}'] = 'JUSTIFICACIÓN'
        ws[f'A{row}'].font = Font(bold=True)
        ws.merge_cells(f'A{row}:F{row}')
        
        row += 1
        justification_lines = materiality_data['justification'].split('\n')
        for line in justification_lines:
            ws.cell(row, 1, line)
            ws.merge_cells(f'A{row}:F{row}')
            ws.cell(row, 1).alignment = Alignment(wrap_text=True)
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        
        # Save
        output_dir = Path(self.config.get('working_papers', {}).get('output_dir', './papeles_trabajo'))
        output_dir.mkdir(exist_ok=True)
        
        filename = f"PT_Materialidad_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        output_path = output_dir / filename
        wb.save(output_path)
        
        self.logger.info(f"Materiality working paper saved to {output_path}")
        
        return output_path
