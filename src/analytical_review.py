"""
Analytical Review and Financial Ratios Module
Comprehensive financial analysis, trend analysis, and sector benchmarking
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class AnalyticalReview:
    """Comprehensive analytical procedures and financial analysis"""
    
    def __init__(self, accounting_core, output_dir="./papeles_trabajo"):
        self.accounting = accounting_core
        self.output_dir = output_dir
        self.sector_benchmarks = self._load_sector_benchmarks()
    
    def _load_sector_benchmarks(self) -> Dict:
        """Load industry benchmark data"""
        # Spanish industry averages (approximate values)
        return {
            'comercio': {
                'name': 'Comercio',
                'liquidity': 1.5,
                'quick_ratio': 0.8,
                'debt_ratio': 0.55,
                'roe': 0.12,
                'roa': 0.06,
                'asset_turnover': 2.5,
                'inventory_turnover': 6.0,
                'receivables_days': 60,
                'payables_days': 70,
                'gross_margin': 0.25,
                'operating_margin': 0.08,
                'net_margin': 0.05
            },
            'industria': {
                'name': 'Industria',
                'liquidity': 1.8,
                'quick_ratio': 1.2,
                'debt_ratio': 0.50,
                'roe': 0.15,
                'roa': 0.08,
                'asset_turnover': 1.5,
                'inventory_turnover': 8.0,
                'receivables_days': 75,
                'payables_days': 80,
                'gross_margin': 0.30,
                'operating_margin': 0.10,
                'net_margin': 0.07
            },
            'servicios': {
                'name': 'Servicios',
                'liquidity': 1.3,
                'quick_ratio': 1.1,
                'debt_ratio': 0.45,
                'roe': 0.18,
                'roa': 0.10,
                'asset_turnover': 2.0,
                'inventory_turnover': 0,  # No inventory typically
                'receivables_days': 50,
                'payables_days': 60,
                'gross_margin': 0.40,
                'operating_margin': 0.15,
                'net_margin': 0.10
            },
            'construccion': {
                'name': 'Construcción',
                'liquidity': 1.4,
                'quick_ratio': 0.9,
                'debt_ratio': 0.65,
                'roe': 0.10,
                'roa': 0.04,
                'asset_turnover': 1.2,
                'inventory_turnover': 4.0,
                'receivables_days': 90,
                'payables_days': 100,
                'gross_margin': 0.20,
                'operating_margin': 0.06,
                'net_margin': 0.03
            },
            'default': {
                'name': 'General',
                'liquidity': 1.5,
                'quick_ratio': 1.0,
                'debt_ratio': 0.50,
                'roe': 0.12,
                'roa': 0.07,
                'asset_turnover': 1.8,
                'inventory_turnover': 6.0,
                'receivables_days': 60,
                'payables_days': 70,
                'gross_margin': 0.25,
                'operating_margin': 0.08,
                'net_margin': 0.05
            }
        }
    
    def calculate_financial_ratios(self, year: int) -> Dict:
        """Calculate comprehensive financial ratios"""
        from src.accounting_core import BalanceAccount, JournalEntry, AccountingPeriod
        from sqlalchemy.orm import sessionmaker
        
        Session = sessionmaker(bind=self.accounting.engine)
        session = Session()
        try:
            period = session.query(AccountingPeriod).filter_by(year=year).first()
            if not period:
                logger.warning(f"No data found for year {year}")
                return {}
            
            # Get key balances
            def get_balance(account_prefix: str) -> float:
                """Get total balance for accounts starting with prefix"""
                accounts = session.query(BalanceAccount).filter(
                    BalanceAccount.period_id == period.id,
                    BalanceAccount.account_code.like(f"{account_prefix}%")
                ).all()
                return sum(float(acc.saldo_final or 0) for acc in accounts)
            
            # Balance Sheet items
            activo_no_corriente = get_balance('2')  # Non-current assets
            existencias = get_balance('3')  # Inventory
            deudores = get_balance('43')  # Trade receivables
            tesoreria = get_balance('57')  # Cash
            activo_corriente = existencias + deudores + tesoreria + get_balance('54')  # Current assets
            total_activo = activo_no_corriente + activo_corriente
            
            patrimonio_neto = get_balance('1')  # Equity
            pasivo_no_corriente = get_balance('17')  # Non-current liabilities
            proveedores = get_balance('40')  # Trade payables
            pasivo_corriente = proveedores + get_balance('52') + get_balance('475')  # Current liabilities
            total_pasivo = pasivo_no_corriente + pasivo_corriente
            
            # Income Statement items
            ingresos_explotacion = abs(get_balance('70'))  # Revenue
            compras = abs(get_balance('60'))  # Purchases
            gastos_personal = abs(get_balance('64'))  # Personnel expenses
            otros_gastos = abs(get_balance('62')) + abs(get_balance('68'))  # Other expenses
            amortizaciones = abs(get_balance('68'))  # Depreciation
            
            resultado_explotacion = ingresos_explotacion - compras - gastos_personal - otros_gastos
            gastos_financieros = abs(get_balance('66'))  # Financial expenses
            resultado_antes_impuestos = resultado_explotacion - gastos_financieros
            impuesto_sociedades = abs(get_balance('630'))  # Income tax
            resultado_neto = resultado_antes_impuestos - impuesto_sociedades
            
            # Calculate ratios
            ratios = {}
            
            # Liquidity Ratios
            if pasivo_corriente > 0:
                ratios['ratio_liquidez'] = activo_corriente / pasivo_corriente
                ratios['ratio_tesoreria'] = (activo_corriente - existencias) / pasivo_corriente
                ratios['ratio_disponibilidad'] = tesoreria / pasivo_corriente
            else:
                ratios['ratio_liquidez'] = 0
                ratios['ratio_tesoreria'] = 0
                ratios['ratio_disponibilidad'] = 0
            
            # Working Capital
            ratios['fondo_maniobra'] = activo_corriente - pasivo_corriente
            
            # Solvency/Leverage Ratios
            if total_activo > 0:
                ratios['ratio_endeudamiento'] = total_pasivo / total_activo
                ratios['ratio_autonomia'] = patrimonio_neto / total_activo
            else:
                ratios['ratio_endeudamiento'] = 0
                ratios['ratio_autonomia'] = 0
            
            if patrimonio_neto > 0:
                ratios['ratio_apalancamiento'] = total_pasivo / patrimonio_neto
            else:
                ratios['ratio_apalancamiento'] = 0
            
            # Profitability Ratios
            if ingresos_explotacion > 0:
                ratios['margen_bruto'] = (ingresos_explotacion - compras) / ingresos_explotacion
                ratios['margen_explotacion'] = resultado_explotacion / ingresos_explotacion
                ratios['margen_neto'] = resultado_neto / ingresos_explotacion
            else:
                ratios['margen_bruto'] = 0
                ratios['margen_explotacion'] = 0
                ratios['margen_neto'] = 0
            
            if total_activo > 0:
                ratios['roa'] = resultado_neto / total_activo  # Return on Assets
            else:
                ratios['roa'] = 0
            
            if patrimonio_neto > 0:
                ratios['roe'] = resultado_neto / patrimonio_neto  # Return on Equity
            else:
                ratios['roe'] = 0
            
            # Activity/Efficiency Ratios
            if total_activo > 0:
                ratios['rotacion_activos'] = ingresos_explotacion / total_activo
            else:
                ratios['rotacion_activos'] = 0
            
            if existencias > 0:
                ratios['rotacion_existencias'] = compras / existencias
                ratios['dias_existencias'] = 365 / ratios['rotacion_existencias'] if ratios['rotacion_existencias'] > 0 else 0
            else:
                ratios['rotacion_existencias'] = 0
                ratios['dias_existencias'] = 0
            
            if deudores > 0:
                ratios['rotacion_clientes'] = ingresos_explotacion / deudores
                ratios['periodo_medio_cobro'] = 365 / ratios['rotacion_clientes'] if ratios['rotacion_clientes'] > 0 else 0
            else:
                ratios['rotacion_clientes'] = 0
                ratios['periodo_medio_cobro'] = 0
            
            if proveedores > 0:
                ratios['rotacion_proveedores'] = compras / proveedores
                ratios['periodo_medio_pago'] = 365 / ratios['rotacion_proveedores'] if ratios['rotacion_proveedores'] > 0 else 0
            else:
                ratios['rotacion_proveedores'] = 0
                ratios['periodo_medio_pago'] = 0
            
            # Store absolute values for reference
            ratios['_values'] = {
                'activo_corriente': activo_corriente,
                'activo_no_corriente': activo_no_corriente,
                'total_activo': total_activo,
                'pasivo_corriente': pasivo_corriente,
                'pasivo_no_corriente': pasivo_no_corriente,
                'total_pasivo': total_pasivo,
                'patrimonio_neto': patrimonio_neto,
                'ingresos_explotacion': ingresos_explotacion,
                'resultado_explotacion': resultado_explotacion,
                'resultado_neto': resultado_neto,
                'existencias': existencias,
                'deudores': deudores,
                'proveedores': proveedores,
                'tesoreria': tesoreria
            }
            
            return ratios
            
        finally:
            session.close()
    
    def compare_with_sector(self, year: int, sector: str = 'default') -> Dict:
        """Compare company ratios with sector benchmarks"""
        company_ratios = self.calculate_financial_ratios(year)
        
        if not company_ratios:
            return {}
        
        benchmarks = self.sector_benchmarks.get(sector, self.sector_benchmarks['default'])
        
        comparison = {
            'sector': benchmarks['name'],
            'year': year,
            'comparisons': []
        }
        
        # Map company ratios to benchmark keys
        ratio_mapping = {
            'ratio_liquidez': ('liquidity', 'Ratio de Liquidez'),
            'ratio_tesoreria': ('quick_ratio', 'Ratio de Tesorería (Quick Ratio)'),
            'ratio_endeudamiento': ('debt_ratio', 'Ratio de Endeudamiento'),
            'roe': ('roe', 'ROE (Return on Equity)'),
            'roa': ('roa', 'ROA (Return on Assets)'),
            'rotacion_activos': ('asset_turnover', 'Rotación de Activos'),
            'rotacion_existencias': ('inventory_turnover', 'Rotación de Existencias'),
            'periodo_medio_cobro': ('receivables_days', 'Periodo Medio de Cobro (días)'),
            'periodo_medio_pago': ('payables_days', 'Periodo Medio de Pago (días)'),
            'margen_bruto': ('gross_margin', 'Margen Bruto'),
            'margen_explotacion': ('operating_margin', 'Margen de Explotación'),
            'margen_neto': ('net_margin', 'Margen Neto')
        }
        
        for company_key, (benchmark_key, name) in ratio_mapping.items():
            if company_key in company_ratios and benchmark_key in benchmarks:
                company_value = company_ratios[company_key]
                benchmark_value = benchmarks[benchmark_key]
                
                if benchmark_value > 0:
                    deviation = ((company_value - benchmark_value) / benchmark_value) * 100
                else:
                    deviation = 0
                
                # Determine if deviation is favorable or unfavorable
                # Higher is better for: liquidity, margins, ROE, ROA
                # Lower is better for: debt ratio, collection/payment days
                favorable_higher = company_key in ['ratio_liquidez', 'ratio_tesoreria', 'roe', 'roa', 
                                                   'margen_bruto', 'margen_explotacion', 'margen_neto',
                                                   'rotacion_activos', 'rotacion_existencias']
                
                if favorable_higher:
                    status = 'Favorable' if company_value > benchmark_value else 'Desfavorable'
                else:
                    status = 'Favorable' if company_value < benchmark_value else 'Desfavorable'
                
                comparison['comparisons'].append({
                    'ratio': name,
                    'company_value': company_value,
                    'sector_value': benchmark_value,
                    'deviation_pct': deviation,
                    'status': status
                })
        
        return comparison
    
    def perform_trend_analysis(self, years: List[int]) -> Dict:
        """Perform trend analysis across multiple years"""
        trends = {
            'years': years,
            'ratios': {}
        }
        
        # Calculate ratios for each year
        for year in years:
            ratios = self.calculate_financial_ratios(year)
            if ratios:
                for key, value in ratios.items():
                    if key != '_values':
                        if key not in trends['ratios']:
                            trends['ratios'][key] = []
                        trends['ratios'][key].append(value)
        
        # Calculate trends
        trends['analysis'] = []
        for ratio_name, values in trends['ratios'].items():
            if len(values) >= 2:
                # Calculate percentage change
                initial = values[0]
                final = values[-1]
                
                if initial != 0:
                    change_pct = ((final - initial) / abs(initial)) * 100
                else:
                    change_pct = 0
                
                # Determine trend direction
                if change_pct > 5:
                    trend = 'Creciente'
                elif change_pct < -5:
                    trend = 'Decreciente'
                else:
                    trend = 'Estable'
                
                trends['analysis'].append({
                    'ratio': ratio_name,
                    'initial_value': initial,
                    'final_value': final,
                    'change_pct': change_pct,
                    'trend': trend,
                    'values': values
                })
        
        return trends
    
    def identify_unusual_fluctuations(self, year: int, threshold_pct: float = 10.0) -> List[Dict]:
        """
        Identify unusual fluctuations in account balances
        
        Args:
            year: Current year
            threshold_pct: Threshold percentage for identifying unusual changes
        
        Returns:
            List of accounts with unusual fluctuations
        """
        from src.accounting_core import BalanceAccount, AccountingPeriod
        from sqlalchemy.orm import sessionmaker
        
        Session = sessionmaker(bind=self.accounting.engine)
        session = Session()
        try:
            # Get current and prior year periods
            current_period = session.query(AccountingPeriod).filter_by(year=year).first()
            prior_period = session.query(AccountingPeriod).filter_by(year=year-1).first()
            
            if not current_period or not prior_period:
                logger.warning(f"Cannot compare years {year} and {year-1} - missing data")
                return []
            
            unusual_items = []
            
            # Get all accounts from current year
            current_accounts = session.query(BalanceAccount).filter_by(period_id=current_period.id).all()
            
            for current_acc in current_accounts:
                # Find corresponding prior year account
                prior_acc = session.query(BalanceAccount).filter_by(
                    period_id=prior_period.id,
                    account_code=current_acc.account_code
                ).first()
                
                if prior_acc:
                    current_balance = float(current_acc.saldo_final or 0)
                    prior_balance = float(prior_acc.saldo_final or 0)
                    
                    # Calculate change
                    if prior_balance != 0:
                        change_pct = ((current_balance - prior_balance) / abs(prior_balance)) * 100
                        
                        if abs(change_pct) > threshold_pct:
                            unusual_items.append({
                                'account_code': current_acc.account_code,
                                'account_name': current_acc.account_name,
                                'prior_balance': prior_balance,
                                'current_balance': current_balance,
                                'change_amount': current_balance - prior_balance,
                                'change_pct': change_pct
                            })
                    elif current_balance != 0:
                        # Account appeared with balance (new account or reactivated)
                        unusual_items.append({
                            'account_code': current_acc.account_code,
                            'account_name': current_acc.account_name,
                            'prior_balance': 0,
                            'current_balance': current_balance,
                            'change_amount': current_balance,
                            'change_pct': 999.99,  # Indicator of new/reactivated
                            'note': 'Cuenta nueva o reactivada'
                        })
            
            # Sort by absolute change percentage
            unusual_items.sort(key=lambda x: abs(x['change_pct']), reverse=True)
            
            return unusual_items
            
        finally:
            session.close()
    
    def generate_analytical_review_workpaper(self, year: int, sector: str = 'default',
                                            compare_years: List[int] = None) -> str:
        """Generate comprehensive analytical review working paper"""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.chart import LineChart, Reference
        
        wb = Workbook()
        
        # Sheet 1: Financial Ratios
        ws_ratios = wb.active
        ws_ratios.title = "Ratios Financieros"
        
        ratios = self.calculate_financial_ratios(year)
        
        ws_ratios['A1'] = "ANÁLISIS DE RATIOS FINANCIEROS"
        ws_ratios['A1'].font = Font(size=14, bold=True)
        ws_ratios['A2'] = f"Ejercicio: {year}"
        ws_ratios['A3'] = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        
        # Liquidity section
        row = 5
        ws_ratios[f'A{row}'] = "RATIOS DE LIQUIDEZ"
        ws_ratios[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        liquidity_ratios = [
            ('Ratio de Liquidez (Corriente)', 'ratio_liquidez', '> 1.5'),
            ('Ratio de Tesorería (Quick Ratio)', 'ratio_tesoreria', '> 1.0'),
            ('Ratio de Disponibilidad', 'ratio_disponibilidad', '> 0.3'),
            ('Fondo de Maniobra', 'fondo_maniobra', '> 0')
        ]
        
        for name, key, benchmark in liquidity_ratios:
            ws_ratios[f'A{row}'] = name
            ws_ratios[f'B{row}'] = ratios.get(key, 0)
            ws_ratios[f'C{row}'] = benchmark
            row += 1
        
        # Solvency section
        row += 1
        ws_ratios[f'A{row}'] = "RATIOS DE SOLVENCIA/ENDEUDAMIENTO"
        ws_ratios[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        solvency_ratios = [
            ('Ratio de Endeudamiento', 'ratio_endeudamiento', '< 0.60'),
            ('Ratio de Autonomía', 'ratio_autonomia', '> 0.40'),
            ('Ratio de Apalancamiento', 'ratio_apalancamiento', '< 1.5')
        ]
        
        for name, key, benchmark in solvency_ratios:
            ws_ratios[f'A{row}'] = name
            ws_ratios[f'B{row}'] = ratios.get(key, 0)
            ws_ratios[f'C{row}'] = benchmark
            row += 1
        
        # Profitability section
        row += 1
        ws_ratios[f'A{row}'] = "RATIOS DE RENTABILIDAD"
        ws_ratios[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        profitability_ratios = [
            ('Margen Bruto', 'margen_bruto', '> 0.25'),
            ('Margen de Explotación', 'margen_explotacion', '> 0.08'),
            ('Margen Neto', 'margen_neto', '> 0.05'),
            ('ROA (Rentabilidad sobre Activos)', 'roa', '> 0.07'),
            ('ROE (Rentabilidad sobre Patrimonio)', 'roe', '> 0.12')
        ]
        
        for name, key, benchmark in profitability_ratios:
            ws_ratios[f'A{row}'] = name
            ws_ratios[f'B{row}'] = ratios.get(key, 0)
            ws_ratios[f'C{row}'] = benchmark
            row += 1
        
        # Activity ratios
        row += 1
        ws_ratios[f'A{row}'] = "RATIOS DE ACTIVIDAD/EFICIENCIA"
        ws_ratios[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        activity_ratios = [
            ('Rotación de Activos', 'rotacion_activos', '> 1.5'),
            ('Rotación de Existencias', 'rotacion_existencias', '> 6.0'),
            ('Días de Existencias', 'dias_existencias', '< 60'),
            ('Periodo Medio de Cobro (días)', 'periodo_medio_cobro', '< 60'),
            ('Periodo Medio de Pago (días)', 'periodo_medio_pago', '60-90')
        ]
        
        for name, key, benchmark in activity_ratios:
            ws_ratios[f'A{row}'] = name
            ws_ratios[f'B{row}'] = ratios.get(key, 0)
            ws_ratios[f'C{row}'] = benchmark
            row += 1
        
        # Format columns
        ws_ratios.column_dimensions['A'].width = 40
        ws_ratios.column_dimensions['B'].width = 15
        ws_ratios.column_dimensions['C'].width = 15
        
        ws_ratios['B4'] = "Valor"
        ws_ratios['C4'] = "Referencia"
        ws_ratios['B4'].font = Font(bold=True)
        ws_ratios['C4'].font = Font(bold=True)
        
        # Sheet 2: Sector Comparison
        ws_sector = wb.create_sheet("Comparación Sector")
        comparison = self.compare_with_sector(year, sector)
        
        ws_sector['A1'] = "COMPARACIÓN CON EL SECTOR"
        ws_sector['A1'].font = Font(size=14, bold=True)
        ws_sector['A2'] = f"Sector: {comparison.get('sector', 'N/A')}"
        ws_sector['A3'] = f"Ejercicio: {year}"
        
        # Headers
        headers = ['Ratio', 'Empresa', 'Sector', 'Desviación %', 'Estado']
        for col, header in enumerate(headers, 1):
            cell = ws_sector.cell(5, col, header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        row = 6
        for comp in comparison.get('comparisons', []):
            ws_sector.cell(row, 1, comp['ratio'])
            ws_sector.cell(row, 2, round(comp['company_value'], 2))
            ws_sector.cell(row, 3, round(comp['sector_value'], 2))
            ws_sector.cell(row, 4, round(comp['deviation_pct'], 1))
            ws_sector.cell(row, 5, comp['status'])
            
            # Color code status
            if comp['status'] == 'Favorable':
                ws_sector.cell(row, 5).fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            else:
                ws_sector.cell(row, 5).fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            
            row += 1
        
        ws_sector.column_dimensions['A'].width = 40
        ws_sector.column_dimensions['B'].width = 12
        ws_sector.column_dimensions['C'].width = 12
        ws_sector.column_dimensions['D'].width = 15
        ws_sector.column_dimensions['E'].width = 15
        
        # Sheet 3: Unusual Fluctuations
        ws_unusual = wb.create_sheet("Variaciones Inusuales")
        unusual_items = self.identify_unusual_fluctuations(year)
        
        ws_unusual['A1'] = "VARIACIONES INUSUALES EN CUENTAS"
        ws_unusual['A1'].font = Font(size=14, bold=True)
        ws_unusual['A2'] = f"Comparación: {year-1} vs {year}"
        ws_unusual['A3'] = f"Umbral: >10% variación"
        
        headers = ['Cuenta', 'Descripción', f'Saldo {year-1}', f'Saldo {year}', 'Variación €', 'Variación %', 'Observaciones']
        for col, header in enumerate(headers, 1):
            cell = ws_unusual.cell(5, col, header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        row = 6
        for item in unusual_items[:50]:  # Top 50 unusual items
            ws_unusual.cell(row, 1, item['account_code'])
            ws_unusual.cell(row, 2, item['account_name'])
            ws_unusual.cell(row, 3, round(item['prior_balance'], 2))
            ws_unusual.cell(row, 4, round(item['current_balance'], 2))
            ws_unusual.cell(row, 5, round(item['change_amount'], 2))
            ws_unusual.cell(row, 6, round(item['change_pct'], 1))
            ws_unusual.cell(row, 7, item.get('note', ''))
            
            # Color code significant changes
            if abs(item['change_pct']) > 50:
                ws_unusual.cell(row, 6).fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            elif abs(item['change_pct']) > 25:
                ws_unusual.cell(row, 6).fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            
            row += 1
        
        ws_unusual.column_dimensions['A'].width = 10
        ws_unusual.column_dimensions['B'].width = 35
        ws_unusual.column_dimensions['C'].width = 15
        ws_unusual.column_dimensions['D'].width = 15
        ws_unusual.column_dimensions['E'].width = 15
        ws_unusual.column_dimensions['F'].width = 12
        ws_unusual.column_dimensions['G'].width = 25
        
        # Sheet 4: Trend Analysis (if multiple years provided)
        if compare_years and len(compare_years) > 1:
            ws_trend = wb.create_sheet("Análisis Tendencias")
            trends = self.perform_trend_analysis(compare_years)
            
            ws_trend['A1'] = "ANÁLISIS DE TENDENCIAS"
            ws_trend['A1'].font = Font(size=14, bold=True)
            ws_trend['A2'] = f"Ejercicios: {', '.join(map(str, compare_years))}"
            
            headers = ['Ratio', 'Valor Inicial', 'Valor Final', 'Variación %', 'Tendencia']
            for col, header in enumerate(headers, 1):
                cell = ws_trend.cell(5, col, header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.font = Font(color="FFFFFF", bold=True)
            
            row = 6
            for analysis in trends.get('analysis', []):
                ws_trend.cell(row, 1, analysis['ratio'])
                ws_trend.cell(row, 2, round(analysis['initial_value'], 2))
                ws_trend.cell(row, 3, round(analysis['final_value'], 2))
                ws_trend.cell(row, 4, round(analysis['change_pct'], 1))
                ws_trend.cell(row, 5, analysis['trend'])
                
                # Color code trends
                if analysis['trend'] == 'Creciente':
                    ws_trend.cell(row, 5).fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif analysis['trend'] == 'Decreciente':
                    ws_trend.cell(row, 5).fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                
                row += 1
            
            ws_trend.column_dimensions['A'].width = 30
            ws_trend.column_dimensions['B'].width = 15
            ws_trend.column_dimensions['C'].width = 15
            ws_trend.column_dimensions['D'].width = 15
            ws_trend.column_dimensions['E'].width = 15
        
        # Save workbook
        filename = f"PT_Revision_Analitica_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = f"{self.output_dir}/{filename}"
        wb.save(filepath)
        
        logger.info(f"Generated analytical review working paper: {filename}")
        return filepath
