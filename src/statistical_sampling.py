"""
Statistical Sampling Module
Implements random sampling for purchases and sales with documented selection methods
"""

import pandas as pd
import logging
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


class StatisticalSamplingGenerator:
    """Generates statistical samples for audit testing"""
    
    def __init__(self, config: Dict, accounting_processor):
        """Initialize sampling generator"""
        self.config = config
        self.accounting = accounting_processor
        self.logger = logging.getLogger(__name__)
        
        # Output directory
        self.output_dir = Path(config.get('working_papers', {}).get('output_dir', './papeles_trabajo'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Sampling methods
        self.sampling_methods = {
            'random': 'Muestreo Aleatorio Simple',
            'systematic': 'Muestreo Sistemático con Arranque Aleatorio',
            'stratified': 'Muestreo Estratificado',
            'monetary_unit': 'Muestreo de Unidades Monetarias (MUS)'
        }
    
    def generate_purchases_sample(self, year: int, sample_size: int = 25,
                                  method: str = 'random',
                                  materiality: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate random sample of purchases for testing
        
        Args:
            year: Audit year
            sample_size: Number of items to sample (default 25)
            method: Sampling method ('random', 'systematic', 'stratified', 'monetary_unit')
            materiality: Optional materiality threshold
            
        Returns:
            Dictionary with sample details and documentation
        """
        self.logger.info(f"Generating purchases sample for year {year}")
        
        # Get period
        period = self.accounting.session.query(
            self.accounting.AccountingPeriod
        ).filter_by(year=year).first()
        
        if not period:
            return {'error': f'Period {year} not found'}
        
        # Get purchase transactions from journal
        purchases = self.accounting.session.query(
            self.accounting.JournalEntry
        ).filter_by(period_id=period.id).filter(
            self.accounting.JournalEntry.account_code.like('60%')  # Purchases accounts
        ).order_by(self.accounting.JournalEntry.entry_date).all()
        
        if not purchases:
            return {'error': 'No purchase transactions found'}
        
        # Convert to DataFrame for easier manipulation
        purchases_data = []
        for i, entry in enumerate(purchases, start=1):
            purchases_data.append({
                'item_number': i,
                'entry_number': entry.entry_number,
                'date': entry.entry_date,
                'account_code': entry.account_code,
                'account_name': entry.account_name,
                'debit_amount': entry.debit_amount,
                'description': entry.description,
                'document_ref': entry.document_ref
            })
        
        df = pd.DataFrame(purchases_data)
        population_size = len(df)
        
        # Apply sampling method
        if method == 'random':
            sample_df = self._random_sampling(df, sample_size)
            selection_method = f"Muestreo Aleatorio Simple con generador de números aleatorios. Semilla: {random.randint(1000, 9999)}"
        
        elif method == 'systematic':
            sample_df = self._systematic_sampling(df, sample_size)
            interval = population_size // sample_size if sample_size > 0 else 0
            start_point = random.randint(1, interval) if interval > 0 else 1
            selection_method = f"Muestreo Sistemático. Intervalo: {interval}, Punto de arranque aleatorio: {start_point}"
        
        elif method == 'stratified':
            sample_df = self._stratified_sampling(df, sample_size, 'debit_amount')
            selection_method = "Muestreo Estratificado por importes (Alto/Medio/Bajo valor)"
        
        elif method == 'monetary_unit':
            sample_df = self._monetary_unit_sampling(df, sample_size, 'debit_amount', materiality)
            selection_method = f"Muestreo de Unidades Monetarias (MUS). Materialidad: {materiality:,.2f} €" if materiality else "Muestreo de Unidades Monetarias (MUS)"
        
        else:
            sample_df = self._random_sampling(df, sample_size)
            selection_method = "Muestreo Aleatorio Simple (método por defecto)"
        
        # Calculate coverage
        total_amount = df['debit_amount'].sum()
        sample_amount = sample_df['debit_amount'].sum()
        coverage_pct = (sample_amount / total_amount * 100) if total_amount > 0 else 0
        
        result = {
            'year': year,
            'transaction_type': 'Compras',
            'population_size': population_size,
            'sample_size': len(sample_df),
            'sampling_method': self.sampling_methods.get(method, 'Desconocido'),
            'selection_documentation': selection_method,
            'total_population_amount': total_amount,
            'sample_amount': sample_amount,
            'coverage_percentage': coverage_pct,
            'sample_items': sample_df.to_dict('records'),
            'sampling_date': datetime.now().isoformat(),
            'random_seed': random.randint(10000, 99999)  # For reproducibility
        }
        
        return result
    
    def generate_sales_sample(self, year: int, sample_size: int = 25,
                             method: str = 'random',
                             materiality: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate random sample of sales for testing
        
        Args:
            year: Audit year
            sample_size: Number of items to sample (default 25)
            method: Sampling method
            materiality: Optional materiality threshold
            
        Returns:
            Dictionary with sample details and documentation
        """
        self.logger.info(f"Generating sales sample for year {year}")
        
        # Get period
        period = self.accounting.session.query(
            self.accounting.AccountingPeriod
        ).filter_by(year=year).first()
        
        if not period:
            return {'error': f'Period {year} not found'}
        
        # Get sales transactions from journal
        sales = self.accounting.session.query(
            self.accounting.JournalEntry
        ).filter_by(period_id=period.id).filter(
            self.accounting.JournalEntry.account_code.like('70%')  # Sales accounts
        ).order_by(self.accounting.JournalEntry.entry_date).all()
        
        if not sales:
            return {'error': 'No sales transactions found'}
        
        # Convert to DataFrame
        sales_data = []
        for i, entry in enumerate(sales, start=1):
            sales_data.append({
                'item_number': i,
                'entry_number': entry.entry_number,
                'date': entry.entry_date,
                'account_code': entry.account_code,
                'account_name': entry.account_name,
                'credit_amount': entry.credit_amount,
                'description': entry.description,
                'document_ref': entry.document_ref
            })
        
        df = pd.DataFrame(sales_data)
        population_size = len(df)
        
        # Apply sampling method
        if method == 'random':
            sample_df = self._random_sampling(df, sample_size)
            selection_method = f"Muestreo Aleatorio Simple con generador de números aleatorios. Semilla: {random.randint(1000, 9999)}"
        
        elif method == 'systematic':
            sample_df = self._systematic_sampling(df, sample_size)
            interval = population_size // sample_size if sample_size > 0 else 0
            start_point = random.randint(1, interval) if interval > 0 else 1
            selection_method = f"Muestreo Sistemático. Intervalo: {interval}, Punto de arranque aleatorio: {start_point}"
        
        elif method == 'stratified':
            sample_df = self._stratified_sampling(df, sample_size, 'credit_amount')
            selection_method = "Muestreo Estratificado por importes (Alto/Medio/Bajo valor)"
        
        elif method == 'monetary_unit':
            sample_df = self._monetary_unit_sampling(df, sample_size, 'credit_amount', materiality)
            selection_method = f"Muestreo de Unidades Monetarias (MUS). Materialidad: {materiality:,.2f} €" if materiality else "Muestreo de Unidades Monetarias (MUS)"
        
        else:
            sample_df = self._random_sampling(df, sample_size)
            selection_method = "Muestreo Aleatorio Simple (método por defecto)"
        
        # Calculate coverage
        total_amount = df['credit_amount'].sum()
        sample_amount = sample_df['credit_amount'].sum()
        coverage_pct = (sample_amount / total_amount * 100) if total_amount > 0 else 0
        
        result = {
            'year': year,
            'transaction_type': 'Ventas',
            'population_size': population_size,
            'sample_size': len(sample_df),
            'sampling_method': self.sampling_methods.get(method, 'Desconocido'),
            'selection_documentation': selection_method,
            'total_population_amount': total_amount,
            'sample_amount': sample_amount,
            'coverage_percentage': coverage_pct,
            'sample_items': sample_df.to_dict('records'),
            'sampling_date': datetime.now().isoformat(),
            'random_seed': random.randint(10000, 99999)
        }
        
        return result
    
    def _random_sampling(self, df: pd.DataFrame, sample_size: int) -> pd.DataFrame:
        """Simple random sampling"""
        if len(df) <= sample_size:
            return df
        return df.sample(n=sample_size, random_state=random.randint(1, 10000))
    
    def _systematic_sampling(self, df: pd.DataFrame, sample_size: int) -> pd.DataFrame:
        """Systematic sampling with random start"""
        population_size = len(df)
        if population_size <= sample_size:
            return df
        
        interval = population_size // sample_size
        start = random.randint(0, interval - 1)
        
        indices = [start + i * interval for i in range(sample_size) if start + i * interval < population_size]
        
        return df.iloc[indices]
    
    def _stratified_sampling(self, df: pd.DataFrame, sample_size: int, amount_column: str) -> pd.DataFrame:
        """Stratified sampling based on amount ranges"""
        if len(df) <= sample_size:
            return df
        
        # Define strata based on amount
        df_copy = df.copy()
        quantiles = df_copy[amount_column].quantile([0.33, 0.67])
        
        df_copy['stratum'] = pd.cut(
            df_copy[amount_column],
            bins=[-np.inf, quantiles.iloc[0], quantiles.iloc[1], np.inf],
            labels=['Low', 'Medium', 'High']
        )
        
        # Proportional allocation
        samples_per_stratum = (df_copy['stratum'].value_counts(normalize=True) * sample_size).round().astype(int)
        
        sampled_dfs = []
        for stratum, count in samples_per_stratum.items():
            stratum_df = df_copy[df_copy['stratum'] == stratum]
            if len(stratum_df) > 0:
                n_sample = min(count, len(stratum_df))
                sampled_dfs.append(stratum_df.sample(n=n_sample, random_state=random.randint(1, 10000)))
        
        result = pd.concat(sampled_dfs) if sampled_dfs else df_copy.head(sample_size)
        return result.drop(columns=['stratum'])
    
    def _monetary_unit_sampling(self, df: pd.DataFrame, sample_size: int,
                                amount_column: str, materiality: Optional[float]) -> pd.DataFrame:
        """Monetary Unit Sampling (MUS) - probability proportional to size"""
        if len(df) <= sample_size:
            return df
        
        df_copy = df.copy()
        
        # Calculate cumulative amounts
        df_copy['cumulative'] = df_copy[amount_column].cumsum()
        total_amount = df_copy[amount_column].sum()
        
        # Calculate sampling interval
        interval = total_amount / sample_size if sample_size > 0 else total_amount
        
        # Random start
        start = random.uniform(0, interval)
        
        # Select items
        selected_indices = []
        current = start
        
        while current <= total_amount and len(selected_indices) < sample_size:
            # Find item that contains this cumulative point
            idx = df_copy[df_copy['cumulative'] >= current].index[0]
            if idx not in selected_indices:
                selected_indices.append(idx)
            current += interval
        
        return df_copy.loc[selected_indices].drop(columns=['cumulative'])
    
    def generate_sampling_working_paper(self, purchases_sample: Dict[str, Any],
                                       sales_sample: Dict[str, Any]) -> Path:
        """Generate Excel working paper with both purchase and sales samples"""
        
        self.logger.info("Generating sampling working paper")
        
        wb = Workbook()
        
        # Sheet 1: Summary
        ws_summary = wb.active
        ws_summary.title = "Resumen"
        
        self._create_summary_sheet(ws_summary, purchases_sample, sales_sample)
        
        # Sheet 2: Purchases sample
        ws_purchases = wb.create_sheet("Muestra Compras")
        self._create_sample_sheet(ws_purchases, purchases_sample)
        
        # Sheet 3: Sales sample
        ws_sales = wb.create_sheet("Muestra Ventas")
        self._create_sample_sheet(ws_sales, sales_sample)
        
        # Save
        year = purchases_sample.get('year', datetime.now().year)
        filename = f"PT_Muestreo_Compras_Ventas_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        output_path = self.output_dir / filename
        wb.save(output_path)
        
        self.logger.info(f"Sampling working paper saved to {output_path}")
        
        return output_path
    
    def _create_summary_sheet(self, ws, purchases_sample: Dict, sales_sample: Dict):
        """Create summary sheet"""
        
        # Header
        ws['A1'] = 'PAPEL DE TRABAJO - MUESTREO ESTADÍSTICO DE COMPRAS Y VENTAS'
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:F1')
        
        ws['A3'] = 'Ejercicio:'
        ws['B3'] = purchases_sample.get('year', '')
        ws['A4'] = 'Fecha:'
        ws['B4'] = datetime.now().strftime('%d/%m/%Y')
        
        # Purchases summary
        ws['A6'] = 'COMPRAS'
        ws['A6'].font = Font(size=12, bold=True)
        
        ws['A7'] = 'Tamaño de la población:'
        ws['B7'] = purchases_sample.get('population_size', 0)
        ws['A8'] = 'Tamaño de la muestra:'
        ws['B8'] = purchases_sample.get('sample_size', 0)
        ws['A9'] = 'Método de muestreo:'
        ws['B9'] = purchases_sample.get('sampling_method', '')
        ws['A10'] = 'Importe total población:'
        ws['B10'] = purchases_sample.get('total_population_amount', 0)
        ws['B10'].number_format = '#,##0.00 €'
        ws['A11'] = 'Importe muestra:'
        ws['B11'] = purchases_sample.get('sample_amount', 0)
        ws['B11'].number_format = '#,##0.00 €'
        ws['A12'] = 'Cobertura:'
        ws['B12'] = f"{purchases_sample.get('coverage_percentage', 0):.2f}%"
        
        ws['A14'] = 'Método de selección:'
        ws['B14'] = purchases_sample.get('selection_documentation', '')
        ws.merge_cells('B14:F14')
        ws['B14'].alignment = Alignment(wrap_text=True)
        
        # Sales summary
        ws['A17'] = 'VENTAS'
        ws['A17'].font = Font(size=12, bold=True)
        
        ws['A18'] = 'Tamaño de la población:'
        ws['B18'] = sales_sample.get('population_size', 0)
        ws['A19'] = 'Tamaño de la muestra:'
        ws['B19'] = sales_sample.get('sample_size', 0)
        ws['A20'] = 'Método de muestreo:'
        ws['B20'] = sales_sample.get('sampling_method', '')
        ws['A21'] = 'Importe total población:'
        ws['B21'] = sales_sample.get('total_population_amount', 0)
        ws['B21'].number_format = '#,##0.00 €'
        ws['A22'] = 'Importe muestra:'
        ws['B22'] = sales_sample.get('sample_amount', 0)
        ws['B22'].number_format = '#,##0.00 €'
        ws['A23'] = 'Cobertura:'
        ws['B23'] = f"{sales_sample.get('coverage_percentage', 0):.2f}%"
        
        ws['A25'] = 'Método de selección:'
        ws['B25'] = sales_sample.get('selection_documentation', '')
        ws.merge_cells('B25:F25')
        ws['B25'].alignment = Alignment(wrap_text=True)
        
        # Adjust columns
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 40
        for col in ['C', 'D', 'E', 'F']:
            ws.column_dimensions[col].width = 15
    
    def _create_sample_sheet(self, ws, sample_data: Dict):
        """Create individual sample sheet"""
        
        # Header
        transaction_type = sample_data.get('transaction_type', 'Transacciones')
        ws['A1'] = f'MUESTRA DE {transaction_type.upper()}'
        ws['A1'].font = Font(size=12, bold=True)
        ws.merge_cells('A1:I1')
        
        # Column headers
        headers = ['Nº Muestra', 'Nº Item Población', 'Nº Asiento', 'Fecha', 
                   'Cuenta', 'Descripción', 'Importe', 'Referencia Doc', 'Verificado']
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(3, col, header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            cell.border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        
        # Sample items
        items = sample_data.get('sample_items', [])
        for i, item in enumerate(items, start=4):
            ws.cell(i, 1, i - 3)  # Sample number
            ws.cell(i, 2, item.get('item_number', ''))
            ws.cell(i, 3, item.get('entry_number', ''))
            
            date_val = item.get('date')
            if date_val:
                ws.cell(i, 4, date_val).number_format = 'dd/mm/yyyy'
            
            ws.cell(i, 5, item.get('account_code', ''))
            ws.cell(i, 6, str(item.get('description', ''))[:50])
            
            # Amount (debit for purchases, credit for sales)
            amount = item.get('debit_amount') or item.get('credit_amount', 0)
            ws.cell(i, 7, amount).number_format = '#,##0.00'
            
            ws.cell(i, 8, item.get('document_ref', ''))
            ws.cell(i, 9, '☐')  # Checkbox for verification
        
        # Adjust columns
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 40
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 20
        ws.column_dimensions['I'].width = 12
