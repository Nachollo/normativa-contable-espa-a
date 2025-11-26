# Sistema de Procesamiento de Documentos de Auditoría

Sistema avanzado de procesamiento y clasificación de documentos para auditorías contables, con capacidades de IA, procesamiento masivo y generación automática de papeles de trabajo.

## 🚀 Características Principales

### Procesamiento Prioritario de Documentos Contables
- **Balances de Sumas y Saldos**: Carga prioritaria con detalle mínimo de 4 dígitos
- **Diarios Contables**: Procesamiento de libros diarios completos en Excel
- **Múltiples Ejercicios**: Soporte para 3 ejercicios o más (comparativas)
- **Base de Datos Contable**: Sistema de consultas integrado para toda la auditoría

### Inteligencia Artificial
- **Clasificación Inteligente**: Usando modelos de IA (OpenAI GPT-4 o modelos locales)
- **OCR Avanzado**: Procesamiento de documentos escaneados con preprocesamiento de imagen
- **Extracción con IA**: Extracción inteligente de datos usando modelos de lenguaje

### Procesamiento Masivo Robusto
- **Carga por Lotes**: Procesamiento paralelo de grandes cantidades de documentos
- **Deduplicación**: Detección automática de documentos duplicados por hash
- **Gestión de Colas**: Sistema de prioridades y reintentos automáticos
- **Múltiples Fuentes**: Carga desde múltiples directorios simultáneamente

### Tipos de Documentos Soportados (15+ tipos)
- **Facturas** (Invoices)
- **Contratos** (Contracts)  
- **Nóminas** (Payrolls)
- **Balances** (Balance Sheets)
- **Recibos** (Receipts)
- **Escrituras** (Notarial Deeds)
- **Justificantes de Pago** (Payment Receipts)
- **Extractos Bancarios** (Bank Statements)
- **CIRBE** (Credit Risk Reports)
- **Declaraciones Fiscales** (Tax Declarations)
- **Respuestas de Circularización** (Audit Confirmations)
- **Albaranes** (Delivery Notes)
- **RLC** (Commercial Registry)
- **RNT** (Property Registry)
- **Documentos sin clasificar**

### Generación de Papeles de Trabajo
- **Balances Comparativos**: Análisis multi-ejercicio automático
- **Detalles por Cuenta**: Papeles de trabajo individuales por cuenta
- **Resumen por Áreas**: Agrupación automática por áreas de auditoría
- **Ratios Financieros**: Cálculo automático de indicadores
- **Formato Excel**: Salidas formateadas y profesionales

## 📄 Formatos de Archivo Soportados (25+ formatos)

### Documentos
- **PDF**: Documentos PDF con texto extraíble y escaneados (con OCR)
- **Texto**: .txt, .rtf

### Microsoft Office (todas las versiones)
- **Word**: .doc, .docx, .docm, .dot, .dotx
- **Excel**: .xls, .xlsx, .xlsm, .xlsb, .xlt, .xltx
- **PowerPoint**: .ppt, .pptx, .pptm, .pps, .ppsx

### LibreOffice/OpenOffice
- **Writer**: .odt
- **Calc**: .ods
- **Impress**: .odp
- **Draw**: .odg
- **Formula**: .odf

### Imágenes (con OCR avanzado)
- .jpg, .jpeg, .png, .bmp, .tiff, .tif, .gif

### Email
- **Outlook**: .msg
- **Email estándar**: .eml

### Datos
- **CSV**: .csv, .tsv
- **JSON**: .json
- **XML**: .xml

### Google Workspace (versiones exportadas)
- Google Docs, Sheets, Slides

## 📦 Instalación

### Requisitos Previos
- Python 3.8 o superior
- 8GB RAM mínimo (16GB recomendado para procesamiento masivo)
- Tesseract OCR para procesamiento de imágenes

### Instalación Paso a Paso

1. **Clona el repositorio**:
```bash
git clone https://github.com/Nachollo/normativa-contable-espa-a.git
cd normativa-contable-espa-a
```

2. **Instala las dependencias**:
```bash
pip install -r requirements.txt
```

3. **Instala Tesseract OCR** (para procesamiento de imágenes):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng
sudo apt-get install poppler-utils  # Para PDF a imagen

# macOS
brew install tesseract tesseract-lang poppler

# Windows
# Descarga e instala:
# - Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# - Poppler: https://github.com/oschwartz10612/poppler-windows/releases
```

4. **Descarga modelos de IA** (opcional, para clasificación local):
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

5. **Configura el sistema**:
```bash
python setup.py
```

## 🎯 Uso del Sistema

### FASE 1: Carga Prioritaria de Documentos Contables

**IMPORTANTE**: Los balances y diarios deben cargarse PRIMERO ya que son la base de toda la auditoría.

1. **Prepara los archivos contables** en formato Excel:
   - `balance_2023.xlsx` - Balance de sumas y saldos ejercicio 2023
   - `diario_2023.xlsx` - Libro diario ejercicio 2023
   - `balance_2022.xlsx` - Balance de sumas y saldos ejercicio 2022
   - `diario_2022.xlsx` - Libro diario ejercicio 2022
   - (Y ejercicios anteriores si están disponibles)

2. **Estructura requerida en los Excel**:
   
   **Balance de Sumas y Saldos:**
   - Código de cuenta (mínimo 4 dígitos, ideal hasta máximo detalle)
   - Nombre de cuenta
   - Suma Debe
   - Suma Haber
   - Saldo Deudor
   - Saldo Acreedor
   
   **Libro Diario:**
   - Número de asiento
   - Fecha
   - Código de cuenta
   - Nombre de cuenta  
   - Debe (cargo)
   - Haber (abono)
   - Concepto/Descripción

3. **Ejecuta la carga prioritaria**:
```bash
python main_audit.py --load-accounting
```

### FASE 2: Procesamiento Masivo de Otros Documentos

Una vez cargados los balances y diarios, procesa el resto de documentos:

```bash
# Procesar documentos en carpeta por defecto
python main_audit.py --process-bulk

