"""
Risk Matrix Module
Creates risk assessment matrix by audit areas based on preliminary analysis,
materiality calculation, and analytical procedures
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

try:
    from src.accounting_core import AccountingPeriod, BalanceAccount
except ImportError:
    AccountingPeriod = None
    BalanceAccount = None


class RiskMatrix:
    """Generates risk assessment matrix by audit areas"""
    
    # Audit areas with account code ranges
    AUDIT_AREAS = {
        'inmovilizado': {
            'name': 'Inmovilizado Material e Intangible',
            'accounts': ['20', '21'],
            'risk_factors': [
                'Existencia física de activos',
                'Valoración y deterioro',
                'Amortizaciones',
                'Altas y bajas del ejercicio',
                'Propiedad y garantías'
            ]
        },
        'existencias': {
            'name': 'Existencias',
            'accounts': ['30', '31', '32', '33', '34', '35', '36'],
            'risk_factors': [
                'Recuento físico',
                'Valoración y obsolescencia',
                'Corte de operaciones',
                'Mercancías en depósito',
                'Provisiones por deterioro'
            ]
        },
        'deudores': {
            'name': 'Deudores Comerciales y Otras Cuentas a Cobrar',
            'accounts': ['43', '44', '46', '47'],
            'risk_factors': [
                'Confirmaciones de saldos',
                'Antigüedad de saldos',
                'Provisiones por insolvencias',
                'Corte de operaciones',
                'Saldos con partes vinculadas'
            ]
        },
        'inversiones_financieras': {
            'name': 'Inversiones Financieras',
            'accounts': ['24', '25', '53', '54'],
            'risk_factors': [
                'Existencia y propiedad',
                'Valoración a valor razonable',
                'Deterioros',
                'Derivados financieros',
                'Clasificación temporal'
            ]
        },
        'tesoreria': {
            'name': 'Efectivo y Otros Activos Líquidos',
            'accounts': ['57'],
            'risk_factors': [
                'Conciliaciones bancarias',
                'Confirmaciones bancarias',
                'Caja y arqueos',
                'Restricciones de disposición',
                'Gestión de efectivo'
            ]
        },
        'patrimonio_neto': {
            'name': 'Patrimonio Neto',
            'accounts': ['10', '11', '12', '13'],
            'risk_factors': [
                'Capital social y participaciones',
                'Reservas y dividendos',
                'Subvenciones',
                'Resultado del ejercicio',
                'Ajustes por cambio de valor'
            ]
        },
        'provisiones': {
            'name': 'Provisiones',
            'accounts': ['14'],
            'risk_factors': [
                'Provisión por impuestos',
                'Otras provisiones',
                'Litigios y contingencias',
                'Garantías',
                'Reestructuración'
            ]
        },
        'pasivos_financieros': {
            'name': 'Pasivos Financieros',
            'accounts': ['16', '17', '52'],
            'risk_factors': [
                'Confirmaciones bancarias',
                'Devengo de intereses',
                'Covenants y garantías',
                'Clasificación temporal',
                'Instrumentos financieros complejos'
            ]
        },
        'acreedores': {
            'name': 'Acreedores Comerciales y Otras Cuentas a Pagar',
            'accounts': ['40', '41', '46', '47', '57'],
            'risk_factors': [
                'Confirmaciones de saldos',
                'Pasivos no registrados',
                'Corte de operaciones',
                'Saldos con partes vinculadas',
                'Provisiones de compras'
            ]
        },
        'ingresos': {
            'name': 'Ingresos de Explotación',
            'accounts': ['70'],
            'risk_factors': [
                'Reconocimiento de ingresos',
                'Corte de operaciones',
                'Descuentos y devoluciones',
                'Partes vinculadas',
                'Contratos a largo plazo'
            ]
        },
        'compras': {
            'name': 'Aprovisionamientos',
            'accounts': ['60'],
            'risk_factors': [
                'Corte de operaciones',
                'Valoración de existencias',
                'Descuentos y rappels',
                'Partes vinculadas',
                'Variación de existencias'
            ]
        },
        'gastos_personal': {
            'name': 'Gastos de Personal',
            'accounts': ['64'],
            'risk_factors': [
                'Provisiones y pasivos devengados',
                'Cumplimiento laboral',
                'Partes vinculadas',
                'Indemnizaciones',
                'Seguridad Social'
            ]
        },
        'servicios_exteriores': {
            'name': 'Servicios Exteriores',
            'accounts': ['62'],
            'risk_factors': [
                'Devengo adecuado',
                'Partes vinculadas',
                'Corte de operaciones',
                'Provisiones de servicios',
                'Contratos plurianuales'
            ]
        },
        'amortizaciones': {
            'name': 'Amortizaciones y Deterioros',
            'accounts': ['68'],
            'risk_factors': [
                'Cálculo de amortizaciones',
                'Deterioros de activos',
                'Vidas útiles',
                'Valores residuales',
                'Pruebas de deterioro'
            ]
        },
        'resultados_financieros': {
            'name': 'Resultados Financieros',
            'accounts': ['76', '66'],
            'risk_factors': [
                'Devengo de intereses',
                'Valoración de instrumentos',
                'Diferencias de cambio',
                'Deterioro inversiones',
                'Derivados financieros'
            ]
        },
        'impuestos': {
            'name': 'Impuesto sobre Beneficios',
            'accounts': ['630', '633', '473', '4740'],
            'risk_factors': [
                'Cálculo del impuesto',
                'Diferencias temporarias',
                'Activos por impuesto diferido',
                'Inspecciones fiscales',
                'Precios de transferencia'
            ]
        },
        'partes_vinculadas': {
            'name': 'Transacciones con Partes Vinculadas',
            'accounts': ['55', '53'],
            'risk_factors': [
                'Identificación de partes vinculadas',
                'Desglose de transacciones',
                'Precios de transferencia',
                'Condiciones de mercado',
                'Revelación en memoria'
            ]
        }
    }
    
    def __init__(self, config: Dict, accounting_processor, materiality_data: Dict):
        """Initialize risk matrix generator"""
        self.config = config
        self.accounting = accounting_processor
        self.materiality = materiality_data
        self.logger = logging.getLogger(__name__)
        
    def assess_area_risk(self, area_key: str, year: int, 
                         financial_data: Dict) -> Dict[str, Any]:
        """
        Assess inherent and control risk for an audit area
        
        Args:
            area_key: Audit area identifier
            year: Audit year
            financial_data: Financial figures and ratios
            
        Returns:
            Risk assessment dictionary
        """
        area = self.AUDIT_AREAS.get(area_key, {})
        
        # Get balances for the area
        area_balance = self._get_area_balance(area.get('accounts', []), year)
        
        # Calculate significance (as % of overall materiality)
        overall_mat = self.materiality.get('overall_materiality', 0)
        if overall_mat > 0:
            significance = (area_balance / overall_mat) * 100
        else:
            # If materiality is 0 or not calculated, use a default threshold
            significance = 100 if area_balance > 10000 else 50
        
        # Assess inherent risk factors
        inherent_risk = self._assess_inherent_risk(area_key, financial_data)
        
        # Assess control risk (default to medium, would be customizable)
        control_risk = 'medium'
        
        # Combined risk assessment
        combined_risk = self._calculate_combined_risk(inherent_risk, control_risk, significance)
        
        return {
            'area_name': area.get('name', ''),
            'balance': area_balance,
            'significance_pct': round(significance, 2),
            'inherent_risk': inherent_risk,
            'control_risk': control_risk,
            'combined_risk': combined_risk,
            'risk_factors': area.get('risk_factors', []),
            'material': significance > 10  # Material if > 10% of overall materiality
        }
    
    def _get_area_balance(self, account_prefixes: List[str], year: int) -> float:
        """Get total balance for accounts matching prefixes"""
        period = self.accounting.session.query(
            AccountingPeriod
        ).filter_by(year=year).first()
        
        if not period:
            return 0.0
        
        total = 0.0
        for prefix in account_prefixes:
            accounts = self.accounting.session.query(
                BalanceAccount
            ).filter(
                BalanceAccount.period_id == period.id,
                BalanceAccount.account_code.like(f"{prefix}%")
            ).all()
            
            for account in accounts:
                total += abs(account.saldo_final or 0.0)
        
        return total
    
    def _assess_inherent_risk(self, area_key: str, financial_data: Dict) -> str:
        """Assess inherent risk level for an area"""
        # High risk areas by default
        high_risk_areas = ['ingresos', 'existencias', 'partes_vinculadas', 
                          'inversiones_financieras', 'provisiones']
        
        # Check financial indicators
        if area_key in high_risk_areas:
            base_risk = 'high'
        elif area_key in ['tesoreria', 'patrimonio_neto']:
            base_risk = 'low'
        else:
            base_risk = 'medium'
        
        # Adjust based on financial indicators
        if financial_data.get('first_year_audit', False):
            if base_risk == 'medium':
                base_risk = 'high'
        
        if financial_data.get('going_concern_issues', False):
            base_risk = 'high'
            
        return base_risk
    
    def _calculate_combined_risk(self, inherent: str, control: str, 
                                 significance: float) -> str:
        """Calculate combined risk level"""
        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        
        inherent_score = risk_scores.get(inherent, 2)
        control_score = risk_scores.get(control, 2)
        
        # Average risk score
        avg_score = (inherent_score + control_score) / 2
        
        # Increase risk if highly material
        if significance > 50:
            avg_score += 0.5
        elif significance > 25:
            avg_score += 0.25
        
        # Map back to risk level
        if avg_score >= 2.5:
            return 'high'
        elif avg_score >= 1.5:
            return 'medium'
        else:
            return 'low'
    
    def generate_risk_matrix(self, year: int, entity_info: Dict) -> pd.DataFrame:
        """
        Generate complete risk matrix for all audit areas
        
        Args:
            year: Audit year
            entity_info: Entity information and financial context
            
        Returns:
            DataFrame with risk assessments
        """
        self.logger.info(f"Generating risk matrix for year {year}")
        
        # Prepare financial data context
        financial_data = {
            'first_year_audit': entity_info.get('first_year_audit', False),
            'going_concern_issues': entity_info.get('going_concern_issues', False),
            'significant_changes': entity_info.get('significant_changes', False)
        }
        
        # Assess each area
        risk_assessments = []
        for area_key in self.AUDIT_AREAS.keys():
            assessment = self.assess_area_risk(area_key, year, financial_data)
            assessment['area_key'] = area_key
            risk_assessments.append(assessment)
        
        # Create DataFrame
        df = pd.DataFrame(risk_assessments)
        
        # Sort by combined risk and significance
        risk_order = {'high': 3, 'medium': 2, 'low': 1}
        df['risk_score'] = df['combined_risk'].map(risk_order)
        df = df.sort_values(['risk_score', 'significance_pct'], ascending=[False, False])
        df = df.drop('risk_score', axis=1)
        
        return df
    
    def export_to_excel(self, risk_matrix: pd.DataFrame, year: int, 
                       output_dir: str = './papeles_trabajo') -> str:
        """Export risk matrix to formatted Excel file"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"PT_Matriz_Riesgos_{year}_{timestamp}.xlsx"
        filepath = Path(output_dir) / filename
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Matriz de Riesgos"
        
        # Header
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        
        headers = [
            'Área de Auditoría',
            'Saldo (€)',
            'Significatividad (%)',
            'Riesgo Inherente',
            'Riesgo de Control',
            'Riesgo Combinado',
            'Material',
            'Factores de Riesgo'
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Data rows
        for row_idx, row_data in enumerate(risk_matrix.itertuples(index=False), start=2):
            ws.cell(row=row_idx, column=1, value=row_data.area_name)
            ws.cell(row=row_idx, column=2, value=row_data.balance)
            ws.cell(row=row_idx, column=3, value=row_data.significance_pct)
            ws.cell(row=row_idx, column=4, value=row_data.inherent_risk.upper())
            ws.cell(row=row_idx, column=5, value=row_data.control_risk.upper())
            ws.cell(row=row_idx, column=6, value=row_data.combined_risk.upper())
            ws.cell(row=row_idx, column=7, value='Sí' if row_data.material else 'No')
            ws.cell(row=row_idx, column=8, value='\n'.join(row_data.risk_factors[:3]))
            
            # Color code by risk level
            risk_cell = ws.cell(row=row_idx, column=6)
            if row_data.combined_risk == 'high':
                risk_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            elif row_data.combined_risk == 'medium':
                risk_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            else:
                risk_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 15
        ws.column_dimensions['G'].width = 10
        ws.column_dimensions['H'].width = 50
        
        wb.save(filepath)
        self.logger.info(f"Risk matrix exported to {filepath}")
        
        return str(filepath)
