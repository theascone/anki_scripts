from common import *
from audio import *


class Extracted(BaseModel):
    sentence_japanese: str
    sentence_english: str


def extract_sentences(input: Input) -> Extracted:
    system_content = dedent(f"""



        extract japanese and english sentences from given subtitles
        - japanese sentence must
        -- contain the vocabulary
        -- be a contiguous substring of japanese subtitle
        -- be a single and complete sentence
        - english sentence must
        -- correspond to japanese sentence
        -- be based on english subtitle
        clean up sentences
        -- remove newlines and control characters
        -- normalize whitespace
        -- add punctuation if not already present
        -- use japanese quotes in japanese sentence

        examples: {dump_data(examples.extract_sentences)}
    """)

    user_content = dict(
        vocabulary=input.vocabulary,
        guide=input.guide,
        subtitle_japanese=input.subtitle_japanese,
        subtitle_english=input.subtitle_english
    )

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user",   "content": dump_data(user_content)},
        ],
        response_format=Extracted
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_data(out))

    return response


def augment_furigana(sentence: str) -> str:
    class Response(BaseModel):
        furigana: str

    system_content = dedent(f"""
        augment given sentence with furigana using html ruby tags,
        identify words and add whitespace between words

        examples: {dump_data(examples.augment_furigana)}
    """)

    user_content = dict(sentence=sentence)

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": dump_data(user_content)}
        ],
        response_format=Response
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_data(out))

    return response.furigana


class SplitIn(BaseModel):
    vocabulary: str
    sentence: str


def split_sentences(input: [SplitIn]) -> [Triplet]:
    class Response(BaseModel):
        split_sentences: List[Triplet]

    system_content = dedent(f"""
        split each sentence into prefix, middle and suffix
        conditions:
        - sentence = prefix + middle + suffix
        - middle: expression in sentence equivalent to vocabulary
        - preserve whitespace

        examples: {dump_data(examples.split_sentences)}
    """)

    user_content = [split_in.model_dump() for split_in in input]

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": dump_data(user_content)}
        ],
        response_format=Response
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_data(out))

    assert len(user_content) == len(response.split_sentences)

    for split_in, split_sentence in zip(input, response.split_sentences):
        assert split_in.sentence == split_sentence.prefix + \
            split_sentence.middle + split_sentence.suffix

    return response.split_sentences


def process(input: Input) -> Output:
    extracted = extract_sentences(input)

    sentence_japanese = extracted.sentence_japanese
    sentence_furigana = augment_furigana(sentence_japanese)
    sentence_english = extracted.sentence_english

    split_in = [
        SplitIn(vocabulary=input.vocabulary, sentence=sentence_japanese),
        SplitIn(vocabulary=input.vocabulary, sentence=sentence_furigana),
        SplitIn(vocabulary=input.vocabulary, sentence=sentence_english),
    ]
    split_out = split_sentences(split_in)
    [sentence_japanese, sentence_furigana, sentence_english] = split_out

    audio = extract_relevant_audio(
        extracted.sentence_japanese,
        input.audio)

    return Output(
        sentence_japanese=sentence_japanese,
        sentence_furigana=sentence_furigana,
        sentence_english=sentence_english,
        sentence_audio=audio,
    )
