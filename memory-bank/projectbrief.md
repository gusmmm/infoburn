# Burns Critical Care Unit Information System

## Project Overview
A full-stack information system designed to manage and process medical data for a burns critical care unit. The system will handle data from multiple sources, ensure privacy compliance, and provide structured data for analysis.

## Core Requirements

### Data Sources Integration
- Connect to and extract data from Google Sheets
- Parse PDF files containing medical texts (admission/release records)
- Transform medical records into structured data

### Data Processing
- Quality control for Google Sheets data
- Convert PDF content to markdown format
- Anonymize medical data for privacy compliance
- Structure data using Pydantic classes
- Extract data using AI agents

### Data Storage & Management
- Store processed data as JSON
- MongoDB database integration
- CRUD operations via FastAPI

### User Interface
- React-based frontend for user interaction
- Intuitive interface for medical staff

## Technical Stack
- Backend: Python (FastAPI)
- Frontend: React
- Database: MongoDB
- AI: Pydantic AI, Google Gemini
- Data Format: JSON, Markdown

## Key Features
1. google_sheet_tools: Google Sheets data integration
2. quality_control_tools: Data quality management
3. pdf_parser_markdown: PDF to markdown conversion
4. markdown_transformer: Content preparation for AI analysis
5. markdown_anonymizer: Data anonymization
6. pydantic_classifier: Structured data typing
7. pydantic_extracter: AI-based data extraction
8. json_saver: Data persistence
9. mongodb_manager: Database management
10. crud_performer: API operations
11. react_UI: User interface

## Core Dependencies
- pydantic
- pydantic-ai
- fastapi
- Google Gen AI SDK
- pymongo
