

# create a function that returns a string with the template for the extraction prompt
# to be imported in burns_extracter.py
def get_extraction_prompt_template():
        
    template: str = """
        You are a specialized medical data extraction AI assistant. Your task is to meticulously analyze the following clinical case text, written in European Portuguese, and extract specific information related to burn injuries.

        **Source Text:**
        --- START TEXT ---
        {medical_text}
        --- END TEXT ---

        **Glossary for Reference (Portuguese Terms):**
        --- START GLOSSARY ---
        {glossary}
        --- END GLOSSARY ---

        **Extraction Task:**
        Extract the required information and structure it precisely according to the provided JSON schema. Adhere strictly to the schema's field names, types, and enum values.

        **Key Information to Extract:**
        1.  `tbsa`: Total Body Surface Area affected by burns (as a percentage, e.g., 15.5). If not mentioned, use `null`.
        2.  `burn_mechanism`: The primary mechanism causing the burn (e.g., "Heat", "Electrical discharge", "Chemicals"). Use one of the allowed enum values: {mechanism_enums}. If unclear or not mentioned, use `null`.
        3.  `accident_type`: The context of the accident (e.g., "domestic", "workplace"). Use one of the allowed enum values: {accident_enums}. If unclear or not mentioned, use `null`.
        4.  `agent`: The specific agent causing the burn (e.g., "fire", "hot water", "sulfuric acid", "high voltage"). If not mentioned, use `null`.
        5.  `wildfire`, `bonfire`, `fireplace`, `violence`, `suicide_attempt`: Boolean flags (true/false) indicating if these specific circumstances were involved. If not mentioned, use `null` or `false` if context implies absence.
        6.  `escharotomy`: Boolean flag (true/false) indicating if an escharotomy procedure was performed. If not mentioned, use `null` or `false`.
        7.  `associated_trauma`: A list of strings describing any other significant injuries sustained concurrently with the burns (e.g., ["fractured femur", "head injury"]). If none mentioned, use an empty list `[]`.
        8.  `burn_injuries`: A list detailing each distinct burn area. For each burn:
            *   `location`: Anatomical location (e.g., "head", "left hand", "anterior trunk"). Use one of the allowed enum values: {location_enums}.
            *   `laterality`: Side affected ("left", "right", "bilateral", "unspecified"). Use one of the allowed enum values: {laterality_enums}. Default to "unspecified" if not mentioned.
            *   `depth`: Depth of the burn (e.g., "1st degree", "2nd degree partial", "3rd degree"). Use one of the allowed enum values: {depth_enums}. If not mentioned, use `null`.
            *   `circumferencial`: Boolean flag (true/false) indicating if the burn encircles the body part. If not mentioned, use `null` or `false`.
            *   `provenance`: Include the exact sentence(s) or text fragment(s) from the original text that support the burn information you've extracted. Quote the relevant text directly, maintaining the original Portuguese wording.

        **Output Requirements:**
        - Return **only** a single, valid JSON object matching the schema. Do not include any explanatory text before or after the JSON.
        - If a specific piece of information is not found in the text, use `null` for optional fields or appropriate defaults (e.g., empty list `[]` for `associated_trauma`, `false` for boolean flags if absence is implied, "unspecified" for `laterality`). Do not guess or infer information not present.
        - Ensure all JSON structures (objects `{{}}`, arrays `[]`) are correctly formed and closed.
        - The patient identifier for this case is `{file_id}`. This ID should *not* be included in the JSON output itself, as it will be added later.
        - For the `provenance` field, always include the exact text snippets that support each burn injury finding, using direct quotes from the source text.

        **JSON Schema Reference (for structure validation):**
        ```json
        {schema_json}
        """

    return template


    """
    This function returns a string containing the template for the extraction prompt.
    The template is used in the burns_extracter.py file to extract information from clinical case texts.
    The template includes placeholders for the medical text, glossary, and JSON schema.
    """ 
