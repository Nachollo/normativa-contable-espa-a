"""
Accounting Core Module
Handles balance sheets (balances de sumas y saldos) and general ledger (diarios)
These are the foundation documents for the entire audit process
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
import re
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import openpyxl
from openpyxl import load_workbook

Base = declarative_base()


class AccountingPeriod(Base):
    """Represents an accounting period/exercise"""
    __tablename__ = 'accounting_periods'
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    company_name = Column(String(200))
    company_cif = Column(String(20))
    start_date = Column(Date)
    end_date = Column(Date)
    is_current_audit = Column(Integer, default=0)
    created_at = Column(Date, default=datetime.now)
    
    # Relationships
    balances = relationship("BalanceAccount", back_populates="period")
    journal_entries = relationship("JournalEntry", back_populates="period")


class BalanceAccount(Base):
    """Balance de Sumas y Saldos - Account level detail"""
    __tablename__ = 'balance_accounts'
    
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey('accounting_periods.id'))
    
    # Account identification
    account_code = Column(String(20), nullable=False, index=True)
    account_name = Column(String(500))
    account_level = Column(Integer)  # Number of digits (4, 5, 6, etc.)
    parent_account = Column(String(20))
    
    # Sumas (totals)
    suma_debe = Column(Float, default=0.0)
    suma_haber = Column(Float, default=0.0)
    
    # Saldos (balances)
    saldo_deudor = Column(Float, default=0.0)
    saldo_acreedor = Column(Float, default=0.0)
    saldo_final = Column(Float, default=0.0)
    
    # Additional fields
    saldo_inicial = Column(Float, default=0.0)
    is_debit_nature = Column(Integer, default=1)
    
    # Metadata
    source_file = Column(String(500))
    import_date = Column(Date, default=datetime.now)
    
    # Relationships
    period = relationship("AccountingPeriod", back_populates="balances")


class JournalEntry(Base):
    """General Ledger Entry (Diario)"""
    __tablename__ = 'journal_entries'
    
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey('accounting_periods.id'))
    
    # Entry identification
    entry_number = Column(String(50), index=True)
    entry_date = Column(Date, nullable=False, index=True)
    posting_date = Column(Date)
    
    # Account details
    account_code = Column(String(20), nullable=False, index=True)
    account_name = Column(String(500))
    
    # Amounts
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    
    # Description and reference
    description = Column(Text)
    document_ref = Column(String(200))
    document_type = Column(String(100))
    
    # Additional fields
    cost_center = Column(String(100))
    analytical_account = Column(String(100))
    currency = Column(String(10), default='EUR')
    
    # Metadata
    source_file = Column(String(500))
    import_date = Column(Date, default=datetime.now)
    
    # Relationships
    period = relationship("AccountingPeriod", back_populates="journal_entries")


class AccountingCoreProcessor:
    """Processes balance sheets and general ledgers as foundation for audit"""
    
    def __init__(self, config: Dict):
        """Initialize accounting core processor"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database setup
        db_path = config.get('database', {}).get('path', 'accounting_core.db')
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Configuration
        self.min_account_digits = config.get('accounting', {}).get('min_account_digits', 4)
        self.max_detail_level = config.get('accounting', {}).get('max_detail_level', 10)
        self.required_exercises = config.get('accounting', {}).get('required_exercises', 3)
        
        # Excel column mappings (flexible detection)
        self.balance_columns = {
            'account_code': ['cuenta', 'codigo', 'code', 'nº cuenta', 'num cuenta'],
            'account_name': ['nombre', 'descripcion', 'description', 'denominacion'],
            'suma_debe': ['suma debe', 'debe', 'debit', 'cargo', 'cargos'],
            'suma_haber': ['suma haber', 'haber', 'credit', 'abono', 'abonos'],
            'saldo_deudor': ['saldo deudor', 'saldo debe', 'deudor'],
            'saldo_acreedor': ['saldo acreedor', 'saldo haber', 'acreedor'],
            'saldo_inicial': ['saldo inicial', 'inicial', 'apertura']
        }
        
        self.journal_columns = {
            'entry_number': ['asiento', 'numero asiento', 'entry', 'num'],
            'entry_date': ['fecha', 'date', 'fecha asiento'],
            'account_code': ['cuenta', 'codigo', 'code'],
            'account_name': ['nombre', 'descripcion', 'concepto cuenta'],
            'debit_amount': ['debe', 'debit', 'cargo'],
            'credit_amount': ['haber', 'credit', 'abono'],
            'description': ['concepto', 'descripcion', 'description', 'detalle'],
            'document_ref': ['documento', 'referencia', 'doc', 'ref']
        }
    
    def load_balance_sheet(self, file_path: Path, year: int, company_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Load and process Balance de Sumas y Saldos
        
        Args:
            file_path: Path to Excel file
            year: Accounting year
            company_info: Optional company information
            
        Returns:
            Processing results
        """
        self.logger.info(f"Loading balance sheet for year {year}: {file_path}")
        
        try:
            # Read Excel file
            df = self._read_excel_smart(file_path)
            
            if df is None or df.empty:
                return {'status': 'error', 'message': 'Could not read file or file is empty'}
            
            # Detect and map columns
            column_mapping = self._detect_columns(df, self.balance_columns)
            
            if not column_mapping.get('account_code'):
                return {'status': 'error', 'message': 'Could not detect account code column'}
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Clean and validate data
            df = self._clean_balance_data(df)
            
            # Filter by account detail level
            df = df[df['account_level'] >= self.min_account_digits]
            
            # Create or get accounting period
            period = self._get_or_create_period(year, company_info)
            
            # Import to database
            imported_count = self._import_balance_data(df, period, file_path)
            
            # Generate statistics
            stats = self._generate_balance_statistics(period.id)
            
            self.logger.info(f"Imported {imported_count} accounts for year {year}")
            
            return {
                'status': 'success',
                'period_id': period.id,
                'year': year,
                'imported_accounts': imported_count,
                'statistics': stats,
                'file_path': str(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load balance sheet: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def load_general_ledger(self, file_path: Path, year: int, company_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Load and process General Ledger (Diario)
        
        Args:
            file_path: Path to Excel file
            year: Accounting year
            company_info: Optional company information
            
        Returns:
            Processing results
        """
        self.logger.info(f"Loading general ledger for year {year}: {file_path}")
        
        try:
            # Read Excel file (may be very large)
            df = self._read_excel_smart(file_path, chunksize=10000)
            
            if df is None:
                return {'status': 'error', 'message': 'Could not read file'}
            
            # Create or get accounting period
            period = self._get_or_create_period(year, company_info)
            
            total_imported = 0
            
            # Process in chunks if necessary
            if isinstance(df, pd.DataFrame):
                chunks = [df]
            else:
                chunks = df
            
            for chunk_df in chunks:
                # Detect and map columns
                column_mapping = self._detect_columns(chunk_df, self.journal_columns)
                
                if not column_mapping.get('account_code'):
                    continue
                
                # Rename columns
                chunk_df = chunk_df.rename(columns=column_mapping)
                
                # Clean and validate data
                chunk_df = self._clean_journal_data(chunk_df)
                
                # Import to database
                imported_count = self._import_journal_data(chunk_df, period, file_path)
                total_imported += imported_count
            
            # Generate statistics
            stats = self._generate_journal_statistics(period.id)
            
            self.logger.info(f"Imported {total_imported} journal entries for year {year}")
            
            return {
                'status': 'success',
                'period_id': period.id,
                'year': year,
                'imported_entries': total_imported,
                'statistics': stats,
                'file_path': str(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to load general ledger: {e}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    def load_multiple_periods(self, files_by_year: Dict[int, Dict[str, Path]], company_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Load balances and ledgers for multiple years
        
        Args:
            files_by_year: Dictionary mapping year to {'balance': path, 'ledger': path}
            company_info: Company information
            
        Returns:
            Combined results
        """
        self.logger.info(f"Loading accounting data for {len(files_by_year)} periods")
        
        results = {
            'periods': [],
            'errors': [],
            'summary': {
                'total_years': len(files_by_year),
                'successful': 0,
                'failed': 0
            }
        }
        
        # Sort years (oldest first)
        sorted_years = sorted(files_by_year.keys())
        
        for year in sorted_years:
            year_files = files_by_year[year]
            year_result = {'year': year, 'balance': None, 'ledger': None}
            
            # Load balance sheet (priority)
            if 'balance' in year_files and year_files['balance']:
                balance_result = self.load_balance_sheet(year_files['balance'], year, company_info)
                year_result['balance'] = balance_result
                
                if balance_result['status'] == 'success':
                    self.logger.info(f"✓ Balance sheet loaded for {year}")
                else:
                    self.logger.error(f"✗ Failed to load balance sheet for {year}")
                    results['errors'].append(f"Year {year} balance: {balance_result.get('message')}")
            
            # Load general ledger
            if 'ledger' in year_files and year_files['ledger']:
                ledger_result = self.load_general_ledger(year_files['ledger'], year, company_info)
                year_result['ledger'] = ledger_result
                
                if ledger_result['status'] == 'success':
                    self.logger.info(f"✓ General ledger loaded for {year}")
                else:
                    self.logger.error(f"✗ Failed to load general ledger for {year}")
                    results['errors'].append(f"Year {year} ledger: {ledger_result.get('message')}")
            
            results['periods'].append(year_result)
            
            # Update summary
            if (year_result['balance'] and year_result['balance']['status'] == 'success') or \
               (year_result['ledger'] and year_result['ledger']['status'] == 'success'):
                results['summary']['successful'] += 1
            else:
                results['summary']['failed'] += 1
        
        # Mark current audit period
        if sorted_years:
            current_year = sorted_years[-1]
            self._mark_current_audit_period(current_year)
        
        return results
    
    def _read_excel_smart(self, file_path: Path, chunksize: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Smart Excel reading with multiple strategies"""
        try:
            # Try openpyxl first (for .xlsx)
            if file_path.suffix.lower() == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
                return df
            
            # Try xlrd for older formats
            elif file_path.suffix.lower() == '.xls':
                df = pd.read_excel(file_path, engine='xlrd')
                return df
            
            # Try pyxlsb for binary Excel
            elif file_path.suffix.lower() == '.xlsb':
                df = pd.read_excel(file_path, engine='pyxlsb')
                return df
            
        except Exception as e:
            self.logger.error(f"Failed to read Excel file {file_path}: {e}")
            return None
    
    def _detect_columns(self, df: pd.DataFrame, column_patterns: Dict[str, List[str]]) -> Dict[str, str]:
        """Detect column mapping by matching patterns"""
        mapping = {}
        df_columns_lower = [str(col).lower().strip() for col in df.columns]
        
        for field_name, patterns in column_patterns.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                for i, col in enumerate(df_columns_lower):
                    if pattern_lower in col or col in pattern_lower:
                        mapping[df.columns[i]] = field_name
                        break
                if field_name in mapping.values():
                    break
        
        return mapping
    
    def _clean_balance_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate balance sheet data"""
        # Ensure account_code is string
        if 'account_code' in df.columns:
            df['account_code'] = df['account_code'].astype(str).str.strip()
            df['account_code'] = df['account_code'].str.replace(r'[^\d]', '', regex=True)
        
        # Calculate account level (number of digits)
        df['account_level'] = df['account_code'].str.len()
        
        # Convert numeric columns
        numeric_columns = ['suma_debe', 'suma_haber', 'saldo_deudor', 'saldo_acreedor', 'saldo_inicial']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        # Calculate final balance
        if 'saldo_final' not in df.columns:
            df['saldo_final'] = df.get('saldo_deudor', 0) - df.get('saldo_acreedor', 0)
        
        # Remove rows without account code
        df = df[df['account_code'].str.len() > 0]
        
        # Calculate parent account
        df['parent_account'] = df['account_code'].apply(
            lambda x: x[:-1] if len(x) > 1 else None
        )
        
        return df
    
    def _clean_journal_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate journal entry data"""
        # Ensure account_code is string
        if 'account_code' in df.columns:
            df['account_code'] = df['account_code'].astype(str).str.strip()
            df['account_code'] = df['account_code'].str.replace(r'[^\d]', '', regex=True)
        
        # Convert dates
        if 'entry_date' in df.columns:
            df['entry_date'] = pd.to_datetime(df['entry_date'], errors='coerce')
        
        # Convert numeric columns
        for col in ['debit_amount', 'credit_amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        # Remove invalid rows
        df = df.dropna(subset=['account_code', 'entry_date'])
        df = df[df['account_code'].str.len() >= self.min_account_digits]
        
        return df
    
    def _get_or_create_period(self, year: int, company_info: Optional[Dict] = None) -> AccountingPeriod:
        """Get or create accounting period"""
        period = self.session.query(AccountingPeriod).filter_by(year=year).first()
        
        if not period:
            period = AccountingPeriod(
                year=year,
                company_name=company_info.get('name') if company_info else None,
                company_cif=company_info.get('cif') if company_info else None,
                start_date=datetime(year, 1, 1),
                end_date=datetime(year, 12, 31)
            )
            self.session.add(period)
            self.session.commit()
        
        return period
    
    def _import_balance_data(self, df: pd.DataFrame, period: AccountingPeriod, source_file: Path) -> int:
        """Import balance data to database"""
        imported = 0
        
        for _, row in df.iterrows():
            try:
                balance = BalanceAccount(
                    period_id=period.id,
                    account_code=row.get('account_code'),
                    account_name=row.get('account_name', ''),
                    account_level=row.get('account_level', 0),
                    parent_account=row.get('parent_account'),
                    suma_debe=row.get('suma_debe', 0.0),
                    suma_haber=row.get('suma_haber', 0.0),
                    saldo_deudor=row.get('saldo_deudor', 0.0),
                    saldo_acreedor=row.get('saldo_acreedor', 0.0),
                    saldo_final=row.get('saldo_final', 0.0),
                    saldo_inicial=row.get('saldo_inicial', 0.0),
                    source_file=str(source_file)
                )
                self.session.add(balance)
                imported += 1
                
                if imported % 1000 == 0:
                    self.session.commit()
                    
            except Exception as e:
                self.logger.error(f"Failed to import balance row: {e}")
        
        self.session.commit()
        return imported
    
    def _import_journal_data(self, df: pd.DataFrame, period: AccountingPeriod, source_file: Path) -> int:
        """Import journal data to database"""
        imported = 0
        
        for _, row in df.iterrows():
            try:
                entry = JournalEntry(
                    period_id=period.id,
                    entry_number=str(row.get('entry_number', '')),
                    entry_date=row.get('entry_date'),
                    account_code=row.get('account_code'),
                    account_name=row.get('account_name', ''),
                    debit_amount=row.get('debit_amount', 0.0),
                    credit_amount=row.get('credit_amount', 0.0),
                    description=row.get('description', ''),
                    document_ref=row.get('document_ref', ''),
                    source_file=str(source_file)
                )
                self.session.add(entry)
                imported += 1
                
                if imported % 5000 == 0:
                    self.session.commit()
                    self.logger.info(f"Imported {imported} entries...")
                    
            except Exception as e:
                self.logger.error(f"Failed to import journal entry: {e}")
        
        self.session.commit()
        return imported
    
    def _mark_current_audit_period(self, year: int):
        """Mark a period as the current audit period"""
        # Reset all periods
        self.session.query(AccountingPeriod).update({'is_current_audit': 0})
        
        # Mark current
        period = self.session.query(AccountingPeriod).filter_by(year=year).first()
        if period:
            period.is_current_audit = 1
            self.session.commit()
    
    def _generate_balance_statistics(self, period_id: int) -> Dict[str, Any]:
        """Generate statistics for balance sheet"""
        accounts = self.session.query(BalanceAccount).filter_by(period_id=period_id).all()
        
        return {
            'total_accounts': len(accounts),
            'by_level': {
                level: len([a for a in accounts if a.account_level == level])
                for level in range(1, 11)
            },
            'total_assets': sum(a.saldo_final for a in accounts if a.account_code.startswith('2') and a.saldo_final > 0),
            'total_liabilities': sum(abs(a.saldo_final) for a in accounts if a.account_code.startswith(('1', '4')) and a.saldo_final < 0)
        }
    
    def _generate_journal_statistics(self, period_id: int) -> Dict[str, Any]:
        """Generate statistics for journal"""
        from sqlalchemy import func
        
        entry_count = self.session.query(func.count(JournalEntry.id)).filter_by(period_id=period_id).scalar()
        total_debit = self.session.query(func.sum(JournalEntry.debit_amount)).filter_by(period_id=period_id).scalar() or 0
        total_credit = self.session.query(func.sum(JournalEntry.credit_amount)).filter_by(period_id=period_id).scalar() or 0
        
        return {
            'total_entries': entry_count,
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
            'difference': float(total_debit - total_credit)
        }
    
    def query_account(self, account_code: str, year: Optional[int] = None) -> List[Dict]:
        """Query account balance and movements"""
        query = self.session.query(BalanceAccount)
        
        if year:
            period = self.session.query(AccountingPeriod).filter_by(year=year).first()
            if period:
                query = query.filter_by(period_id=period.id)
        
        query = query.filter(BalanceAccount.account_code.startswith(account_code))
        accounts = query.all()
        
        return [
            {
                'account_code': a.account_code,
                'account_name': a.account_name,
                'saldo_final': a.saldo_final,
                'suma_debe': a.suma_debe,
                'suma_haber': a.suma_haber
            }
            for a in accounts
        ]
    
    def get_account_movements(self, account_code: str, year: int) -> pd.DataFrame:
        """Get all journal entries for an account"""
        period = self.session.query(AccountingPeriod).filter_by(year=year).first()
        
        if not period:
            return pd.DataFrame()
        
        entries = self.session.query(JournalEntry).filter_by(
            period_id=period.id,
            account_code=account_code
        ).all()
        
        return pd.DataFrame([
            {
                'date': e.entry_date,
                'entry_number': e.entry_number,
                'description': e.description,
                'debit': e.debit_amount,
                'credit': e.credit_amount,
                'document_ref': e.document_ref
            }
            for e in entries
        ])
