# Burns critical care unit - information system

The information system will be a full stack system that can handle the following taks, followed by the name of the task:
- connet to a google sheet and obtain data from the google sheet - google_sheet_tools
- control the quality of the data in the google sheet - quality_control_tools
- transform pdf files containing medical texts about admission and release of patients from a burns critical care unit and parse them in markdown file - pdf_parser_markdown
- merge, clean and tranform the markdown files to be ready to be analyzed by AI agents - markdown_transformer
- make the content of the markdown files anonym for security and privacy purposes - markdown_anonymizer
- create pydantic classes to make the extraction of data from the files typed and structured - pydantic_classifier
- use pydantic ai agents to extract the data from the files using the pydantic classes - pydantic_extracter
- save all the extracted data as json - json_saver
- manage a mongodb - mongodb_manager
- perform CRUD operations of the mongodb using fastAPI - crud_performer
- use a react js frontend for interaction with the user - react_UI

# python libraries needed
The basic python libraries needed are:
- pydantic
- pydantic ai
- fastAPI
