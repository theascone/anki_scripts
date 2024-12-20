import os
import subprocess
import re
from aqt import mw
from aqt.qt import QAction, QMessageBox
from anki.hooks import addHook

# Function to convert OGG to MP3 using FFmpeg
def convert_ogg_to_mp3(ogg_path):
    mp3_path = os.path.splitext(ogg_path)[0] + '.mp3'

    # Check if the MP3 already exists to avoid redundant conversion
    if os.path.exists(mp3_path):
        return mp3_path

    try:
        # Run the FFmpeg command to convert the file
        subprocess.run(['/usr/local/bin/ffmpeg', '-i', ogg_path, mp3_path], check=True)
        return mp3_path
    except subprocess.CalledProcessError as e:
        QMessageBox.information(mw, "OGG to MP3 Conversion", f"Error converting {ogg_path} to MP3: {e} stderr: {e.stderr} stdout: {e.stdout}")
        return None

# Function to convert OGG files and update notes
def convert_ogg_files_and_update_notes():
    # Regular expression to match [sound:filename.ogg]
    sound_regex = re.compile(r'\[sound:(.+\.ogg)\]')

    # Iterate through all notes
    note_ids = mw.col.findNotes("")
    for note_id in note_ids:
        note = mw.col.getNote(note_id)

        # Only process the "Audio" field
        if 'Audio' not in note:
            continue

        field_value = note['Audio']
        match = sound_regex.match(field_value)

        if not match:
            continue  # Skip if no OGG reference is found

        ogg_filename = match.group(1)  # Extract the filename
        ogg_path = os.path.join(mw.col.media.dir(), ogg_filename)

        # Check if the OGG file exists
        if not os.path.exists(ogg_path):
            QMessageBox.information(mw, "OGG to MP3 Conversion", f"OGG file not found: {ogg_path}")
            continue

        # Convert the OGG file to MP3
        mp3_path = convert_ogg_to_mp3(ogg_path)
        if not mp3_path:
            continue  # Skip if conversion failed

        mp3_filename = os.path.basename(mp3_path)


        # Update the field to reference the MP3 file
        note['Audio'] = f"[sound:{mp3_filename}]"
        note.flush()  # Save the changes
        print(f"Updated note {note.id} to reference {mp3_filename}")

# Add the menu item to Anki
def on_menu_item():
    convert_ogg_files_and_update_notes()
    QMessageBox.information(mw, "OGG to MP3 Conversion", "Conversion completed and Audio fields updated!")

# Hook the function to Anki's menu
action = QAction("Convert OGG to MP3", mw)
action.triggered.connect(on_menu_item)
mw.form.menuTools.addAction(action)
