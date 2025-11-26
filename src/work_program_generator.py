"""
Work Program Generator Module
AI-powered generation of audit work programs and procedures based on risk assessment
Creates customized test procedures for each audit area with methodology documentation
"""

import pandas as pd
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


class WorkProgramGenerator:
    """Generates customized audit work programs based on risk assessment"""
    
    # Standard audit procedures by area and risk level
    PROCEDURES_LIBRARY = {
        'inmovilizado': {
            'high': [
                {
                    'id': 'INM-01',
                    'procedure': 'Inspección física de activos materiales significativos',
                    'methodology': 'Visitar instalaciones y verificar existencia física de activos seleccionados en el inventario',
                    'sample_size': 'Muestra estadística del 25% del valor total',
                    'evidence': 'Fotografías, identificación de placas, actas de inventario'
                },
                {
                    'id': 'INM-02',
                    'procedure': 'Revisión de títulos de propiedad y escrituras',
                    'methodology': 'Obtener escrituras de inmuebles y verificar inscripción registral',
                    'sample_size': 'Todas las propiedades inmobiliarias',
                    'evidence': 'Notas simples registrales, escrituras, certificados de cargas'
                },
                {
                    'id': 'INM-03',
                    'procedure': 'Prueba detallada de amortizaciones',
                    'methodology': 'Recalcular amortizaciones según vidas útiles y métodos aplicados',
                    'sample_size': 'Muestra de 30 activos de mayor valor',
                    'evidence': 'Hoja de cálculo con recálculo, comparativa con contabilidad'
                },
                {
                    'id': 'INM-04',
                    'procedure': 'Análisis de altas del ejercicio',
                    'methodology': 'Revisar facturas, actas de recepción y activación de activos',
                    'sample_size': 'Todas las altas > materialidad de ejecución',
                    'evidence': 'Facturas, contratos, autorizaciones, actas de recepción'
                },
                {
                    'id': 'INM-05',
                    'procedure': 'Prueba de deterioro de activos',
                    'methodology': 'Verificar cálculos de deterioro y razonabilidad de hipótesis',
                    'sample_size': 'Todos los activos con indicios de deterioro',
                    'evidence': 'Tasaciones, informes de valoración, cálculos internos'
                }
            ],
            'medium': [
                {
                    'id': 'INM-01',
                    'procedure': 'Inspección física selectiva de activos',
                    'methodology': 'Verificar muestra de activos materiales significativos',
                    'sample_size': '15% del valor total',
                    'evidence': 'Acta de inspección'
                },
                {
                    'id': 'INM-02',
                    'procedure': 'Revisión analítica de amortizaciones',
                    'methodology': 'Comparar dotaciones con ejercicio anterior y ratios sectoriales',
                    'sample_size': 'N/A - Procedimiento analítico',
                    'evidence': 'Análisis comparativo'
                },
                {
                    'id': 'INM-03',
                    'procedure': 'Prueba de altas significativas',
                    'methodology': 'Revisar documentación de altas materiales',
                    'sample_size': 'Altas > materialidad de ejecución',
                    'evidence': 'Facturas y contratos'
                }
            ],
            'low': [
                {
                    'id': 'INM-01',
                    'procedure': 'Procedimientos analíticos sustantivos',
                    'methodology': 'Análisis de tendencias y ratios',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis de ratios'
                },
                {
                    'id': 'INM-02',
                    'procedure': 'Revisión de movimientos inusuales',
                    'methodology': 'Investigar variaciones significativas',
                    'sample_size': 'Variaciones > 10%',
                    'evidence': 'Explicaciones de la dirección'
                }
            ]
        },
        'existencias': {
            'high': [
                {
                    'id': 'EXI-01',
                    'procedure': 'Asistencia a inventario físico',
                    'methodology': 'Presenciar recuento físico y realizar pruebas de rastreo y seguimiento',
                    'sample_size': 'Mínimo 50 referencias',
                    'evidence': 'Hoja de observaciones, recuentos propios, fotografías'
                },
                {
                    'id': 'EXI-02',
                    'procedure': 'Prueba de valoración de existencias',
                    'methodology': 'Verificar coste de adquisición o producción según facturas y costes',
                    'sample_size': '25 referencias de mayor valor',
                    'evidence': 'Facturas de compra, análisis de costes, cálculos'
                },
                {
                    'id': 'EXI-03',
                    'procedure': 'Análisis de obsolescencia',
                    'methodology': 'Revisar antigüedad, rotación y provisiones por deterioro',
                    'sample_size': 'Todas las referencias con antigüedad > 12 meses',
                    'evidence': 'Listado de antigüedad, análisis de rotación, propuestas de provisión'
                },
                {
                    'id': 'EXI-04',
                    'procedure': 'Prueba de corte de operaciones',
                    'methodology': 'Verificar corte de compras y ventas en cierre de ejercicio',
                    'sample_size': '10 últimas compras y 10 últimas ventas del ejercicio',
                    'evidence': 'Albaranes, facturas, registros contables'
                }
            ],
            'medium': [
                {
                    'id': 'EXI-01',
                    'procedure': 'Revisión de inventario físico',
                    'methodology': 'Revisar procedimientos y ajustes de inventario',
                    'sample_size': '20 referencias',
                    'evidence': 'Actas de inventario'
                },
                {
                    'id': 'EXI-02',
                    'procedure': 'Prueba selectiva de valoración',
                    'methodology': 'Verificar coste de referencias significativas',
                    'sample_size': '15 referencias',
                    'evidence': 'Facturas seleccionadas'
                },
                {
                    'id': 'EXI-03',
                    'procedure': 'Revisión de provisiones',
                    'methodology': 'Analizar razonabilidad de provisiones por obsolescencia',
                    'sample_size': 'N/A - Analítico',
                    'evidence': 'Análisis de rotación'
                }
            ],
            'low': [
                {
                    'id': 'EXI-01',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de rotación y variaciones',
                    'sample_size': 'N/A',
                    'evidence': 'Ratios de rotación'
                }
            ]
        },
        'deudores': {
            'high': [
                {
                    'id': 'DEU-01',
                    'procedure': 'Circularización de saldos de clientes',
                    'methodology': 'Enviar confirmaciones externas a muestra de clientes',
                    'sample_size': '30 clientes (cobertura 70% saldo)',
                    'evidence': 'Confirmaciones recibidas, análisis de diferencias'
                },
                {
                    'id': 'DEU-02',
                    'procedure': 'Prueba de cobros posteriores',
                    'methodology': 'Verificar cobros posteriores al cierre del ejercicio',
                    'sample_size': 'Saldos > materialidad de ejecución',
                    'evidence': 'Extractos bancarios, aplicación de cobros'
                },
                {
                    'id': 'DEU-03',
                    'procedure': 'Análisis de antigüedad de saldos',
                    'methodology': 'Clasificar saldos por antigüedad y evaluar provisiones',
                    'sample_size': 'Todos los saldos',
                    'evidence': 'Listado de antigüedad, análisis de cobrabilidad'
                },
                {
                    'id': 'DEU-04',
                    'procedure': 'Prueba de corte de ventas',
                    'methodology': 'Verificar registro de ventas en periodo correcto',
                    'sample_size': '15 últimas y primeras ventas del ejercicio',
                    'evidence': 'Facturas, albaranes, registros contables'
                }
            ],
            'medium': [
                {
                    'id': 'DEU-01',
                    'procedure': 'Circularización selectiva',
                    'methodology': 'Confirmar saldos significativos',
                    'sample_size': '20 clientes principales',
                    'evidence': 'Confirmaciones'
                },
                {
                    'id': 'DEU-02',
                    'procedure': 'Cobros posteriores',
                    'methodology': 'Verificar cobros de saldos materiales',
                    'sample_size': 'Saldos > materialidad de ejecución',
                    'evidence': 'Extractos bancarios'
                },
                {
                    'id': 'DEU-03',
                    'procedure': 'Revisión de provisiones',
                    'methodology': 'Analizar razonabilidad de provisiones',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis de antigüedad'
                }
            ],
            'low': [
                {
                    'id': 'DEU-01',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de ratios y tendencias',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis comparativo'
                }
            ]
        },
        'tesoreria': {
            'high': [
                {
                    'id': 'TES-01',
                    'procedure': 'Confirmación bancaria de saldos y condiciones',
                    'methodology': 'Solicitar confirmaciones a todas las entidades bancarias',
                    'sample_size': 'Todas las cuentas bancarias',
                    'evidence': 'Confirmaciones bancarias recibidas'
                },
                {
                    'id': 'TES-02',
                    'procedure': 'Conciliaciones bancarias al cierre',
                    'methodology': 'Revisar y verificar todas las conciliaciones bancarias',
                    'sample_size': 'Todas las cuentas',
                    'evidence': 'Conciliaciones, extractos bancarios, libro mayor'
                },
                {
                    'id': 'TES-03',
                    'procedure': 'Arqueo de caja',
                    'methodology': 'Realizar arqueo sorpresa de efectivo en caja',
                    'sample_size': 'Todas las cajas',
                    'evidence': 'Acta de arqueo firmada'
                },
                {
                    'id': 'TES-04',
                    'procedure': 'Revisión de restricciones y garantías',
                    'methodology': 'Verificar restricciones de disposición y garantías constituidas',
                    'sample_size': 'Todas las cuentas',
                    'evidence': 'Confirmaciones, contratos de préstamo'
                }
            ],
            'medium': [
                {
                    'id': 'TES-01',
                    'procedure': 'Confirmaciones bancarias',
                    'methodology': 'Confirmar cuentas principales',
                    'sample_size': 'Cuentas > 90% del saldo',
                    'evidence': 'Confirmaciones'
                },
                {
                    'id': 'TES-02',
                    'procedure': 'Revisión de conciliaciones',
                    'methodology': 'Revisar conciliaciones de cuentas significativas',
                    'sample_size': 'Cuentas materiales',
                    'evidence': 'Conciliaciones'
                }
            ],
            'low': [
                {
                    'id': 'TES-01',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de movimientos',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ]
        },
        'pasivos_financieros': {
            'high': [
                {
                    'id': 'PAS-01',
                    'procedure': 'Confirmación de préstamos y líneas de crédito',
                    'methodology': 'Solicitar confirmaciones de saldos, condiciones y garantías',
                    'sample_size': 'Todos los préstamos',
                    'evidence': 'Confirmaciones bancarias'
                },
                {
                    'id': 'PAS-02',
                    'procedure': 'Revisión de contratos de financiación',
                    'methodology': 'Revisar términos, condiciones, covenants y garantías',
                    'sample_size': 'Todos los contratos',
                    'evidence': 'Contratos, análisis de covenants'
                },
                {
                    'id': 'PAS-03',
                    'procedure': 'Verificación de devengo de intereses',
                    'methodology': 'Recalcular intereses devengados al cierre',
                    'sample_size': 'Todos los préstamos',
                    'evidence': 'Cálculo de intereses, extractos'
                },
                {
                    'id': 'PAS-04',
                    'procedure': 'Análisis de clasificación corriente/no corriente',
                    'methodology': 'Verificar clasificación temporal según vencimientos',
                    'sample_size': 'Todos los préstamos',
                    'evidence': 'Cuadro de vencimientos'
                }
            ],
            'medium': [
                {
                    'id': 'PAS-01',
                    'procedure': 'Confirmaciones de deuda',
                    'methodology': 'Confirmar préstamos significativos',
                    'sample_size': 'Préstamos > materialidad',
                    'evidence': 'Confirmaciones'
                },
                {
                    'id': 'PAS-02',
                    'procedure': 'Revisión de intereses',
                    'methodology': 'Verificar razonabilidad de intereses',
                    'sample_size': 'Analítico',
                    'evidence': 'Análisis de tipos'
                }
            ],
            'low': [
                {
                    'id': 'PAS-01',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de endeudamiento',
                    'sample_size': 'N/A',
                    'evidence': 'Ratios financieros'
                }
            ]
        },
        'ingresos': {
            'high': [
                {
                    'id': 'ING-01',
                    'procedure': 'Prueba de corte de ingresos',
                    'methodology': 'Verificar reconocimiento de ingresos en periodo correcto',
                    'sample_size': '15 últimas y primeras ventas',
                    'evidence': 'Facturas, albaranes, condiciones de venta'
                },
                {
                    'id': 'ING-02',
                    'procedure': 'Circularización de clientes (ver Deudores)',
                    'methodology': 'Confirmaciones externas de saldos',
                    'sample_size': '30 clientes',
                    'evidence': 'Confirmaciones'
                },
                {
                    'id': 'ING-03',
                    'procedure': 'Análisis de contratos y condiciones',
                    'methodology': 'Revisar políticas de reconocimiento de ingresos',
                    'sample_size': 'Contratos significativos',
                    'evidence': 'Contratos, memorandos'
                },
                {
                    'id': 'ING-04',
                    'procedure': 'Prueba de descuentos y devoluciones',
                    'methodology': 'Verificar registro adecuado de descuentos y devoluciones',
                    'sample_size': 'Muestra de 20 operaciones',
                    'evidence': 'Notas de crédito, contratos'
                }
            ],
            'medium': [
                {
                    'id': 'ING-01',
                    'procedure': 'Prueba de corte',
                    'methodology': 'Verificar corte de ventas',
                    'sample_size': '10 operaciones',
                    'evidence': 'Facturas y albaranes'
                },
                {
                    'id': 'ING-02',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de márgenes y tendencias',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ],
            'low': [
                {
                    'id': 'ING-01',
                    'procedure': 'Procedimientos analíticos sustantivos',
                    'methodology': 'Análisis de tendencias',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ]
        },
        'compras': {
            'high': [
                {
                    'id': 'COM-01',
                    'procedure': 'Prueba de corte de compras',
                    'methodology': 'Verificar registro de compras en periodo correcto',
                    'sample_size': '15 últimas y primeras compras',
                    'evidence': 'Facturas, albaranes, registros'
                },
                {
                    'id': 'COM-02',
                    'procedure': 'Circularización de proveedores',
                    'methodology': 'Confirmaciones externas de saldos',
                    'sample_size': '25 proveedores principales',
                    'evidence': 'Confirmaciones'
                },
                {
                    'id': 'COM-03',
                    'procedure': 'Búsqueda de pasivos no registrados',
                    'methodology': 'Revisar facturas recibidas tras el cierre',
                    'sample_size': 'Facturas de 2 meses posteriores',
                    'evidence': 'Facturas posteriores'
                },
                {
                    'id': 'COM-04',
                    'procedure': 'Análisis de variación de existencias',
                    'methodology': 'Conciliar compras con variación de existencias',
                    'sample_size': 'N/A - Analítico',
                    'evidence': 'Conciliación'
                }
            ],
            'medium': [
                {
                    'id': 'COM-01',
                    'procedure': 'Prueba de corte',
                    'methodology': 'Verificar corte de compras',
                    'sample_size': '10 operaciones',
                    'evidence': 'Facturas'
                },
                {
                    'id': 'COM-02',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de costes',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ],
            'low': [
                {
                    'id': 'COM-01',
                    'procedure': 'Procedimientos analíticos sustantivos',
                    'methodology': 'Análisis de tendencias',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ]
        },
        'gastos_personal': {
            'high': [
                {
                    'id': 'PER-01',
                    'procedure': 'Revisión de nóminas y liquidaciones',
                    'methodology': 'Verificar cálculo de nóminas y retenciones',
                    'sample_size': 'Muestra de 15 empleados',
                    'evidence': 'Nóminas, contratos, liquidaciones'
                },
                {
                    'id': 'PER-02',
                    'procedure': 'Prueba de provisiones laborales',
                    'methodology': 'Recalcular vacaciones y pagas devengadas',
                    'sample_size': 'Todos los empleados',
                    'evidence': 'Cálculo de provisiones'
                },
                {
                    'id': 'PER-03',
                    'procedure': 'Verificación de Seguridad Social',
                    'methodology': 'Conciliar pagos con declaraciones TC1 y TC2',
                    'sample_size': 'Todos los meses',
                    'evidence': 'TC1, TC2, justificantes de pago'
                },
                {
                    'id': 'PER-04',
                    'procedure': 'Revisión de indemnizaciones',
                    'methodology': 'Verificar cálculo y tratamiento de indemnizaciones',
                    'sample_size': 'Todas las indemnizaciones',
                    'evidence': 'Cartas de despido, finiquitos'
                }
            ],
            'medium': [
                {
                    'id': 'PER-01',
                    'procedure': 'Revisión selectiva de nóminas',
                    'methodology': 'Verificar muestra de nóminas',
                    'sample_size': '10 empleados',
                    'evidence': 'Nóminas'
                },
                {
                    'id': 'PER-02',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de plantilla y costes',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ],
            'low': [
                {
                    'id': 'PER-01',
                    'procedure': 'Procedimientos analíticos sustantivos',
                    'methodology': 'Análisis de tendencias de personal',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ]
        },
        'servicios_exteriores': {
            'high': [
                {
                    'id': 'SER-01',
                    'procedure': 'Prueba detallada de servicios',
                    'methodology': 'Verificar facturas y devengo de servicios',
                    'sample_size': '30 facturas significativas',
                    'evidence': 'Facturas, contratos'
                },
                {
                    'id': 'SER-02',
                    'procedure': 'Análisis de servicios con vinculadas',
                    'methodology': 'Identificar y analizar servicios con partes vinculadas',
                    'sample_size': 'Todas las transacciones con vinculadas',
                    'evidence': 'Contratos, facturas, análisis de mercado'
                },
                {
                    'id': 'SER-03',
                    'procedure': 'Revisión de provisiones de servicios',
                    'methodology': 'Verificar servicios devengados no facturados',
                    'sample_size': 'N/A - Analítico',
                    'evidence': 'Contratos, estimaciones'
                }
            ],
            'medium': [
                {
                    'id': 'SER-01',
                    'procedure': 'Prueba selectiva de servicios',
                    'methodology': 'Verificar muestra de facturas',
                    'sample_size': '20 facturas',
                    'evidence': 'Facturas'
                },
                {
                    'id': 'SER-02',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de tendencias',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ],
            'low': [
                {
                    'id': 'SER-01',
                    'procedure': 'Procedimientos analíticos sustantivos',
                    'methodology': 'Análisis comparativo',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ]
        },
        'impuestos': {
            'high': [
                {
                    'id': 'IMP-01',
                    'procedure': 'Revisión de declaraciones fiscales',
                    'methodology': 'Revisar modelos 200, 303, 347 y conciliar con contabilidad',
                    'sample_size': 'Todas las declaraciones',
                    'evidence': 'Declaraciones, conciliaciones'
                },
                {
                    'id': 'IMP-02',
                    'procedure': 'Cálculo del impuesto de sociedades',
                    'methodology': 'Recalcular cuota íntegra y líquida',
                    'sample_size': 'Completo',
                    'evidence': 'Cálculo independiente, modelo 200'
                },
                {
                    'id': 'IMP-03',
                    'procedure': 'Análisis de diferencias temporarias',
                    'methodology': 'Verificar activos y pasivos por impuesto diferido',
                    'sample_size': 'Todas las diferencias',
                    'evidence': 'Cuadro de diferencias temporarias'
                },
                {
                    'id': 'IMP-04',
                    'procedure': 'Revisión de ejercicios abiertos a inspección',
                    'methodology': 'Evaluar contingencias fiscales',
                    'sample_size': 'Últimos 4 ejercicios',
                    'evidence': 'Análisis de riesgos, consulta con asesores'
                }
            ],
            'medium': [
                {
                    'id': 'IMP-01',
                    'procedure': 'Revisión de declaraciones',
                    'methodology': 'Revisar modelos fiscales',
                    'sample_size': 'Principales',
                    'evidence': 'Declaraciones'
                },
                {
                    'id': 'IMP-02',
                    'procedure': 'Procedimientos analíticos',
                    'methodology': 'Análisis de tipo efectivo',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ],
            'low': [
                {
                    'id': 'IMP-01',
                    'procedure': 'Procedimientos analíticos sustantivos',
                    'methodology': 'Análisis de tipo efectivo',
                    'sample_size': 'N/A',
                    'evidence': 'Análisis'
                }
            ]
        },
        'partes_vinculadas': {
            'high': [
                {
                    'id': 'VIN-01',
                    'procedure': 'Identificación de partes vinculadas',
                    'methodology': 'Obtener listado completo de partes vinculadas y verificar con registros',
                    'sample_size': 'Todas las partes vinculadas',
                    'evidence': 'Declaraciones de la dirección, Registro Mercantil'
                },
                {
                    'id': 'VIN-02',
                    'procedure': 'Análisis de transacciones con vinculadas',
                    'methodology': 'Detallar todas las transacciones y saldos',
                    'sample_size': 'Todas las transacciones',
                    'evidence': 'Listado de transacciones, contratos'
                },
                {
                    'id': 'VIN-03',
                    'procedure': 'Evaluación de precios de transferencia',
                    'methodology': 'Verificar si las transacciones están a valor de mercado',
                    'sample_size': 'Transacciones significativas',
                    'evidence': 'Estudios de precios, comparables de mercado'
                },
                {
                    'id': 'VIN-04',
                    'procedure': 'Revisión de desglose en memoria',
                    'methodology': 'Verificar información revelada en memoria',
                    'sample_size': 'Completo',
                    'evidence': 'Memoria, check-list de revelación'
                }
            ],
            'medium': [
                {
                    'id': 'VIN-01',
                    'procedure': 'Identificación de vinculadas',
                    'methodology': 'Obtener y verificar listado',
                    'sample_size': 'Todas',
                    'evidence': 'Listado'
                },
                {
                    'id': 'VIN-02',
                    'procedure': 'Revisión de transacciones significativas',
                    'methodology': 'Analizar transacciones materiales',
                    'sample_size': 'Transacciones > materialidad',
                    'evidence': 'Contratos'
                }
            ],
            'low': [
                {
                    'id': 'VIN-01',
                    'procedure': 'Indagación sobre vinculadas',
                    'methodology': 'Indagar con dirección',
                    'sample_size': 'N/A',
                    'evidence': 'Carta de manifestaciones'
                }
            ]
        }
    }
    
    def __init__(self, config: Dict, risk_matrix: pd.DataFrame):
        """Initialize work program generator"""
        self.config = config
        self.risk_matrix = risk_matrix
        self.logger = logging.getLogger(__name__)
        self.custom_procedures = {}  # Store custom procedures created for this audit
    
    def generate_work_program(self, area_key: str, year: int) -> Dict[str, Any]:
        """
        Generate work program for a specific audit area based on risk assessment
        
        Args:
            area_key: Audit area identifier
            year: Audit year
            
        Returns:
            Dictionary with work program details
        """
        # Get risk assessment for this area
        area_risk = self.risk_matrix[self.risk_matrix['area_key'] == area_key].iloc[0]
        
        risk_level = area_risk['combined_risk']
        
        # Get standard procedures for this risk level
        procedures = self.PROCEDURES_LIBRARY.get(area_key, {}).get(risk_level, [])
        
        # Check if there are custom procedures for this area
        if area_key in self.custom_procedures:
            procedures = procedures + self.custom_procedures[area_key]
        
        work_program = {
            'area_key': area_key,
            'area_name': area_risk['area_name'],
            'year': year,
            'risk_level': risk_level,
            'significance': area_risk['significance_pct'],
            'procedures': procedures,
            'total_procedures': len(procedures),
            'generated_date': datetime.now().isoformat()
        }
        
        self.logger.info(f"Generated work program for {area_key}: {len(procedures)} procedures")
        
        return work_program
    
    def add_custom_procedure(self, area_key: str, procedure: Dict[str, str]):
        """
        Add a custom procedure for a specific area
        This allows AI or users to create new procedures for specific audit circumstances
        
        Args:
            area_key: Audit area
            procedure: Procedure dictionary with id, procedure, methodology, sample_size, evidence
        """
        if area_key not in self.custom_procedures:
            self.custom_procedures[area_key] = []
        
        self.custom_procedures[area_key].append(procedure)
        self.logger.info(f"Added custom procedure {procedure['id']} to {area_key}")
    
    def export_work_program(self, work_program: Dict, output_dir: str = './papeles_trabajo') -> str:
        """Export work program to Excel file"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d')
        area_name_clean = work_program['area_name'].replace(' ', '_')
        filename = f"PT_Programa_Trabajo_{area_name_clean}_{work_program['year']}_{timestamp}.xlsx"
        filepath = Path(output_dir) / filename
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Programa de Trabajo"
        
        # Title
        ws.merge_cells('A1:G1')
        title_cell = ws['A1']
        title_cell.value = f"PROGRAMA DE TRABAJO - {work_program['area_name'].upper()}"
        title_cell.font = Font(bold=True, size=14, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Metadata
        ws['A3'] = "Ejercicio:"
        ws['B3'] = work_program['year']
        ws['A4'] = "Nivel de Riesgo:"
        ws['B4'] = work_program['risk_level'].upper()
        ws['A5'] = "Significatividad:"
        ws['B5'] = f"{work_program['significance']:.2f}%"
        ws['A6'] = "Total Procedimientos:"
        ws['B6'] = work_program['total_procedures']
        
        # Color code risk
        risk_cell = ws['B4']
        if work_program['risk_level'] == 'high':
            risk_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        elif work_program['risk_level'] == 'medium':
            risk_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        else:
            risk_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        
        # Headers
        headers = ['ID', 'Procedimiento', 'Metodología', 'Tamaño Muestra', 'Evidencia', 'Realizado', 'Ref. PT']
        header_row = 8
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        # Procedures
        for row_idx, procedure in enumerate(work_program['procedures'], start=header_row+1):
            ws.cell(row=row_idx, column=1, value=procedure['id'])
            ws.cell(row=row_idx, column=2, value=procedure['procedure'])
            ws.cell(row=row_idx, column=3, value=procedure['methodology'])
            ws.cell(row=row_idx, column=4, value=procedure['sample_size'])
            ws.cell(row=row_idx, column=5, value=procedure['evidence'])
            ws.cell(row=row_idx, column=6, value='')  # To be filled during audit
            ws.cell(row=row_idx, column=7, value='')  # To be filled during audit
            
            # Wrap text
            for col in range(1, 8):
                ws.cell(row=row_idx, column=col).alignment = Alignment(wrap_text=True, vertical='top')
        
        # Column widths
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 50
        ws.column_dimensions['D'].width = 25
        ws.column_dimensions['E'].width = 35
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 12
        
        # Row heights
        ws.row_dimensions[1].height = 30
        for row in range(header_row+1, header_row+1+len(work_program['procedures'])):
            ws.row_dimensions[row].height = 60
        
        wb.save(filepath)
        self.logger.info(f"Work program exported to {filepath}")
        
        return str(filepath)
    
    def generate_all_work_programs(self, year: int, output_dir: str = './papeles_trabajo') -> List[str]:
        """Generate work programs for all areas in the risk matrix"""
        self.logger.info(f"Generating work programs for all areas - year {year}")
        
        generated_files = []
        
        for _, area_row in self.risk_matrix.iterrows():
            area_key = area_row['area_key']
            
            # Only generate if area is material or high/medium risk
            if area_row['material'] or area_row['combined_risk'] in ['high', 'medium']:
                work_program = self.generate_work_program(area_key, year)
                filepath = self.export_work_program(work_program, output_dir)
                generated_files.append(filepath)
        
        self.logger.info(f"Generated {len(generated_files)} work programs")
        
        return generated_files
    
    def save_custom_procedures_template(self, output_dir: str = './templates/audit_programs'):
        """
        Save custom procedures as template for future audits
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"custom_procedures_template_{timestamp}.json"
        filepath = Path(output_dir) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.custom_procedures, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Custom procedures template saved to {filepath}")
        
        return str(filepath)
    
    def load_custom_procedures_template(self, template_path: str):
        """Load custom procedures from a previous audit template"""
        with open(template_path, 'r', encoding='utf-8') as f:
            self.custom_procedures = json.load(f)
        
        self.logger.info(f"Loaded custom procedures from {template_path}")
