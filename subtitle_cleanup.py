import requests
import re

# Define the AnkiConnect API endpoint
ANKICONNECT_URL = "http://localhost:8765"

def invoke(action, params):
    return requests.post(ANKICONNECT_URL, json={"action": action, "version": 6, "params": params}).json()

# Define the regex pattern to match the substrings to be removed
pattern = r"[\(（]([^\(\)（）]|(([\(（][^\(\)（）]+[\)）])))+[\)）]"

# Function to remove matching substrings from a given field
def clean_field_content(content):
    return re.sub(pattern, "", content)

# Get all notes of the "Mining" note type
response = invoke("findNotes", params={"query": "note:Mining"})
if not response.get("result"):
    print("No notes found or AnkiConnect is not running.")
    exit()

note_ids = response["result"]

def process_notes(dry_run=True):
    for note_id in note_ids:
        note_response = invoke("notesInfo", params={"notes": [note_id]})
        if not note_response.get("result"):
            continue

        note = note_response["result"][0]
        fields = note.get("fields", {})

        # Check and optionally clean the "Subtitle Japanese" field
        if "Subtitle Japanese" in fields:
            original_content = fields["Subtitle Japanese"]["value"]
            cleaned_content = clean_field_content(original_content)
            if original_content != cleaned_content:
                print(f"Note ID {note_id}: 'Subtitle Japanese'\n  Old: {original_content}\n  New: {cleaned_content}")
                if not dry_run:
                    invoke("updateNoteFields", params={"note": {"id": note_id, "fields": {"Subtitle Japanese": cleaned_content}}})

        # Check and optionally clean the "Subtitle English" field
        if "Subtitle English" in fields:
            original_content = fields["Subtitle English"]["value"]
            cleaned_content = clean_field_content(original_content)
            if original_content != cleaned_content:
                print(f"Note ID {note_id}: 'Subtitle English'\n  Old: {original_content}\n  New: {cleaned_content}")
                if not dry_run:
                    invoke("updateNoteFields", params={"note": {"id": note_id, "fields": {"Subtitle English": cleaned_content}}})

# Perform a dry run first
print("Dry run: Changes that would be made:")
process_notes(dry_run=False)

# Uncomment the line below to perform actual updates after reviewing the dry run output
# process_notes(dry_run=False)

print("Processing complete.")
