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


def update_similar_field_all(notes, duplicates, primary_field, fallback_field):
    """
    Overwrite the "Similar" field for all notes of the given note type. If duplicates are found, include them;
    otherwise, leave the field empty.

    :param notes: List of all notes in the given note type.
    :param duplicates: Dictionary of duplicate values and their associated notes.
    :param primary_field: The primary field being checked for duplicates (e.g., "Reading").
    :param fallback_field: The fallback field used when the primary field is empty (e.g., "Expression").
    """
    for note in notes:
        note_id = note["noteId"]
        similar_entries = []
        field_value = note["fields"].get(primary_field, {}).get("value", "")
        if not field_value:
            field_value = note["fields"].get(
                fallback_field, {}).get("value", "")

        if field_value in duplicates:
            for other_note in duplicates[field_value]:
                if other_note["noteId"] != note_id:
                    expression = other_note["fields"].get(
                        "Expression", {}).get("value", "")
                    meaning = other_note["fields"].get(
                        "Meaning", {}).get("value", "")
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


def update_alternative_field_all(notes, expression_duplicates):
    """
    Overwrite the "Alternative" field for all notes of the given note type. If duplicates are found in the Expression field,
    include the meanings of other notes; otherwise, leave the field empty.

    :param notes: List of all notes in the given note type.
    :param expression_duplicates: Dictionary of duplicate values and their associated notes.
    """
    for note in notes:
        note_id = note["noteId"]
        alternative_meanings = []
        field_value = note["fields"].get("Expression", {}).get("value", "")

        if field_value in expression_duplicates:
            for other_note in expression_duplicates[field_value]:
                if other_note["noteId"] != note_id:
                    meaning = other_note["fields"].get(
                        "Meaning", {}).get("value", "")
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


def print_summary(duplicates, field_name):
    """
    Print a summary of similar notes grouped by the common field value.

    :param duplicates: Dictionary of duplicate values and their associated notes.
    :param field_name: The name of the field being summarized.
    """
    print(f"\nSummary of {field_name} Duplicates:")
    for content, notes in duplicates.items():
        print(f"Common Value: {content}")
        for note in notes:
            expression = note["fields"].get("Expression", {}).get("value", "")
            meaning = note["fields"].get("Meaning", {}).get("value", "")
            print(f"  {expression}: {meaning}")
        print("---")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Process Anki notes for duplicates.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only print summaries without updating fields.")
    args = parser.parse_args()

    primary_field = "Reading"
    fallback_field = "Expression"
    expression_field = "Expression"
    note_type = "Core 2000 Vocabulary"

    # Get all notes of the given note type
    all_notes_response = invoke(
        "findNotes", {"query": f"note:\"{note_type}\""})
    all_note_ids = all_notes_response.get("result", [])

    if all_note_ids:
        all_notes_info = invoke(
            "notesInfo", {"notes": all_note_ids}).get("result", [])

        # Find duplicates by primary and fallback fields
        duplicates = find_duplicates_by_field(
            primary_field, fallback_field, note_type)

        # Print summary of Reading duplicates
        if duplicates:
            print_summary(duplicates, "Reading")
        else:
            print("No duplicates found in Reading field.")

        # Find duplicates by Expression field
        expression_duplicates = find_expression_duplicates(
            expression_field, note_type)

        if expression_duplicates:
            print_summary(expression_duplicates, "Expression")
        else:
            print(f"No duplicates found in field '{
                  expression_field}' within note type '{note_type}'.")

        # If not a dry run, update fields
        if not args.dry_run:
            print(f"Overwriting the 'Similar' field for all notes in note type '{
                  note_type}'...")
            update_similar_field_all(
                all_notes_info, duplicates, primary_field, fallback_field)
            print("Updated the 'Similar' field for all notes.")

            print(f"Overwriting the 'Alternative' field for all notes in note type '{
                  note_type}'...")
            update_alternative_field_all(all_notes_info, expression_duplicates)
            print("Updated the 'Alternative' field for all notes.")
    else:
        print(f"No notes found for note type '{note_type}'.")