# Procesar desde directorio específico
python main_audit.py --process-bulk --input-dir /ruta/a/documentos
```

### Modo Interactivo (Consultas en Tiempo Real)

```bash
python main_audit.py --interactive
```

Comandos disponibles:
- `query <cuenta> [año]` - Consultar saldo de una cuenta
- `detail <cuenta> <año>` - Generar papel de trabajo detallado
- `wp <año>` - Generar papeles de trabajo completos del año
- `exit` - Salir

### Procesamiento Completo Automatizado

```bash
# Procesa todo: carga contable + documentos + genera papeles
python main_audit.py
```

### Ejemplos de Uso

**Ejemplo 1: Consultar cuenta específica**
```bash
python main_audit.py -i
> query 430 2023
# Muestra saldo y movimientos de clientes
```

**Ejemplo 2: Generar papel de trabajo de clientes**
```bash
python main_audit.py -i
> detail 430 2023
# Genera Excel detallado con todos los movimientos
```

**Ejemplo 3: Procesar 10,000 documentos**
```bash
# Coloca los documentos en input_documents/
python main_audit.py --process-bulk
# El sistema los procesa en paralelo con barra de progreso
```

## Estructura de carpetas

```
normativa-contable-espa-a/
├── input_documents/           # Documentos a procesar
├── classified_documents/      # Documentos clasificados
│   ├── factura/              # Facturas
│   ├── contrato/             # Contratos
│   ├── nomina/               # Nóminas
│   ├── balance/              # Balances
│   ├── recibo/               # Recibos
│   └── sin_clasificar/       # Documentos no clasificados
├── backup/                   # Copias de seguridad
├── extraction_results/       # Resultados de extracción
├── templates/                # Plantillas de extracción
├── logs/                     # Archivos de log
└── src/                      # Código fuente
```

## Configuración

El archivo `config.json` permite personalizar:

- Tipos de documentos y palabras clave
- Umbral de confianza para clasificación
- Configuración de extracción de datos
- Carpetas de entrada y salida

### Ejemplo de configuración:

```json
{
  "input_folder": "./input_documents",
  "output_folder": "./classified_documents",
  "document_types": {
    "factura": {
      "keywords": ["factura", "invoice", "bill", "pago", "importe", "total", "iva"],
      "extensions": [".pdf", ".jpg", ".jpeg", ".png"],
      "template": "factura_template.json"
    }
  },
  "classification": {
    "confidence_threshold": 0.6,
    "unknown_folder": "sin_clasificar"
  }
}
```

## Plantillas de extracción

Las plantillas definen qué datos extraer de cada tipo de documento. Se almacenan en formato JSON en la carpeta `templates/`.

### Ejemplo de plantilla para facturas:

```json
{
  "name": "Factura Template",
  "fields": {
    "numero_factura": {
      "patterns": [
        "(?:factura|invoice)[\s#]*:?\s*([A-Z0-9\-\/]+)"
      ],
      "type": "string",
      "required": true
    },
    "importe_total": {
      "patterns": [
        "total[\s:]*([0-9,\.]+)[\s]*€?"
      ],
      "type": "decimal",
      "required": true
    }
  }
}
```

## Personalización

### Añadir nuevos tipos de documentos

1. Edita `config.json` para añadir el nuevo tipo
2. Crea una plantilla de extracción en `templates/`
3. El sistema creará automáticamente la carpeta correspondiente

### Crear plantillas personalizadas

Las plantillas usan expresiones regulares para extraer datos. Campos disponibles:

- `patterns`: Lista de expresiones regulares
- `type`: Tipo de dato (string, decimal, integer, date, array)
- `required`: Si el campo es obligatorio

## API del código

### DocumentClassifier

```python
from src.document_classifier import DocumentClassifier

classifier = DocumentClassifier(config)
result = classifier.classify_document(file_path)
```

### FolderOrganizer

```python
from src.folder_organizer import FolderOrganizer

organizer = FolderOrganizer(config)
new_path = organizer.organize_document(file_path, document_type)
```

### DataExtractor

```python
from src.data_extractor import DataExtractor

extractor = DataExtractor(config)
result = extractor.extract_data(file_path, document_type)
```

## Logging

Los logs se guardan en `logs/document_agent.log` y incluyen:

- Información de procesamiento
- Errores y advertencias
- Estadísticas de clasificación
- Resultados de extracción

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## Soporte

Para reportar bugs o solicitar features, por favor abre un issue en GitHub.