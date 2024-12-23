import textwrap
import json
from openai import OpenAI
from pydantic import BaseModel

model = "gpt-4o"
dump_inout = True

client = OpenAI()


class Input(BaseModel):
    vocabulary: str
    guide: str
    subtitle_japanese: str
    subtitle_english: str
    audio: bytes


class Extracted(BaseModel):
    sentence_japanese: str
    sentence_english: str


class Furigana(BaseModel):
    furigana: str


class Triplet(BaseModel):
    prefix: str
    middle: str
    suffix: str


class CutRange(BaseModel):
    begin: float
    end: float


class Output(BaseModel):
    sentence_japanese: Triplet
    sentence_furigana: Triplet
    sentence_english: Triplet
    sentence_audio: bytes


def dedent(string):
    return textwrap.dedent(string).strip()


def dump_dict(data):
    return json.dumps(data, ensure_ascii=False)


def fmt_dict(data):
    return json.dumps(data, indent=4, ensure_ascii=False)
