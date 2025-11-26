"""
Comprehensive Audit Questionnaires Module
Generates risk assessment, internal control, and audit area questionnaires
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class AuditQuestionnaires:
    """Generate and evaluate comprehensive audit questionnaires"""
    
    def __init__(self, accounting_core, output_dir="./papeles_trabajo"):
        self.accounting = accounting_core
        self.output_dir = output_dir
        self.questionnaires = self._initialize_questionnaires()
    
    def _initialize_questionnaires(self) -> Dict:
        """Initialize all questionnaire templates"""
        return {
            'general_risk': self._general_risk_questionnaire(),
            'internal_control': self._internal_control_questionnaire(),
            'fraud_risk': self._fraud_risk_questionnaire(),
            'inmovilizado': self._fixed_assets_questionnaire(),
            'existencias': self._inventory_questionnaire(),
            'tesoreria': self._cash_questionnaire(),
            'deudores': self._receivables_questionnaire(),
            'pasivos': self._liabilities_questionnaire(),
            'ingresos': self._revenue_questionnaire(),
            'compras': self._purchases_questionnaire(),
            'personal': self._payroll_questionnaire(),
            'impuestos': self._tax_questionnaire(),
        }
    
    def _general_risk_questionnaire(self) -> List[Dict]:
        """General risk assessment questionnaire"""
        return [
            {
                'area': 'Entorno General',
                'question': '¿Es la primera auditoría de esta entidad?',
                'risk_if_yes': 'high',
                'risk_if_no': 'low',
                'weight': 5
            },
            {
                'area': 'Entorno General',
                'question': '¿Ha habido cambios significativos en la dirección o estructura organizativa?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 4
            },
            {
                'area': 'Entorno General',
                'question': '¿La empresa tiene problemas de continuidad o dificultades financieras?',
                'risk_if_yes': 'high',
                'risk_if_no': 'low',
                'weight': 5
            },
            {
                'area': 'Entorno General',
                'question': '¿Existe presión sobre la dirección para alcanzar objetivos de resultados?',
                'risk_if_yes': 'high',
                'risk_if_no': 'medium',
                'weight': 4
            },
            {
                'area': 'Entorno General',
                'question': '¿Hay transacciones significativas con partes vinculadas?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 4
            },
            {
                'area': 'Sector',
                'question': '¿Opera la entidad en un sector altamente regulado?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 3
            },
            {
                'area': 'Sector',
                'question': '¿Existe alta volatilidad en el sector de actividad?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 3
            },
            {
                'area': 'Tecnología',
                'question': '¿Utiliza la entidad sistemas informáticos complejos o recientes?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 3
            },
            {
                'area': 'Tecnología',
                'question': '¿Se han producido cambios significativos en los sistemas durante el ejercicio?',
                'risk_if_yes': 'high',
                'risk_if_no': 'low',
                'weight': 4
            },
        ]
    
    def _internal_control_questionnaire(self) -> List[Dict]:
        """Internal control evaluation questionnaire"""
        return [
            {
                'area': 'Entorno de Control',
                'question': '¿Existe un código de conducta y ética empresarial formalizado?',
                'risk_if_yes': 'low',
                'risk_if_no': 'medium',
                'weight': 4
            },
            {
                'area': 'Entorno de Control',
                'question': '¿La dirección tiene competencia y experiencia adecuada?',
                'risk_if_yes': 'low',
                'risk_if_no': 'high',
                'weight': 5
            },
            {
                'area': 'Entorno de Control',
                'question': '¿Existe segregación de funciones adecuada?',
                'risk_if_yes': 'low',
                'risk_if_no': 'high',
                'weight': 5
            },
            {
                'area': 'Evaluación de Riesgos',
                'question': '¿Realiza la entidad evaluaciones periódicas de riesgos?',
                'risk_if_yes': 'low',
                'risk_if_no': 'medium',
                'weight': 3
            },
            {
                'area': 'Actividades de Control',
                'question': '¿Existen autorizaciones documentadas para transacciones significativas?',
                'risk_if_yes': 'low',
                'risk_if_no': 'high',
                'weight': 5
            },
            {
                'area': 'Actividades de Control',
                'question': '¿Se realizan conciliaciones bancarias mensuales?',
                'risk_if_yes': 'low',
                'risk_if_no': 'high',
                'weight': 4
            },
            {
                'area': 'Actividades de Control',
                'question': '¿Existe control de acceso físico a activos importantes?',
                'risk_if_yes': 'low',
                'risk_if_no': 'medium',
                'weight': 3
            },
            {
                'area': 'Información y Comunicación',
                'question': '¿Se generan informes financieros periódicos para la dirección?',
                'risk_if_yes': 'low',
                'risk_if_no': 'medium',
                'weight': 3
            },
            {
                'area': 'Supervisión',
                'question': '¿Existe auditoría interna o función similar?',
                'risk_if_yes': 'low',
                'risk_if_no': 'medium',
                'weight': 3
            },
        ]
    
    def _fraud_risk_questionnaire(self) -> List[Dict]:
        """Fraud risk assessment questionnaire"""
        return [
            {
                'area': 'Incentivos/Presión',
                'question': '¿Existen incentivos basados en resultados financieros?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 4
            },
            {
                'area': 'Incentivos/Presión',
                'question': '¿Tiene la entidad obligaciones de deuda significativas?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 3
            },
            {
                'area': 'Oportunidad',
                'question': '¿Hay falta de supervisión de la dirección?',
                'risk_if_yes': 'high',
                'risk_if_no': 'low',
                'weight': 5
            },
            {
                'area': 'Oportunidad',
                'question': '¿Existen transacciones complejas o inusuales?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 4
            },
            {
                'area': 'Actitud/Racionalización',
                'question': '¿Ha habido rotación alta de personal clave?',
                'risk_if_yes': 'medium',
                'risk_if_no': 'low',
                'weight': 3
            },
        ]
    
    def _fixed_assets_questionnaire(self) -> List[Dict]:
        """Fixed assets specific questionnaire"""
        return [
            {'area': 'Inmovilizado', 'question': '¿Se mantiene un registro detallado de activos fijos?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Inmovilizado', 'question': '¿Se realizan inventarios físicos periódicos?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
            {'area': 'Inmovilizado', 'question': '¿Las adquisiciones requieren autorización previa?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 4},
            {'area': 'Inmovilizado', 'question': '¿Se revisan anualmente las vidas útiles y valores residuales?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 3},
            {'area': 'Inmovilizado', 'question': '¿Se evalúa el deterioro de activos regularmente?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 4},
        ]
    
    def _inventory_questionnaire(self) -> List[Dict]:
        """Inventory specific questionnaire"""
        return [
            {'area': 'Existencias', 'question': '¿Se realizan inventarios físicos al cierre del ejercicio?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Existencias', 'question': '¿Existe control de entradas y salidas de almacén?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Existencias', 'question': '¿Se evalúan regularmente las existencias obsoletas?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
            {'area': 'Existencias', 'question': '¿El almacén tiene acceso restringido?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 3},
        ]
    
    def _cash_questionnaire(self) -> List[Dict]:
        """Cash and treasury questionnaire"""
        return [
            {'area': 'Tesorería', 'question': '¿Se realizan conciliaciones bancarias mensuales?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Tesorería', 'question': '¿Están segregadas las funciones de autorización, custodia y registro?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Tesorería', 'question': '¿Se requieren dos firmas para pagos significativos?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
            {'area': 'Tesorería', 'question': '¿Se realizan arqueos de caja sorpresa?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 3},
        ]
    
    def _receivables_questionnaire(self) -> List[Dict]:
        """Receivables questionnaire"""
        return [
            {'area': 'Deudores', 'question': '¿Se revisa periódicamente la antigüedad de saldos?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
            {'area': 'Deudores', 'question': '¿Existe política documentada de crédito?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 3},
            {'area': 'Deudores', 'question': '¿Se aprueban las bajas de saldos incobrables?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 4},
        ]
    
    def _liabilities_questionnaire(self) -> List[Dict]:
        """Liabilities questionnaire"""
        return [
            {'area': 'Pasivos', 'question': '¿Se concilian regularmente los saldos con acreedores?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
            {'area': 'Pasivos', 'question': '¿Las obligaciones financieras están autorizadas por órgano competente?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Pasivos', 'question': '¿Se controlan los vencimientos y compromisos financieros?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
        ]
    
    def _revenue_questionnaire(self) -> List[Dict]:
        """Revenue questionnaire"""
        return [
            {'area': 'Ingresos', 'question': '¿Se facturan todas las ventas/servicios realizados?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Ingresos', 'question': '¿Se realizan pruebas de corte al cierre?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Ingresos', 'question': '¿Las devoluciones y descuentos requieren autorización?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
        ]
    
    def _purchases_questionnaire(self) -> List[Dict]:
        """Purchases questionnaire"""
        return [
            {'area': 'Compras', 'question': '¿Se cotejan facturas con pedidos y albaranes?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Compras', 'question': '¿Las compras requieren autorización previa?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Compras', 'question': '¿Existe segregación entre quien compra y quien autoriza pagos?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
        ]
    
    def _payroll_questionnaire(self) -> List[Dict]:
        """Payroll questionnaire"""
        return [
            {'area': 'Personal', 'question': '¿Se revisan y autorizan las nóminas antes del pago?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Personal', 'question': '¿Se mantienen expedientes actualizados de empleados?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 3},
            {'area': 'Personal', 'question': '¿Las altas y bajas de empleados se procesan oportunamente?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 4},
        ]
    
    def _tax_questionnaire(self) -> List[Dict]:
        """Tax questionnaire"""
        return [
            {'area': 'Impuestos', 'question': '¿Se presentan las declaraciones fiscales en plazo?', 'risk_if_yes': 'low', 'risk_if_no': 'high', 'weight': 5},
            {'area': 'Impuestos', 'question': '¿Se revisan por profesionales las declaraciones antes de presentar?', 'risk_if_yes': 'low', 'risk_if_no': 'medium', 'weight': 4},
            {'area': 'Impuestos', 'question': '¿Existen contingencias fiscales conocidas?', 'risk_if_yes': 'high', 'risk_if_no': 'low', 'weight': 5},
        ]
    
    def evaluate_questionnaire(self, questionnaire_name: str, responses: Dict[int, bool]) -> Tuple[str, float, Dict]:
        """
        Evaluate questionnaire responses
        
        Args:
            questionnaire_name: Name of questionnaire to evaluate
            responses: Dict mapping question index to Yes/No (True/False)
        
        Returns:
            Tuple of (overall_risk_level, risk_score, detailed_results)
        """
        if questionnaire_name not in self.questionnaires:
            raise ValueError(f"Unknown questionnaire: {questionnaire_name}")
        
        questions = self.questionnaires[questionnaire_name]
        total_weight = sum(q['weight'] for q in questions)
        risk_score = 0
        detailed_results = []
        
        for idx, question in enumerate(questions):
            if idx not in responses:
                continue
            
            answer = responses[idx]
            risk_level = question['risk_if_yes'] if answer else question['risk_if_no']
            
            # Convert risk level to numeric score
            risk_values = {'low': 1, 'medium': 2, 'high': 3}
            question_risk_score = risk_values[risk_level] * question['weight']
            risk_score += question_risk_score
            
            detailed_results.append({
                'area': question['area'],
                'question': question['question'],
                'answer': 'Sí' if answer else 'No',
                'risk_level': risk_level,
                'weight': question['weight'],
                'score': question_risk_score
            })
        
        # Calculate normalized risk score (0-100)
        max_possible_score = total_weight * 3  # Max is high risk (3) for all questions
        normalized_score = (risk_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        
        # Determine overall risk level
        if normalized_score < 33:
            overall_risk = 'low'
        elif normalized_score < 66:
            overall_risk = 'medium'
        else:
            overall_risk = 'high'
        
        return overall_risk, normalized_score, detailed_results
    
    def generate_questionnaire_workpaper(self, year: int, questionnaire_name: str, 
                                        responses: Dict[int, bool] = None) -> str:
        """Generate Excel working paper for questionnaire"""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        if questionnaire_name not in self.questionnaires:
            raise ValueError(f"Unknown questionnaire: {questionnaire_name}")
        
        questions = self.questionnaires[questionnaire_name]
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Cuestionario"
        
        # Title
        ws['A1'] = f"CUESTIONARIO - {questionnaire_name.upper().replace('_', ' ')}"
        ws['A1'].font = Font(size=14, bold=True)
        ws['A2'] = f"Ejercicio: {year}"
        ws['A3'] = f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"
        
        # Headers
        headers = ['#', 'Área', 'Pregunta', 'Respuesta', 'Nivel de Riesgo', 'Peso', 'Observaciones']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(5, col, header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Questions
        row = 6
        for idx, question in enumerate(questions):
            ws.cell(row, 1, idx + 1)
            ws.cell(row, 2, question['area'])
            ws.cell(row, 3, question['question'])
            ws.cell(row, 4, '')  # Response to be filled
            ws.cell(row, 5, '')  # Risk level calculated
            ws.cell(row, 6, question['weight'])
            ws.cell(row, 7, '')  # Observations
            row += 1
        
        # If responses provided, evaluate and fill
        if responses:
            overall_risk, score, details = self.evaluate_questionnaire(questionnaire_name, responses)
            
            row = 6
            for detail in details:
                ws.cell(row, 4, detail['answer'])
                ws.cell(row, 5, detail['risk_level'].upper())
                
                # Color code risk
                risk_colors = {
                    'low': 'C6EFCE',
                    'medium': 'FFEB9C',
                    'high': 'FFC7CE'
                }
                ws.cell(row, 5).fill = PatternFill(
                    start_color=risk_colors[detail['risk_level']],
                    end_color=risk_colors[detail['risk_level']],
                    fill_type="solid"
                )
                row += 1
            
            # Summary
            summary_row = row + 2
            ws.cell(summary_row, 1, "RESUMEN").font = Font(bold=True, size=12)
            ws.cell(summary_row + 1, 1, "Puntuación de Riesgo:")
            ws.cell(summary_row + 1, 2, f"{score:.1f}/100")
            ws.cell(summary_row + 2, 1, "Nivel de Riesgo Global:")
            ws.cell(summary_row + 2, 2, overall_risk.upper())
            ws.cell(summary_row + 2, 2).fill = PatternFill(
                start_color=risk_colors[overall_risk],
                end_color=risk_colors[overall_risk],
                fill_type="solid"
            )
        
        # Column widths
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 60
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 18
        ws.column_dimensions['F'].width = 8
        ws.column_dimensions['G'].width = 30
        
        # Save
        filename = f"PT_Cuestionario_{questionnaire_name}_{year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        filepath = f"{self.output_dir}/{filename}"
        wb.save(filepath)
        
        logger.info(f"Generated questionnaire working paper: {filename}")
        return filepath
    
    def generate_all_questionnaires(self, year: int) -> List[str]:
        """Generate all questionnaire templates"""
        files = []
        for name in self.questionnaires.keys():
            try:
                filepath = self.generate_questionnaire_workpaper(year, name)
                files.append(filepath)
            except Exception as e:
                logger.error(f"Error generating questionnaire {name}: {e}")
        return files
