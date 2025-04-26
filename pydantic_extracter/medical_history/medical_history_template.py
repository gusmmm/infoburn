def get_medical_history_prompt_template():
        
    template: str = """
        You are a specialized medical data extraction AI assistant. Your task is to meticulously analyze the following clinical case text, written in European Portuguese, and extract information about the patient's previous medical history.

        **Source Text:**
        --- START TEXT ---
        {medical_text}
        --- END TEXT ---

        **Glossary for Reference (Portuguese Terms):**
        --- START GLOSSARY ---
        {glossary}
        --- END GLOSSARY ---

        **Extraction Task:**
        Extract the patient's previous medical history (diseases or conditions they had *before* the current burn incident) and structure it precisely according to the provided JSON schema. Adhere strictly to the schema's field names, types, and enum values.

        **Key Information to Extract:**
        1.  `previous_diseases`: A list of diseases or conditions the patient had prior to the current admission. For each disease:
            *   `name`: The name of the disease or condition, translated to standardized English medical terminology.
            *   `category`: The category of the disease based on standard classifications. Use one of the allowed enum values: {category_enums}.
            *   `provenance`: Include the exact sentence(s) or text fragment(s) from the original text that support the disease information you've extracted. Quote the relevant text directly, maintaining the original Portuguese wording.

        **Output Requirements:**
        - Return **only** a single, valid JSON object matching the schema. Do not include any explanatory text before or after the JSON.
        - If a specific piece of information is not found in the text, use appropriate defaults (e.g., "Unknown or Unspecified" for category).
        - Ensure all JSON structures (objects `{{}}`, arrays `[]`) are correctly formed and closed.
        - The patient identifier for this case should *not* be included in the JSON output itself, as it will be added later.
        - For the `provenance` field, always include the exact text snippets that support each disease finding, using direct quotes from the source text.

        **JSON Schema Reference (for structure validation):**
        ```json
        {schema_json}
        ```
        """

    return template