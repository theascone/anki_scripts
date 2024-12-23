from common import *

import openai
import subprocess
import tempfile


def transcribe_audio(audio_path: str) -> dict:
    """Transcribe audio using Whisper and return the transcription with timestamps."""
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

        return [
            {
                "start": word.start,
                "end": word.end,
                "text": word.word
            }
            for word in transcription.words
        ]


def find_japanese_sentence(japanese_sentence: str, transcription: dict) -> CutRange:
    system_content = dedent("""
        match the given japanese sentence against the provided transcription
        return range where japanese sentence begins and ends in transcription
        pad start and end by up to 0.5 seconds
    """)

    user_content = dict(
        japanese_sentence=japanese_sentence,
        transcription=transcription
    )

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": dump_data(user_content)}
        ],
        response_format=CutRange
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_data(out))

    return response


def cut_audio(audio_path: str, cut_range: CutRange) -> bytearray:
    """Cut the audio file to the specified start and end times and return the resulting bytearray."""
    output_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name

    command = [
        "ffmpeg", "-i", audio_path,
        "-ss", str(cut_range.begin), "-to", str(cut_range.end),
        output_path, "-y"
    ]

    subprocess.run(command, check=True)

    with open(output_path, "rb") as output_file:
        return bytearray(output_file.read())


def extract_relevant_audio(japanese_sentence: str, audio_bytes: bytearray) -> bytearray:
    """Extract the relevant part of the audio containing the Japanese sentence."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
        temp_audio_file.write(audio_bytes)
        temp_audio_path = temp_audio_file.name

        transcription = transcribe_audio(temp_audio_path)
        cut_range = find_japanese_sentence(
            japanese_sentence, transcription)
        return cut_audio(temp_audio_path, cut_range)
