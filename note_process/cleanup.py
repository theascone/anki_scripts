import json
import requests
from process import *

ANKICONNECT_URL = "http://127.0.0.1:8765"


def invoke(action, **params):
    """Helper function to interact with AnkiConnect."""
    return requests.post(
        ANKICONNECT_URL, json={"action": action,
                               "version": 6, "params": params}
    ).json()


def get_note(note_id):
    """Retrieve a note from Anki by its ID."""
    response = invoke("notesInfo", notes=[note_id])
    if response.get("error") is not None:
        raise ValueError(f"AnkiConnect error: {response['error']}")

    if len(response.get("result", [])) == 0:
        raise ValueError("Note not found.")

    return response["result"][0]


def fetch_audio_data(file_name):
    """Fetch audio data from the collection media folder."""
    response = invoke("retrieveMediaFile", filename=file_name)
    if response.get("error") is not None:
        raise ValueError(f"AnkiConnect error fetching audio: {
                         response['error']}")

    audio_data = response.get("result")
    if audio_data is None:
        raise ValueError(f"Audio file {file_name} not found.")

    return bytearray(audio_data, "utf-8")


def extract_audio_filename(audio_field):
    """Extract the filename from the [sound:filename] format."""
    if audio_field.startswith("[sound:") and audio_field.endswith("]"):
        return audio_field[7:-1]  # Strip [sound: and ]
    return ""


def prepare_input(note):
    """Prepare the input structure for the process function based on the field mapping."""
    audio_field = note["fields"].get("Raw Sentence Audio", {}).get("value", "")
    audio_file = extract_audio_filename(audio_field)
    audio_data = fetch_audio_data(audio_file) if audio_file else bytearray()

    input_structure = Input(
        vocabulary=note["fields"].get("Expression", {}).get("value", ""),
        guide=note["fields"].get("Raw Yomitan Sentence", {}).get("value", ""),
        subtitle_japanese=note["fields"].get(
            "Raw Sentence Japanese", {}).get("value", ""),
        subtitle_english=note["fields"].get(
            "Raw Sentence English", {}).get("value", ""),
        audio=audio_data
    )
    return input_structure


def merge_triplet(triplet):
    """Merge the prefix, middle, and suffix into the required HTML format."""
    return f"{triplet.prefix}<span class=\"expression-highlight\">{triplet.middle}</span>{triplet.suffix}"


def update_note_fields(note_id, results):
    """Update the output fields in the note with the processed results."""
    fields_to_update = {
        "Sentence Japanese": merge_triplet(results.sentence_japanese),
        "Sentence Furigana": merge_triplet(results.sentence_furigana),
        "Sentence English": merge_triplet(results.sentence_english)
    }

    response = invoke("updateNoteFields", note={
        "id": note_id,
        "fields": fields_to_update
    })

    if response.get("error") is not None:
        raise ValueError(f"AnkiConnect error updating fields: {
                         response['error']}")


test_result = {"sentence_japanese": {"prefix": "アメリカ軍はＵＡＰの存在を", "middle": "正式", "suffix": "に認め“宇宙軍”を再編成しました。"}, "sentence_furigana": {"prefix": "<ruby>アメリカ<rt>あめりか</rt></ruby> <ruby>軍<rt>ぐん</rt></ruby> は ＵＡＰ の <ruby>存在<rt>そんざい</rt></ruby> を ", "middle": "<ruby>正式<rt>せいしき</rt></ruby>",
                                                                                                                                      "suffix": " に <ruby>認<rt>みと</rt></ruby>め “ <ruby>宇宙軍<rt>うちゅうぐん</rt></ruby> ” を <ruby>再編成<rt>さいへんせい</rt></ruby> しました 。"}, "sentence_english": {"prefix": "The U.S. military has ", "middle": "officially", "suffix": " acknowledged the existence of UAPs and reformed the Space Force!"}}


def main(note_id):
    """Main function to retrieve the note, prepare input, process it, and update fields."""
    try:
        # note = get_note(note_id)
        # input_structure = prepare_input(note)
        # result = process(input_structure)
        # print(dump_dict(result.model_dump()))
        result = Output.model_validate(test_result)
        update_note_fields(note_id, result)

        print("Processing and updating completed successfully.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # note_id = int(input("Enter the Note ID: "))
    main(1734907310908)
