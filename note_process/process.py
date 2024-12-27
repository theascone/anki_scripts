import unicodedata
from common import *
from audio import *


class Extracted(BaseModel):
    sentence_japanese: str
    sentence_english: str


def normalize_string(s):
    s = "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
    s = s.replace('<br>', '\n')
    return s


def fmt_examples(examples):
    out = ""
    for example in examples:
        out += dedent(f"""
        **Input:** {dump_data(example["input"])}
        **Output:** {dump_data(example["output"])}

        """)
    return out


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
        -- add punctuation if not already present
        -- remove newlines
        -- normalize whitespace
        -- use japanese quotation marks (「」) in japanese sentence
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
        **Objective:**
        Enhance the given Japanese sentence by:
        1. Adding **furigana** annotations using HTML `<ruby>` tags to provide readings for kanji and complex words.
        2. Inserting whitespace between words to clearly separate them for easier parsing and readability.

        ---

        **Detailed Requirements:**
        1. **Furigana Annotation**:
        - Identify kanji or complex words in the sentence.
        - Annotate these words with furigana readings using the `<ruby>` and `<rt>` tags.
        - Preserve the original sentence structure while adding the annotations.

        2. **Word Separation**:
        - Add whitespace between individual words to improve readability.
        - Words include particles, verbs, nouns, and other grammatical components.

        3. **Output Format**:
        - The output should be a string with furigana annotations and whitespace separating words.

        ---

        **Examples**:
    """) + fmt_examples(examples.augment_furigana)

    user_content = dict(sentence=sentence)

    completion = client.beta.chat.completions.parse(
        model=model2,
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
        **Objective:**
        Split each given sentence into three parts: prefix, middle, and suffix. The "middle" corresponds to a specified vocabulary term or its equivalent expression in the sentence. The "prefix" and "suffix" are the parts of the sentence before and after the "middle," respectively. The concatenation of "prefix," "middle," and "suffix" must exactly recreate the original sentence, including all whitespaces, punctuation, and formatting.

        ---

        **Detailed Requirements:**
        1. Identify the **middle** as the expression in the sentence that corresponds to the specified "vocabulary."
        2. Ensure the **prefix** consists of all content in the sentence before the "middle."
        3. Ensure the **suffix** consists of all content in the sentence after the "middle."
        4. Preserve all formatting, including whitespace, punctuation, and special annotations (e.g., `<ruby>` tags).

        ---

        **Examples:**
        Examples: {dump_data(examples.split_sentences)}
    """)

    user_content = [split_in.model_dump() for split_in in input]

    completion = client.beta.chat.completions.parse(
        model=model2,
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
    input.guide = normalize_string(input.guide)
    input.subtitle_japanese = normalize_string(input.subtitle_japanese)
    input.subtitle_english = normalize_string(input.subtitle_english)
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
