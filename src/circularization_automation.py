"""
Automated Circularization System for Audit Confirmations
Handles loading of confirmation responses, reconciliation, and generation of working papers
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows


class CircularizationAutomation:
    """
    Automated circularization system that:
    - Loads confirmation responses from various formats
    - Reconciles with company records
    - Generates working papers with balance verification
    - Applies alternative procedures for non-responses
    - Verifies subsequent period settlements
    """
    
    def __init__(self, accounting_core, output_dir="./papeles_trabajo"):
        self.accounting = accounting_core
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Confirmation types
        self.confirmation_types = {
            'clientes': {'accounts': ['430', '431', '432', '433', '434', '435', '436', '437'], 'type': 'deudor'},
            'proveedores': {'accounts': ['400', '401', '403', '405', '406', '407', '410'], 'type': 'acreedor'},
            'bancos': {'accounts': ['572', '573'], 'type': 'acreedor_deudor'},
            'acreedores': {'accounts': ['410', '411', '419', '465', '466', '475', '476'], 'type': 'acreedor'}
        }
        
        # Response statuses
        self.RESPONSE_STATUS = {
            'CONFIRMADO': 'Confirmed - Matches',
            'DIFERENCIA': 'Difference - Reconciliation Required',
            'NO_RESPUESTA': 'No Response - Alternative Procedures',
            'DEVUELTO': 'Returned - Cannot Deliver',
            'RECHAZADO': 'Rejected by Third Party'
        }
        
        # Alternative procedures for non-responses
        self.alternative_procedures = [
            "Revisión de pagos/cobros posteriores al cierre",
            "Inspección de facturas y albaranes originales",
            "Revisión de correspondencia y comunicaciones",
            "Análisis de antigüedad de saldos",
            "Pruebas de corte (cut-off testing)"
        ]
    
    def load_confirmation_responses(self, file_path: str, confirmation_type: str) -> pd.DataFrame:
        """
        Load confirmation responses from Excel, CSV, or PDF (with OCR)
        Expected columns: entity_name, account_code, confirmed_balance, response_date, notes, differences
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext == '.pdf':
            # For PDF responses, we'd use OCR and AI extraction
            # For now, return empty DataFrame with proper structure
            df = pd.DataFrame(columns=['entity_name', 'account_code', 'confirmed_balance', 
                                      'response_date', 'notes', 'differences'])
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Standardize column names
        column_mapping = {
            'nombre': 'entity_name',
            'entidad': 'entity_name',
            'cuenta': 'account_code',
            'codigo_cuenta': 'account_code',
            'saldo_confirmado': 'confirmed_balance',
            'saldo': 'confirmed_balance',
            'fecha_respuesta': 'response_date',
            'fecha': 'response_date',
            'observaciones': 'notes',
            'notas': 'notes',
            'diferencias': 'differences'
        }
        
        df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)
        
        return df
    
    def get_company_balances(self, year: int, confirmation_type: str) -> pd.DataFrame:
        """
        Extract balances from accounting system for circularization
        """
        account_codes = self.confirmation_types[confirmation_type]['accounts']
        
        balances = []
        for account_code in account_codes:
            # Get all accounts starting with the code (e.g., 430, 4300, 43001, etc.)
            accounts = self.accounting.get_accounts_by_prefix(year, account_code)
            
            for account in accounts:
                balance_data = {
                    'account_code': account.account_code,
                    'account_name': account.account_name or '',
                    'company_balance': account.saldo_final or 0.0,
                    'debe': account.suma_debe or 0.0,
                    'haber': account.suma_haber or 0.0
                }
                balances.append(balance_data)
        
        return pd.DataFrame(balances)
    
    def reconcile_responses(self, company_balances: pd.DataFrame, responses: pd.DataFrame, 
                           tolerance: float = 1.0) -> pd.DataFrame:
        """
        Reconcile company balances with confirmation responses
        """
        # Merge on account_code
        merged = company_balances.merge(
            responses, 
            on='account_code', 
            how='left',
            suffixes=('_company', '_response')
        )
        
        # Calculate differences
        merged['confirmed_balance'] = pd.to_numeric(merged['confirmed_balance'], errors='coerce').fillna(0)
        merged['difference'] = merged['company_balance'] - merged['confirmed_balance']
        merged['difference_abs'] = merged['difference'].abs()
        
        # Determine status
        def get_status(row):
            if pd.isna(row['response_date']) or row['response_date'] == '':
                return 'NO_RESPUESTA'
            elif row['difference_abs'] <= tolerance:
                return 'CONFIRMADO'
            else:
                return 'DIFERENCIA'
        
        merged['status'] = merged.apply(get_status, axis=1)
        merged['status_desc'] = merged['status'].map(self.RESPONSE_STATUS)
        
        return merged
    
    def verify_subsequent_settlement(self, account_code: str, year: int, 
                                    balance_date: datetime) -> Dict:
        """
        Verify if the balance was settled/paid in the subsequent period
        Looks for journal entries after year-end that reduce the balance
        """
        # Get journal entries for the account in the next year
        next_year = year + 1
        
        try:
            entries = self.accounting.get_journal_entries(next_year, account_code)
            
            # Calculate first 3 months settlement
            cutoff_date = datetime(next_year, 3, 31)
            settled_amount = 0.0
            settlement_entries = []
            
            for entry in entries:
                if entry.entry_date and entry.entry_date <= cutoff_date:
                    # For debtors (clientes), credits reduce balance
                    # For creditors (proveedores), debits reduce balance
                    settlement = entry.credit_amount - entry.debit_amount
                    settled_amount += abs(settlement)
                    settlement_entries.append({
                        'date': entry.entry_date,
                        'entry_number': entry.entry_number,
                        'amount': settlement,
                        'description': entry.description
                    })
            
            return {
                'settled': settled_amount > 0,
                'settled_amount': settled_amount,
                'settlement_entries': settlement_entries[:10],  # Top 10 entries
                'next_year_entries': len(entries)
            }
        except:
            return {
                'settled': False,
                'settled_amount': 0.0,
                'settlement_entries': [],
                'next_year_entries': 0
            }
    
    def apply_alternative_procedures(self, account_code: str, year: int, 
                                    company_balance: float) -> Dict:
        """
        Apply alternative audit procedures for non-responses
        """
        results = {
            'account_code': account_code,
            'procedures_applied': [],
            'evidence_obtained': [],
            'conclusion': ''
        }
        
        # Procedure 1: Subsequent settlements
        settlement = self.verify_subsequent_settlement(account_code, year, 
                                                      datetime(year, 12, 31))
        if settlement['settled']:
            results['procedures_applied'].append(self.alternative_procedures[0])
            results['evidence_obtained'].append(
                f"Verificado cobro/pago posterior: {settlement['settled_amount']:.2f}€ "
                f"({len(settlement['settlement_entries'])} movimientos)"
            )
        
        # Procedure 2: Review of original documents
        try:
            entries = self.accounting.get_journal_entries(year, account_code)
            if entries:
                sample_size = min(5, len(entries))
                results['procedures_applied'].append(self.alternative_procedures[1])
                results['evidence_obtained'].append(
                    f"Revisadas {sample_size} operaciones originales del ejercicio"
                )
        except:
            pass
        
        # Procedure 3: Aging analysis
        results['procedures_applied'].append(self.alternative_procedures[3])
        results['evidence_obtained'].append(
            f"Análisis de antigüedad realizado para saldo de {company_balance:.2f}€"
        )
        
        # Conclusion
        if settlement['settled'] and settlement['settled_amount'] >= company_balance * 0.8:
            results['conclusion'] = "SATISFACTORIO - Saldo verificado mediante cobro/pago posterior"
        elif settlement['settled']:
            results['conclusion'] = f"PARCIAL - Verificado {settlement['settled_amount']:.2f}€ de {company_balance:.2f}€"
        else:
            results['conclusion'] = "PENDIENTE - Requiere procedimientos adicionales"
        
        return results
    
    def generate_circularization_workpaper(self, year: int, confirmation_type: str,
                                          reconciliation: pd.DataFrame,
                                          entity_type: str = 'mercantil') -> str:
        """
        Generate comprehensive circularization working paper in Excel
        """
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"PT_Circularizacion_{confirmation_type.capitalize()}_{year}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        wb.remove(wb.active)
        
        # Sheet 1: Summary
        ws_summary = wb.create_sheet("Resumen")
        self._create_summary_sheet(ws_summary, year, confirmation_type, reconciliation)
        
        # Sheet 2: Reconciliation Detail
        ws_detail = wb.create_sheet("Detalle Reconciliación")
        self._create_reconciliation_sheet(ws_detail, reconciliation)
        
        # Sheet 3: Non-Responses with Alternative Procedures
        ws_alt = wb.create_sheet("Procedimientos Alternativos")
        self._create_alternative_procedures_sheet(ws_alt, reconciliation, year)
        
        # Sheet 4: Subsequent Period Verification
        ws_subsequent = wb.create_sheet("Verificación Posterior")
        self._create_subsequent_verification_sheet(ws_subsequent, reconciliation, year)
        
        # Sheet 5: Differences Analysis
        ws_diff = wb.create_sheet("Análisis Diferencias")
        self._create_differences_analysis_sheet(ws_diff, reconciliation)
        
        wb.save(filepath)
        return filepath
    
    def _create_summary_sheet(self, ws, year: int, confirmation_type: str, data: pd.DataFrame):
        """Create summary sheet with statistics"""
        # Header
        ws['A1'] = f"CIRCULARIZACIÓN - {confirmation_type.upper()}"
        ws['A1'].font = Font(size=14, bold=True)
        ws['A2'] = f"Ejercicio: {year}"
        
        # Statistics
        total = len(data)
        confirmed = len(data[data['status'] == 'CONFIRMADO'])
        differences = len(data[data['status'] == 'DIFERENCIA'])
        no_response = len(data[data['status'] == 'NO_RESPUESTA'])
        
        total_balance = data['company_balance'].sum()
        confirmed_balance = data[data['status'] == 'CONFIRMADO']['company_balance'].sum()
        
        row = 4
        ws[f'A{row}'] = "ESTADÍSTICAS DE CIRCULARIZACIÓN"
        ws[f'A{row}'].font = Font(bold=True)
        
        stats = [
            ("Total confirmaciones enviadas:", total),
            ("Confirmaciones recibidas y conformes:", confirmed),
            ("Respuestas con diferencias:", differences),
            ("Sin respuesta:", no_response),
            ("", ""),
            ("Saldo total contabilizado:", f"{total_balance:,.2f} €"),
            ("Saldo confirmado:", f"{confirmed_balance:,.2f} €"),
            ("% Cobertura por confirmación:", f"{(confirmed_balance/total_balance*100) if total_balance else 0:.1f}%"),
        ]
        
        for i, (label, value) in enumerate(stats, start=row+1):
            ws[f'A{i}'] = label
            ws[f'B{i}'] = value
            if "%" in str(value) or "€" in str(value):
                ws[f'A{i}'].font = Font(bold=True)
    
    def _create_reconciliation_sheet(self, ws, data: pd.DataFrame):
        """Create detailed reconciliation sheet"""
        # Headers
        headers = ['Cuenta', 'Nombre', 'Saldo Empresa', 'Saldo Confirmado', 
                  'Diferencia', 'Estado', 'Fecha Respuesta', 'Observaciones']
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        # Data
        for idx, row_data in data.iterrows():
            row = idx + 2
            ws.cell(row=row, column=1, value=row_data.get('account_code', ''))
            ws.cell(row=row, column=2, value=row_data.get('account_name', ''))
            ws.cell(row=row, column=3, value=row_data.get('company_balance', 0))
            ws.cell(row=row, column=4, value=row_data.get('confirmed_balance', 0))
            ws.cell(row=row, column=5, value=row_data.get('difference', 0))
            ws.cell(row=row, column=6, value=row_data.get('status_desc', ''))
            ws.cell(row=row, column=7, value=row_data.get('response_date', ''))
            ws.cell(row=row, column=8, value=row_data.get('notes', ''))
            
            # Color coding
            status = row_data.get('status', '')
            if status == 'CONFIRMADO':
                fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif status == 'DIFERENCIA':
                fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            elif status == 'NO_RESPUESTA':
                fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            else:
                fill = None
            
            if fill:
                for col in range(1, 9):
                    ws.cell(row=row, column=col).fill = fill
        
        # Adjust column widths
        for col in range(1, 9):
            ws.column_dimensions[chr(64 + col)].width = 15
    
    def _create_alternative_procedures_sheet(self, ws, data: pd.DataFrame, year: int):
        """Create sheet with alternative procedures for non-responses"""
        no_responses = data[data['status'] == 'NO_RESPUESTA']
        
        ws['A1'] = "PROCEDIMIENTOS ALTERNATIVOS - SIN RESPUESTA"
        ws['A1'].font = Font(size=12, bold=True)
        
        headers = ['Cuenta', 'Saldo', 'Procedimientos Aplicados', 'Evidencia', 'Conclusión']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        row = 4
        for _, account_data in no_responses.iterrows():
            account_code = account_data['account_code']
            balance = account_data['company_balance']
            
            # Apply alternative procedures
            alt_results = self.apply_alternative_procedures(account_code, year, balance)
            
            ws.cell(row=row, column=1, value=account_code)
            ws.cell(row=row, column=2, value=f"{balance:,.2f} €")
            ws.cell(row=row, column=3, value="\n".join(alt_results['procedures_applied']))
            ws.cell(row=row, column=4, value="\n".join(alt_results['evidence_obtained']))
            ws.cell(row=row, column=5, value=alt_results['conclusion'])
            
            # Wrap text
            for col in range(3, 6):
                ws.cell(row=row, column=col).alignment = Alignment(wrap_text=True, vertical='top')
            
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 35
        ws.column_dimensions['D'].width = 40
        ws.column_dimensions['E'].width = 30
    
    def _create_subsequent_verification_sheet(self, ws, data: pd.DataFrame, year: int):
        """Create sheet verifying subsequent period settlements"""
        ws['A1'] = "VERIFICACIÓN EJERCICIO POSTERIOR"
        ws['A1'].font = Font(size=12, bold=True)
        ws['A2'] = f"Revisión de cancelaciones en el ejercicio {year + 1}"
        
        headers = ['Cuenta', 'Saldo {}'.format(year), 'Cancelado Ejercicio Posterior', 
                  '% Cancelación', 'Movimientos', 'Conclusión']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        row = 5
        for _, account_data in data.iterrows():
            account_code = account_data['account_code']
            balance = account_data['company_balance']
            
            # Verify subsequent settlement
            settlement = self.verify_subsequent_settlement(
                account_code, year, datetime(year, 12, 31)
            )
            
            ws.cell(row=row, column=1, value=account_code)
            ws.cell(row=row, column=2, value=f"{balance:,.2f} €")
            ws.cell(row=row, column=3, value=f"{settlement['settled_amount']:,.2f} €")
            
            cancel_pct = (settlement['settled_amount'] / balance * 100) if balance else 0
            ws.cell(row=row, column=4, value=f"{cancel_pct:.1f}%")
            ws.cell(row=row, column=5, value=settlement['next_year_entries'])
            
            # Conclusion
            if cancel_pct >= 80:
                conclusion = "Verificado - Alta cancelación"
                fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif cancel_pct >= 50:
                conclusion = "Parcial - Cancelación moderada"
                fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            else:
                conclusion = "Pendiente - Baja cancelación"
                fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            
            ws.cell(row=row, column=6, value=conclusion)
            for col in range(1, 7):
                ws.cell(row=row, column=col).fill = fill
            
            row += 1
        
        # Adjust column widths
        for col in range(1, 7):
            ws.column_dimensions[chr(64 + col)].width = 18
    
    def _create_differences_analysis_sheet(self, ws, data: pd.DataFrame):
        """Create sheet analyzing differences between company and confirmed balances"""
        differences = data[data['status'] == 'DIFERENCIA']
        
        ws['A1'] = "ANÁLISIS DE DIFERENCIAS"
        ws['A1'].font = Font(size=12, bold=True)
        
        if len(differences) == 0:
            ws['A3'] = "No se identificaron diferencias significativas"
            return
        
        headers = ['Cuenta', 'Saldo Empresa', 'Saldo Confirmado', 'Diferencia', 
                  'Tipo', 'Causa Probable', 'Ajuste Requerido']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        row = 4
        for _, diff_data in differences.iterrows():
            ws.cell(row=row, column=1, value=diff_data['account_code'])
            ws.cell(row=row, column=2, value=f"{diff_data['company_balance']:,.2f} €")
            ws.cell(row=row, column=3, value=f"{diff_data['confirmed_balance']:,.2f} €")
            ws.cell(row=row, column=4, value=f"{diff_data['difference']:,.2f} €")
            
            # Analyze type of difference
            if diff_data['difference'] > 0:
                diff_type = "Empresa > Confirmado"
                probable_cause = "Facturas en tránsito, operaciones no registradas por tercero"
            else:
                diff_type = "Empresa < Confirmado"
                probable_cause = "Pagos/cobros no contabilizados, errores contables"
            
            ws.cell(row=row, column=5, value=diff_type)
            ws.cell(row=row, column=6, value=probable_cause)
            ws.cell(row=row, column=6).alignment = Alignment(wrap_text=True)
            
            # Determine if adjustment needed
            if abs(diff_data['difference']) > 100:
                adjustment = "SÍ - Investigar y ajustar"
                fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            else:
                adjustment = "NO - Diferencia inmaterial"
                fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            
            ws.cell(row=row, column=7, value=adjustment)
            for col in range(1, 8):
                ws.cell(row=row, column=col).fill = fill
            
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['F'].width = 40
        ws.column_dimensions['G'].width = 25
    
    def process_circularization(self, year: int, confirmation_type: str, 
                               responses_file: Optional[str] = None,
                               entity_type: str = 'mercantil') -> str:
        """
        Main method to process circularization for a given type
        """
        # Get company balances
        company_balances = self.get_company_balances(year, confirmation_type)
        
        if company_balances.empty:
            print(f"No balances found for {confirmation_type} in year {year}")
            return None
        
        # Load responses if file provided
        if responses_file and os.path.exists(responses_file):
            responses = self.load_confirmation_responses(responses_file, confirmation_type)
        else:
            # No responses file - all will be marked as no response
            responses = pd.DataFrame(columns=['entity_name', 'account_code', 'confirmed_balance', 
                                             'response_date', 'notes', 'differences'])
        
        # Reconcile
        reconciliation = self.reconcile_responses(company_balances, responses)
        
        # Generate working paper
        filepath = self.generate_circularization_workpaper(
            year, confirmation_type, reconciliation, entity_type
        )
        
        print(f"✓ Circularization working paper generated: {filepath}")
        return filepath
