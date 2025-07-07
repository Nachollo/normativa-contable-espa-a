# Document Classification Agent

Este proyecto implementa un agente de clasificación de documentos que puede procesar documentos cargados de forma masiva, clasificarlos según su naturaleza y organizarlos en subcarpetas para posterior extracción de datos.

## Características

- **Clasificación automática**: Clasifica documentos basándose en contenido y nombre de archivo
- **Organización inteligente**: Organiza documentos en carpetas según su tipo
- **Extracción de datos**: Extrae datos estructurados usando plantillas predefinidas
- **Tipos de documentos soportados**:
  - Facturas
  - Contratos
  - Nóminas
  - Balances
  - Recibos
  - Documentos sin clasificar

## Formatos de archivo soportados

- **PDF**: Documentos PDF con texto extraíble
- **Word**: Documentos .docx y .doc
- **Excel**: Hojas de cálculo .xlsx y .xls
- **Imágenes**: .jpg, .jpeg, .png, .bmp, .tiff (con OCR)
- **Texto**: Archivos .txt

## Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/Nachollo/normativa-contable-espa-a.git
cd normativa-contable-espa-a
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Para OCR en imágenes, instala Tesseract:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# macOS
brew install tesseract tesseract-lang

# Windows
# Descarga e instala desde: https://github.com/UB-Mannheim/tesseract/wiki
```

## Uso

### Procesamiento básico

Coloca los documentos a clasificar en la carpeta `input_documents/` y ejecuta:

```bash
python main.py
```

### Modo vigilancia

Para procesar documentos automáticamente según se van añadiendo:

```bash
python main.py --watch
```

### Ver estadísticas

Para ver el estado actual de los documentos clasificados:

```bash
python main.py --stats
```

### Configuración personalizada

Puedes usar un archivo de configuración personalizado:

```bash
python main.py --config mi_config.json
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