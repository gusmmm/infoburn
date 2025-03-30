# Product Context

## Problem Statement
Healthcare providers in burns critical care units need an efficient system to:
- Digitize and structure patient admission/release records
- Ensure data quality and privacy compliance
- Enable seamless data analysis for improving patient care
- Maintain organized medical records across different data sources

## User Personas

### Medical Staff
- Need quick access to patient records
- Must be able to input/update patient data
- Require intuitive interface for daily operations

### Data Managers
- Responsible for data quality
- Need tools to anonymize sensitive information
- Manage data transformations and storage

### System Administrators
- Maintain database operations
- Manage user access and permissions
- Monitor system performance

## Workflow

1. Data Input
   - Medical staff enters data in Google Sheets
   - PDF documents are uploaded containing patient records
   - Quality control checks are automated

2. Data Processing
   - PDFs are converted to markdown format
   - Content is anonymized for privacy
   - Data is structured using Pydantic models
   - AI agents extract relevant information

3. Data Storage
   - Processed data is saved as JSON
   - MongoDB stores structured records
   - CRUD operations via FastAPI enable data management

4. User Interface
   - React frontend provides intuitive access
   - Different views for different user roles
   - Real-time data updates

## Success Criteria
- Reduced time in processing patient records
- Improved data accuracy and completeness
- Enhanced privacy compliance
- Better accessibility of patient data
- Seamless integration with existing workflows

## Privacy & Security
- All patient data must be anonymized
- Access controls for different user roles
- Secure data storage and transmission
- Audit trail for data modifications
