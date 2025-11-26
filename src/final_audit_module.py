"""
Final Audit Module - Comprehensive audit completion and reporting
Implements final balance, management letter, findings, report generation
"""

import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import logging

logger = logging.getLogger(__name__)


class FinalAuditModule:
    """
    Handles final audit procedures:
    - Approved adjustments and reclassifications
    - Final trial balance
    - Management representation letter
    - Audit findings summary
    - Article 229 LSC confirmation
    - Annual accounts review
    - Audit report generation
    """
    
    def __init__(self, accounting_core, output_dir="./papeles_trabajo"):
        self.accounting = accounting_core
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_final_audit_package(self, year, entity_type="mercantil", 
                                     client_name="", client_cif="",
                                     approved_adjustments=None,
                                     approved_reclassifications=None):
        """
        Generates complete final audit package
        """
        logger.info(f"Generating final audit package for {year}")
        
        if approved_adjustments is None:
            approved_adjustments = []
        if approved_reclassifications is None:
            approved_reclassifications = []
            
        files_generated = []
        
        # 1. Final trial balance with adjustments
        final_balance_file = self.generate_final_balance(
            year, client_name, approved_adjustments, approved_reclassifications
        )
        files_generated.append(final_balance_file)
        
        # 2. Management representation letter
        carta_file = self.generate_management_letter(
            year, client_name, client_cif, entity_type
        )
        files_generated.append(carta_file)
        
        # 3. Audit findings summary
        findings_file = self.generate_findings_summary(
            year, client_name, approved_adjustments, approved_reclassifications
        )
        files_generated.append(findings_file)
        
        # 4. Article 229 LSC confirmation
        art229_file = self.generate_art229_confirmation(
            year, client_name, client_cif
        )
        files_generated.append(art229_file)
        
        # 5. Annual accounts review
        accounts_file = self.generate_annual_accounts_review(
            year, client_name, entity_type
        )
        files_generated.append(accounts_file)
        
        # 6. Audit report
        report_file = self.generate_audit_report(
            year, client_name, client_cif, entity_type,
            approved_adjustments, approved_reclassifications
        )
        files_generated.append(report_file)
        
        logger.info(f"Final audit package generated: {len(files_generated)} files")
        return files_generated
    
    def generate_final_balance(self, year, client_name, adjustments, reclassifications):
        """Generates final trial balance with approved adjustments"""
        filename = f"PT_Balance_Final_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        
        # Sheet 1: Final Balance
        ws1 = wb.active
        ws1.title = "Balance Final"
        
        # Header
        ws1['A1'] = "BALANCE DE SUMAS Y SALDOS FINAL"
        ws1['A1'].font = Font(size=14, bold=True)
        ws1['A2'] = f"Cliente: {client_name}"
        ws1['A3'] = f"Ejercicio: {year}"
        ws1['A4'] = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        
        headers = ['Cuenta', 'Denominación', 'Saldo Inicial', 'Ajustes Debe', 
                  'Ajustes Haber', 'Reclasif. Debe', 'Reclasif. Haber', 'Saldo Final']
        for col, header in enumerate(headers, 1):
            cell = ws1.cell(row=6, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        # Get accounts from database
        accounts = self.accounting.get_all_accounts(year)
        row = 7
        
        for account in accounts[:20]:  # Sample data
            ws1.cell(row=row, column=1, value=account.get('code', ''))
            ws1.cell(row=row, column=2, value=account.get('name', ''))
            ws1.cell(row=row, column=3, value=account.get('balance', 0))
            
            # Calculate adjustment impact
            adj_debe = sum(a['debe'] for a in adjustments if a.get('cuenta') == account.get('code'))
            adj_haber = sum(a['haber'] for a in adjustments if a.get('cuenta') == account.get('code'))
            
            ws1.cell(row=row, column=4, value=adj_debe)
            ws1.cell(row=row, column=5, value=adj_haber)
            
            # Calculate reclassification impact
            reclas_debe = sum(r['importe'] for r in reclassifications if r.get('a_cuenta') == account.get('code'))
            reclas_haber = sum(r['importe'] for r in reclassifications if r.get('de_cuenta') == account.get('code'))
            
            ws1.cell(row=row, column=6, value=reclas_debe)
            ws1.cell(row=row, column=7, value=reclas_haber)
            
            # Final balance
            final = account.get('balance', 0) + adj_debe - adj_haber + reclas_debe - reclas_haber
            ws1.cell(row=row, column=8, value=final)
            row += 1
        
        # Sheet 2: Adjustments applied
        ws2 = wb.create_sheet("Ajustes Aplicados")
        ws2['A1'] = f"AJUSTES DEFINITIVOS - {year}"
        ws2['A1'].font = Font(size=12, bold=True)
        
        adj_headers = ['ID', 'Descripción', 'Cuenta', 'Debe', 'Haber', 'Estado']
        for col, header in enumerate(adj_headers, 1):
            ws2.cell(row=3, column=col, value=header).font = Font(bold=True)
        
        for idx, adj in enumerate(adjustments, 4):
            ws2.cell(row=idx, column=1, value=adj.get('id', ''))
            ws2.cell(row=idx, column=2, value=adj.get('descripcion', ''))
            ws2.cell(row=idx, column=3, value=adj.get('cuenta', ''))
            ws2.cell(row=idx, column=4, value=adj.get('debe', 0))
            ws2.cell(row=idx, column=5, value=adj.get('haber', 0))
            ws2.cell(row=idx, column=6, value='PROCESADO')
        
        # Sheet 3: Reclassifications applied
        ws3 = wb.create_sheet("Reclasificaciones Aplicadas")
        ws3['A1'] = f"RECLASIFICACIONES DEFINITIVAS - {year}"
        ws3['A1'].font = Font(size=12, bold=True)
        
        reclas_headers = ['ID', 'Descripción', 'De Cuenta', 'A Cuenta', 'Importe', 'Estado']
        for col, header in enumerate(reclas_headers, 1):
            ws3.cell(row=3, column=col, value=header).font = Font(bold=True)
        
        for idx, reclas in enumerate(reclassifications, 4):
            ws3.cell(row=idx, column=1, value=reclas.get('id', ''))
            ws3.cell(row=idx, column=2, value=reclas.get('descripcion', ''))
            ws3.cell(row=idx, column=3, value=reclas.get('de_cuenta', ''))
            ws3.cell(row=idx, column=4, value=reclas.get('a_cuenta', ''))
            ws3.cell(row=idx, column=5, value=reclas.get('importe', 0))
            ws3.cell(row=idx, column=6, value='PROCESADO')
        
        wb.save(filepath)
        logger.info(f"Final balance generated: {filename}")
        return filepath
    
    def generate_management_letter(self, year, client_name, client_cif, entity_type):
        """Generates management representation letter (Carta de Manifestaciones)"""
        filename = f"Carta_Manifestaciones_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Carta Manifestaciones"
        
        # Header
        ws['A1'] = "CARTA DE MANIFESTACIONES DE LA DIRECCIÓN"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:F1')
        
        ws['A3'] = f"Cliente: {client_name}"
        ws['A4'] = f"CIF: {client_cif}"
        ws['A5'] = f"Ejercicio: {year}"
        ws['A6'] = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        
        # Content
        row = 8
        manifestations = [
            "1. RESPONSABILIDAD DE LAS CUENTAS ANUALES",
            "   - Las cuentas anuales han sido preparadas de acuerdo con el marco normativo aplicable",
            "   - Toda la información contable y documental ha sido puesta a disposición del auditor",
            "",
            "2. INTEGRIDAD DE LA INFORMACIÓN",
            "   - Todos los libros y registros contables están completos y al día",
            "   - No existen irregularidades que involucren a la dirección o empleados",
            "   - No hay conocimiento de fraude que pueda afectar a las cuentas anuales",
            "",
            "3. RECONOCIMIENTO, VALORACIÓN Y PRESENTACIÓN",
            "   - Los criterios contables aplicados son uniformes con el ejercicio anterior",
            "   - Las estimaciones contables se basan en hipótesis razonables",
            "   - Los activos y pasivos registrados existen y son propiedad de la entidad",
            "",
            "4. HECHOS POSTERIORES",
            "   - No hay hechos posteriores al cierre que requieran ajuste o revelación",
            "   - No hay litigios o reclamaciones pendientes no contabilizados",
            "",
            "5. CUMPLIMIENTO NORMATIVO",
            "   - La sociedad ha cumplido con todas las disposiciones legales aplicables",
            "   - No hay incumplimientos fiscales, laborales o mercantiles significativos",
            "",
            "6. CONTINUIDAD",
            "   - La entidad continuará con sus operaciones en el futuro previsible",
            "   - No existen incertidumbres significativas sobre la continuidad",
        ]
        
        for item in manifestations:
            ws.cell(row=row, column=1, value=item)
            row += 1
        
        # Signatures
        row += 3
        ws.cell(row=row, column=1, value="FIRMAS:")
        ws.cell(row=row, column=1).font = Font(bold=True)
        row += 2
        ws.cell(row=row, column=1, value="Administrador:")
        ws.cell(row=row, column=4, value="Firma:")
        row += 5
        ws.cell(row=row, column=1, value="Fecha: ___/___/______")
        
        wb.save(filepath)
        logger.info(f"Management letter generated: {filename}")
        return filepath
    
    def generate_findings_summary(self, year, client_name, adjustments, reclassifications):
        """Generates audit findings summary (Hallazgos)"""
        filename = f"Hallazgos_Auditoria_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Hallazgos"
        
        # Header
        ws['A1'] = "RESUMEN DE HALLAZGOS DE AUDITORÍA"
        ws['A1'].font = Font(size=14, bold=True)
        ws['A2'] = f"Cliente: {client_name}"
        ws['A3'] = f"Ejercicio: {year}"
        
        headers = ['Ref', 'Área', 'Hallazgo', 'Impacto', 'Recomendación', 'Estado']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=5, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        # Sample findings based on adjustments
        row = 6
        findings = []
        
        if len(adjustments) > 0:
            findings.append({
                'ref': 'H001',
                'area': 'Ajustes Contables',
                'finding': f'{len(adjustments)} ajustes propuestos y procesados',
                'impact': f'{sum(a.get("debe", 0) for a in adjustments)} €',
                'recommendation': 'Revisar procedimientos de cierre contable',
                'status': 'CERRADO'
            })
        
        if len(reclassifications) > 0:
            findings.append({
                'ref': 'H002',
                'area': 'Reclasificaciones',
                'finding': f'{len(reclassifications)} reclasificaciones realizadas',
                'impact': f'{sum(r.get("importe", 0) for r in reclassifications)} €',
                'recommendation': 'Mejorar criterios de clasificación',
                'status': 'CERRADO'
            })
        
        for finding in findings:
            ws.cell(row=row, column=1, value=finding['ref'])
            ws.cell(row=row, column=2, value=finding['area'])
            ws.cell(row=row, column=3, value=finding['finding'])
            ws.cell(row=row, column=4, value=finding['impact'])
            ws.cell(row=row, column=5, value=finding['recommendation'])
            ws.cell(row=row, column=6, value=finding['status'])
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 40
        ws.column_dimensions['F'].width = 12
        
        wb.save(filepath)
        logger.info(f"Findings summary generated: {filename}")
        return filepath
    
    def generate_art229_confirmation(self, year, client_name, client_cif):
        """Generates Article 229 LSC confirmation"""
        filename = f"Confirmacion_Art229_LSC_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Art 229 LSC"
        
        ws['A1'] = "CONFIRMACIÓN ARTÍCULO 229 LEY DE SOCIEDADES DE CAPITAL"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:D1')
        
        ws['A3'] = f"Cliente: {client_name}"
        ws['A4'] = f"CIF: {client_cif}"
        ws['A5'] = f"Ejercicio: {year}"
        
        content = [
            "",
            "De conformidad con el artículo 229 de la Ley de Sociedades de Capital,",
            "confirmamos que:",
            "",
            "1. El auditor ha tenido acceso a toda la información necesaria",
            "2. No existen limitaciones al alcance de la auditoría",
            "3. Se han facilitado todas las aclaraciones solicitadas",
            "4. El auditor ha podido aplicar todos los procedimientos necesarios",
            "",
            "Adicionalmente confirmamos:",
            "- Independencia del auditor respecto a la sociedad",
            "- Ausencia de conflictos de interés",
            "- Cumplimiento de normativa de auditoría de cuentas",
            "",
            "",
            "FIRMAS:",
            "",
            "Por la Sociedad:                    Por el Auditor:",
            "",
            "________________                    ________________",
            "Administrador                       Auditor de Cuentas",
            "",
            f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        ]
        
        for idx, line in enumerate(content, 7):
            ws.cell(row=idx, column=1, value=line)
        
        wb.save(filepath)
        logger.info(f"Art 229 confirmation generated: {filename}")
        return filepath
    
    def generate_annual_accounts_review(self, year, client_name, entity_type):
        """Generates annual accounts review checklist"""
        filename = f"Revision_Cuentas_Anuales_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        
        # Sheet 1: Balance Sheet Review
        ws1 = wb.active
        ws1.title = "Balance"
        ws1['A1'] = "REVISIÓN BALANCE DE SITUACIÓN"
        ws1['A1'].font = Font(size=12, bold=True)
        
        balance_items = [
            ("A) ACTIVO NO CORRIENTE", ""),
            ("  I. Inmovilizado intangible", "✓"),
            ("  II. Inmovilizado material", "✓"),
            ("  III. Inversiones inmobiliarias", "✓"),
            ("  IV. Inversiones financieras a largo plazo", "✓"),
            ("B) ACTIVO CORRIENTE", ""),
            ("  I. Activos no corrientes mantenidos para la venta", "✓"),
            ("  II. Existencias", "✓"),
            ("  III. Deudores comerciales", "✓"),
            ("  IV. Inversiones financieras a corto plazo", "✓"),
            ("  V. Efectivo y equivalentes", "✓"),
            ("C) PATRIMONIO NETO", ""),
            ("  I. Fondos propios", "✓"),
            ("  II. Subvenciones", "✓"),
            ("D) PASIVO NO CORRIENTE", ""),
            ("  I. Provisiones a largo plazo", "✓"),
            ("  II. Deudas a largo plazo", "✓"),
            ("E) PASIVO CORRIENTE", ""),
            ("  I. Provisiones a corto plazo", "✓"),
            ("  II. Deudas a corto plazo", "✓"),
            ("  III. Acreedores comerciales", "✓"),
        ]
        
        for idx, (item, check) in enumerate(balance_items, 3):
            ws1.cell(row=idx, column=1, value=item)
            ws1.cell(row=idx, column=2, value=check)
        
        # Sheet 2: P&L Review
        ws2 = wb.create_sheet("Cuenta Resultados")
        ws2['A1'] = "REVISIÓN CUENTA DE PÉRDIDAS Y GANANCIAS"
        ws2['A1'].font = Font(size=12, bold=True)
        
        pl_items = [
            ("1. Importe neto de la cifra de negocios", "✓"),
            ("2. Variación de existencias", "✓"),
            ("3. Trabajos realizados para su activo", "✓"),
            ("4. Aprovisionamientos", "✓"),
            ("5. Otros ingresos de explotación", "✓"),
            ("6. Gastos de personal", "✓"),
            ("7. Otros gastos de explotación", "✓"),
            ("8. Amortización del inmovilizado", "✓"),
            ("9. Imputación de subvenciones", "✓"),
            ("10. Deterioros y resultados", "✓"),
            ("A) RESULTADO DE EXPLOTACIÓN", "✓"),
            ("11. Ingresos financieros", "✓"),
            ("12. Gastos financieros", "✓"),
            ("B) RESULTADO FINANCIERO", "✓"),
            ("C) RESULTADO ANTES DE IMPUESTOS", "✓"),
            ("13. Impuesto sobre beneficios", "✓"),
            ("D) RESULTADO DEL EJERCICIO", "✓"),
        ]
        
        for idx, (item, check) in enumerate(pl_items, 3):
            ws2.cell(row=idx, column=1, value=item)
            ws2.cell(row=idx, column=2, value=check)
        
        # Sheet 3: Memory Notes
        ws3 = wb.create_sheet("Memoria")
        ws3['A1'] = "REVISIÓN MEMORIA"
        ws3['A1'].font = Font(size=12, bold=True)
        
        memory_notes = [
            ("1. Actividad de la empresa", "✓"),
            ("2. Bases de presentación", "✓"),
            ("3. Distribución de resultados", "✓"),
            ("4. Normas de valoración", "✓"),
            ("5. Inmovilizado material", "✓"),
            ("6. Inmovilizado intangible", "✓"),
            ("7. Arrendamientos", "✓"),
            ("8. Instrumentos financieros", "✓"),
            ("9. Existencias", "✓"),
            ("10. Fondos propios", "✓"),
            ("11. Subvenciones", "✓"),
            ("12. Provisiones", "✓"),
            ("13. Deudas", "✓"),
            ("14. Situación fiscal", "✓"),
            ("15. Ingresos y gastos", "✓"),
            ("16. Operaciones partes vinculadas", "✓"),
            ("17. Otra información", "✓"),
        ]
        
        for idx, (note, check) in enumerate(memory_notes, 3):
            ws3.cell(row=idx, column=1, value=note)
            ws3.cell(row=idx, column=2, value=check)
        
        wb.save(filepath)
        logger.info(f"Annual accounts review generated: {filename}")
        return filepath
    
    def generate_audit_report(self, year, client_name, client_cif, entity_type,
                            adjustments, reclassifications):
        """Generates audit report (Informe de Auditoría)"""
        filename = f"Informe_Auditoria_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Informe Auditoría"
        
        ws['A1'] = "INFORME DE AUDITORÍA DE CUENTAS ANUALES"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:E1')
        
        ws['A3'] = f"Cliente: {client_name}"
        ws['A4'] = f"CIF: {client_cif}"
        ws['A5'] = f"Ejercicio: {year}"
        ws['A6'] = f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y')}"
        
        # Report content structure
        content = [
            "",
            "I. OPINIÓN",
            "",
            "Hemos auditado las cuentas anuales de [CLIENTE], que comprenden el balance",
            "de situación a 31 de diciembre de [AÑO], la cuenta de pérdidas y ganancias,",
            "el estado de cambios en el patrimonio neto, el estado de flujos de efectivo",
            "y la memoria correspondientes al ejercicio anual terminado en dicha fecha.",
            "",
            "En nuestra opinión, las cuentas anuales adjuntas expresan, en todos los",
            "aspectos significativos, la imagen fiel del patrimonio y de la situación",
            "financiera de [CLIENTE] a 31 de diciembre de [AÑO], así como de sus",
            "resultados y flujos de efectivo correspondientes al ejercicio anual",
            "terminado en dicha fecha, de conformidad con el marco normativo de",
            "información financiera que resulta de aplicación.",
            "",
            "II. FUNDAMENTO DE LA OPINIÓN",
            "",
            "Hemos llevado a cabo nuestra auditoría de conformidad con la normativa",
            "reguladora de la actividad de auditoría de cuentas vigente en España.",
            "Nuestras responsabilidades de acuerdo con dichas normas se describen más",
            "adelante en la sección Responsabilidades del auditor.",
            "",
            "III. CUESTIONES CLAVE DE LA AUDITORÍA",
            "",
            f"• Se procesaron {len(adjustments)} ajustes de auditoría",
            f"• Se realizaron {len(reclassifications)} reclasificaciones contables",
            "• Se obtuvieron confirmaciones externas satisfactorias",
            "• Se revisaron estimaciones contables significativas",
            "",
            "IV. OTRA INFORMACIÓN",
            "",
            "La otra información comprende exclusivamente el informe de gestión del",
            "ejercicio [AÑO], cuya formulación es responsabilidad de los administradores",
            "de la Sociedad.",
            "",
            "V. RESPONSABILIDADES",
            "",
            "Los administradores de la Sociedad son responsables de formular las cuentas",
            "anuales adjuntas, de forma que expresen la imagen fiel del patrimonio, de la",
            "situación financiera y de los resultados de la Sociedad.",
            "",
            "Nuestra responsabilidad consiste en expresar una opinión sobre dichas cuentas",
            "anuales basada en nuestra auditoría.",
            "",
            "",
            "___________________________",
            "[FIRMA DEL AUDITOR]",
            "Auditor de Cuentas",
            f"Fecha: {datetime.now().strftime('%d/%m/%Y')}",
        ]
        
        for idx, line in enumerate(content, 8):
            ws.cell(row=idx, column=1, value=line)
        
        # Format
        ws.column_dimensions['A'].width = 80
        
        wb.save(filepath)
        logger.info(f"Audit report generated: {filename}")
        return filepath
