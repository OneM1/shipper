# Shipper 🚢

**Document Compliance Checker for Exporters**

Document compliance checker for Chinese exporters shipping to US/EU. Catches documentation errors before shipments leave port.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## Features

- 📄 **Document Upload**: Support for PDF, JPG, PNG formats via drag-and-drop
- 🔍 **OCR + LLM Extraction**: Automatically extracts key fields from documents
- ✅ **Compliance Validation**: Checks HS codes, invoice values, shipper/consignee info, product descriptions, dates
- 🔗 **Cross-Document Validation**: Ensures consistency between invoice and packing list
- 🌐 **Bilingual Reports**: Chinese UI with bilingual compliance reports
- 📥 **PDF Report Download**: Generate professional PDF reports
- 📝 **Fix Instructions**: Specific guidance on how to correct errors

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **OCR**: PyPDF for text extraction
- **PDF Generation**: ReportLab
- **Validation**: Pydantic v2 models

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **File Upload**: react-dropzone

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend Setup

```bash
cd backend
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

API docs available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/documents/upload` | Upload invoice + packing list |
| GET | `/api/v1/documents/{id}/status` | Check processing status |
| GET | `/api/v1/documents/{id}/report` | Get compliance report (JSON) |
| GET | `/api/v1/documents/{id}/report.pdf` | Download PDF report |
| GET | `/api/v1/documents/{id}/fields` | Get extracted fields |

### Example API Usage

```bash
# Upload documents
curl -X POST http://localhost:8001/api/v1/documents/upload \
  -F "invoice=@invoice.pdf" \
  -F "packing_list=@packing_list.pdf"

# Get report
curl http://localhost:8001/api/v1/documents/{document_id}/report

# Download PDF
curl -O -J http://localhost:8001/api/v1/documents/{document_id}/report.pdf
```

## Validation Rules

The system checks these fields:

| Field | Rule | Error Message (CN) |
|-------|------|-------------------|
| HS Code | 6-10 digits | "HS code missing or invalid" |
| Invoice Value | Present with currency | "Total invoice value missing" |
| Shipper Name | Non-empty, >2 chars | "Shipper name incomplete" |
| Consignee Name | Non-empty, >2 chars | "Consignee name incomplete" |
| Consignee Address | Non-empty, >10 chars | "Consignee address incomplete" |
| Product Description | Non-empty, specific | "Product description too vague" |
| Invoice Date | Present | "Missing required date" |
| Cross-Document | Item counts match | "Item count mismatch" |

## Project Structure

```
shipper-lite/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Configuration
│   │   ├── models/       # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   │   ├── document_parser.py
│   │   │   ├── validation_engine.py
│   │   │   ├── report_generator.py
│   │   │   └── pdf_generator.py
│   │   └── main.py       # FastAPI entry point
│   ├── tests/            # Test suite
│   └── pyproject.toml
├── frontend/             # React frontend
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   └── App.tsx
│   └── package.json
├── testdata/             # Test PDFs
│   └── real_samples/     # Real-world samples
├── test_integration.py   # Integration tests
└── README.md
```




## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Document templates from FedEx, DHL, TNT, UPS
- Test data generated for demonstration purposes

---


