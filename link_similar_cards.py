import requests
from collections import defaultdict

# AnkiConnect API configuration
ANKI_CONNECT_URL = "http://localhost:8765"

def invoke(action, params):
    return requests.post(ANKI_CONNECT_URL, json={"action": action, "version": 6, "params": params}).json()

def find_duplicates_by_field(primary_field, fallback_field, note_type):
    """
    Find notes with duplicate content in a specific field within a specific note type.

    :param primary_field: The primary field to check for duplicates (e.g., "Reading").
    :param fallback_field: The fallback field to use if the primary field is empty (e.g., "Expression").
    :param note_type: The name of the note type to limit the search (e.g., "Core 2000 Vocabulary").
    :return: Dictionary where keys are duplicate values and values are lists of note IDs.
    """
    # Get all notes of the specified note type
    response = invoke("findNotes", {"query": f"note:\"{note_type}\""})
    note_ids = response.get("result", [])

    if not note_ids:
        print(f"No notes found with the note type '{note_type}'.")
        return {}

    # Fetch note details
    notes_response = invoke("notesInfo", {"notes": note_ids})
    notes_info = notes_response.get("result", [])

    # Organize notes by field content
    field_content_map = defaultdict(list)

    for note in notes_info:
        fields = note.get("fields", {})
        field_value = fields.get(primary_field, {}).get("value", "")
        if not field_value:
            field_value = fields.get(fallback_field, {}).get("value", "")
        if field_value:
            field_content_map[field_value].append(note)

    # Filter duplicates (field content with more than one note ID)
    duplicates = {k: v for k, v in field_content_map.items() if len(v) > 1}

    return duplicates

def find_expression_duplicates(expression_field, note_type):
    """
    Find notes with duplicate content in the Expression field.

    :param expression_field: The field to check for duplicates (e.g., "Expression").
    :param note_type: The name of the note type to limit the search (e.g., "Core 2000 Vocabulary").
    :return: Dictionary where keys are duplicate values and values are lists of note IDs.
    """
    # Get all notes of the specified note type
    response = invoke("findNotes", {"query": f"note:\"{note_type}\""})
    note_ids = response.get("result", [])

    if not note_ids:
        print(f"No notes found with the note type '{note_type}'.")
        return {}

    # Fetch note details
    notes_response = invoke("notesInfo", {"notes": note_ids})
    notes_info = notes_response.get("result", [])

    # Organize notes by Expression field content
    field_content_map = defaultdict(list)

    for note in notes_info:
        fields = note.get("fields", {})
        field_value = fields.get(expression_field, {}).get("value", "")
        if field_value:
            field_content_map[field_value].append(note)

    # Filter duplicates (field content with more than one note ID)
    duplicates = {k: v for k, v in field_content_map.items() if len(v) > 1}

    return duplicates

def update_similar_field(duplicates, primary_field, fallback_field):
    """
    Update the "Similar" field for each note with duplicates, 
    excluding the note itself and including the "Expression" and "Meaning" fields of other notes.

    :param duplicates: Dictionary of duplicate values and their associated notes.
    :param primary_field: The primary field being checked for duplicates (e.g., "Reading").
    :param fallback_field: The fallback field used when the primary field is empty (e.g., "Expression").
    """
    for content, notes in duplicates.items():
        for note in notes:
            note_id = note["noteId"]
            similar_entries = []
            for other_note in notes:
                if other_note["noteId"] != note_id:
                    expression = other_note["fields"].get("Expression", {}).get("value", "")
                    meaning = other_note["fields"].get("Meaning", {}).get("value", "")
                    similar_entries.append(f"{expression}: {meaning}")
            
            # Update the "Similar" field
            similar_field_value = "<br>".join(similar_entries)
            invoke("updateNoteFields", {
                "note": {
                    "id": note_id,
                    "fields": {
                        "Similar": similar_field_value
                    }
                }
            })

def update_alternative_field(expression_duplicates):
    """
    Update the "Alternative" field for each note with duplicates in the Expression field,
    excluding the note itself and including the "Meaning" fields of other notes.

    :param expression_duplicates: Dictionary of duplicate values and their associated notes.
    """
    for expression, notes in expression_duplicates.items():
        for note in notes:
            note_id = note["noteId"]
            alternative_meanings = []
            for other_note in notes:
                if other_note["noteId"] != note_id:
                    meaning = other_note["fields"].get("Meaning", {}).get("value", "")
                    if meaning:
                        alternative_meanings.append(meaning)

            # Update the "Alternative" field
            alternative_field_value = "<br>".join(alternative_meanings)
            invoke("updateNoteFields", {
                "note": {
                    "id": note_id,
                    "fields": {
                        "Alternative": alternative_field_value
                    }
                }
            })

def print_summary(duplicates):
    """
    Print a summary of similar notes grouped by the common field value.

    :param duplicates: Dictionary of duplicate values and their associated notes.
    """
    print("\nSummary of Similar Notes:")
    for content, notes in duplicates.items():
        print(f"Common Value: {content}")
        for note in notes:
            expression = note["fields"].get("Expression", {}).get("value", "")
            meaning = note["fields"].get("Meaning", {}).get("value", "")
            print(f"  {expression}: {meaning}")
        print("---")

if __name__ == "__main__":
    primary_field = "Reading"
    fallback_field = "Expression"
    expression_field = "Expression"
    note_type = "Core 2000 Vocabulary"

    # Find duplicates by primary and fallback fields
    duplicates = find_duplicates_by_field(primary_field, fallback_field, note_type)

    if duplicates:
        print(f"Found duplicates in field '{primary_field}' (with fallback '{fallback_field}') within note type '{note_type}':")
        update_similar_field(duplicates, primary_field, fallback_field)
        print("Updated the 'Similar' field for notes with duplicates.")
        print_summary(duplicates)
    else:
        print(f"No duplicates found in field '{primary_field}' (with fallback '{fallback_field}') within note type '{note_type}'.")

    # Find duplicates by Expression field
    expression_duplicates = find_expression_duplicates(expression_field, note_type)

    if expression_duplicates:
        print(f"\nFound duplicates in field '{expression_field}' within note type '{note_type}':")
        update_alternative_field(expression_duplicates)
        print("Updated the 'Alternative' field for notes with duplicate Expressions.")
        print_summary(expression_duplicates)
    else:
        print(f"No duplicates found in field '{expression_field}' within note type '{note_type}'.")
