#!/usr/bin/env python3
"""
Demo script para probar el agente de clasificación de documentos
"""

import os
import shutil
from pathlib import Path
from main import DocumentAgent


def create_demo_documents():
    """Crear documentos de demostración para probar el sistema"""
    demo_folder = Path("input_documents/demo")
    demo_folder.mkdir(parents=True, exist_ok=True)
    
    # Crear archivos de texto de ejemplo
    demo_files = {
        "factura_ejemplo.txt": """
        FACTURA #12345
        Fecha: 15/11/2023
        De: Empresa Ejemplo S.L.
        Para: Cliente Demo
        
        Concepto: Servicios de consultoría
        Importe base: 1000.00 €
        IVA (21%): 210.00 €
        Total: 1210.00 €
        """,
        
        "contrato_ejemplo.txt": """
        CONTRATO DE SERVICIOS
        
        Contrato de prestación de servicios entre Empresa ABC S.L.
        y Cliente XYZ S.A.
        
        Fecha inicio: 01/01/2024
        Fecha fin: 31/12/2024
        
        Las partes acuerdan los siguientes términos...
        """,
        
        "nomina_ejemplo.txt": """
        NÓMINA
        
        Empleado: Juan Pérez García
        Periodo: Noviembre 2023
        
        Salario bruto: 2500.00 €
        Deducciones: 520.00 €
        Salario neto: 1980.00 €
        """,
        
        "recibo_ejemplo.txt": """
        SuperMercado Central
        
        Fecha: 20/11/2023
        
        Productos varios
        Total: 45.60 €
        
        Pago: Tarjeta
        """,
        
        "documento_desconocido.txt": """
        Este es un documento que no pertenece a ninguna
        categoría específica y debería ir a la carpeta
        de documentos sin clasificar.
        """
    }
    
    for filename, content in demo_files.items():
        file_path = demo_folder / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"Creado: {file_path}")
    
    print(f"\nArchivos de demostración creados en: {demo_folder}")
    return demo_folder


def run_demo():
    """Ejecutar demostración del sistema"""
    print("=" * 60)
    print("DEMOSTRACIÓN DEL AGENTE DE CLASIFICACIÓN DE DOCUMENTOS")
    print("=" * 60)
    
    # Crear documentos de demostración
    print("\n1. Creando documentos de demostración...")
    demo_folder = create_demo_documents()
    
    # Mover archivos a la carpeta de entrada
    input_folder = Path("input_documents")
    print(f"\n2. Moviendo archivos a la carpeta de entrada: {input_folder}")
    
    for demo_file in demo_folder.glob("*.txt"):
        target_path = input_folder / demo_file.name
        shutil.copy2(demo_file, target_path)
        print(f"   Copiado: {demo_file.name}")
    
    # Limpiar carpeta demo
    shutil.rmtree(demo_folder)
    
    # Inicializar el agente
    print("\n3. Inicializando el agente de clasificación...")
    agent = DocumentAgent()
    
    # Procesar documentos
    print("\n4. Procesando documentos...")
    results = agent.process_documents()
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("RESULTADOS DEL PROCESAMIENTO")
    print("=" * 60)
    print(f"Documentos procesados: {results['processed']}")
    print(f"Documentos clasificados: {results['classified']}")
    print(f"Datos extraídos: {results['extracted']}")
    print(f"Errores: {results['errors']}")
    
    # Mostrar estadísticas de carpetas
    print("\n5. Estadísticas de clasificación:")
    folder_stats = agent.get_statistics()
    for doc_type, count in folder_stats.items():
        print(f"   {doc_type.capitalize()}: {count} documentos")
    
    # Mostrar estructura de carpetas
    print("\n6. Estructura de carpetas creada:")
    output_folder = Path("classified_documents")
    if output_folder.exists():
        for folder in output_folder.iterdir():
            if folder.is_dir():
                file_count = len(list(folder.glob("*")))
                print(f"   📁 {folder.name}/  ({file_count} archivos)")
                for file in folder.glob("*"):
                    if file.is_file():
                        print(f"      📄 {file.name}")
    
    print("\n" + "=" * 60)
    print("DEMOSTRACIÓN COMPLETADA")
    print("=" * 60)
    print("\nPuedes revisar:")
    print("- Documentos clasificados en: classified_documents/")
    print("- Resultados de extracción en: classified_documents/extraction_results/")
    print("- Logs del sistema en: logs/")
    print("- Copias de seguridad en: backup/")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\nDemostración interrumpida por el usuario")
    except Exception as e:
        print(f"\nError durante la demostración: {str(e)}")
        print("Asegúrate de que todas las dependencias estén instaladas.")