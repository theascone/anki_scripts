import textwrap
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import List

model = "gpt-4o"
model2 = "gpt-4o-mini"
dump_inout = True

client = OpenAI()


class Input(BaseModel):
    vocabulary: str
    guide: str
    subtitle_japanese: str
    subtitle_english: str
    audio: bytes


class Triplet(BaseModel):
    prefix: str
    middle: str
    suffix: str


class Output(BaseModel):
    sentence_japanese: Triplet
    sentence_furigana: Triplet
    sentence_english: Triplet
    sentence_audio: bytes


def dedent(string):
    return textwrap.dedent(string).strip() + "\n"


def dump_data(data):
    return json.dumps(data, ensure_ascii=False)


def fmt_data(data):
    return json.dumps(data, indent=4, ensure_ascii=False)
