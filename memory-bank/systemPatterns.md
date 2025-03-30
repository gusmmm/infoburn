# System Patterns

## Architecture Overview

```mermaid
flowchart TD
    UI[React Frontend] --> API[FastAPI Backend]
    API --> DB[(MongoDB)]
    API --> AI[AI Processing Layer]
    API --> GS[Google Sheets Integration]
    
    subgraph Data Processing
        PDF[PDF Parser] --> MD[Markdown Converter]
        MD --> AN[Anonymizer]
        AN --> ST[Structure Builder]
        ST --> EX[Data Extractor]
    end
    
    API --> Data Processing
```

## Component Architecture

### Data Input Layer
1. Google Sheets Integration
   - Direct connection to sheets
   - Real-time data validation
   - Automated quality checks

2. PDF Processing Pipeline
   - PDF to markdown conversion
   - Text extraction and formatting
   - Document structure preservation

### Processing Layer
1. Data Anonymization
   - Pattern-based identification of sensitive data
   - Consistent anonymization rules
   - Audit logging of changes

2. Data Structuring
   - Pydantic model definitions
   - Type validation
   - Schema enforcement

3. AI Processing
   - Google Gemini integration
   - Intelligent data extraction
   - Pattern recognition

### Storage Layer
1. MongoDB Integration
   - Document-based storage
   - Flexible schema design
   - Efficient querying

2. JSON Management
   - Standardized format
   - Data validation
   - Version control

### API Layer
1. FastAPI Implementation
   - RESTful endpoints
   - Async operations
   - OpenAPI documentation

### Frontend Layer
1. React Components
   - Modular design
   - State management
   - Role-based views

## Design Patterns

### Data Processing
- Pipeline Pattern for PDF to structured data conversion
- Observer Pattern for real-time updates
- Strategy Pattern for different anonymization rules

### API Design
- Repository Pattern for database operations
- Facade Pattern for complex operations
- Factory Pattern for data transformations

### Security
- Authentication using JWT
- Role-based access control
- Data encryption at rest and in transit

## Technical Standards

### Code Organization
- Feature-based directory structure
- Clear separation of concerns
- Consistent naming conventions

### Error Handling
- Standardized error responses
- Comprehensive logging
- Graceful degradation

### Testing
- Unit tests for core functionality
- Integration tests for pipelines
- End-to-end testing for critical paths
