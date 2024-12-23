from common import *
from audio import *


def extract_sentences(input: Input) -> Extracted:
    system_content = dedent("""
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

        examples: [
            {"input": {"vocabulary": "正式", "guide": "‎ＵＡＰの存在を正式に認め", "subtitle_japanese": "‎ねえ ウザいんだけど<br>‎アメリカ軍は<br>‎ＵＡＰの存在を正式に認め<br>‎“宇宙軍”を再編成しました", "subtitle_english": "Hey, you're being a pest.<br>The U.S. military has officially<br>acknowledged the existence of UAPs<br>and reformed the Space Force!"}, "output": {"sentence_japanese": "アメリカ軍はＵＡＰの存在を正式に認め「宇宙軍」を再編成しました。", "sentence_english": "The U.S. military has officially acknowledged the existence of UAPs and reformed the Space Force!"}}
            {"input": {"vocabulary": "遭遇", "guide": "遭遇しただけでした！", "subtitle_japanese": "‎たぶん ジブンの見間違えっす<br>‎ただのエロい おばあちゃんに<br>‎遭遇しただけでした！<br>‎‎そこのヤツには<br>‎絶対 抜かれちゃダメだって", "subtitle_english": "I'm pretty sure I misunderstood something.<br>I simply bumped into a lewd granny!<br>They say you can't let her<br>outrun you at any cost!"}, "output": {"sentence_japanese": "ただのエロいおばあちゃんに遭遇しただけでした！", "sentence_english": "I simply bumped into a lewd granny!"}}
        ]
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
    system_content = dedent("""
        augment given sentence with furigana using html ruby tags,
        identify words and add whitespace between words

        examples: [
            {"input": {"sentence": "アメリカ軍はＵＡＰの存在を正式に認め“宇宙軍”を再編成しました。"}, "output": {"furigana": "<ruby>アメリカ<rt>あめりか</rt></ruby> <ruby>軍<rt>ぐん</rt></ruby> は ＵＡＰ の <ruby>存在<rt>そんざい</rt></ruby> を <ruby>正式<rt>せいしき</rt></ruby> に <ruby>認<rt>みと</rt></ruby>め “ <ruby>宇宙軍<rt>うちゅうぐん</rt></ruby> ” を <ruby>再編成<rt>さいへんせい</rt></ruby> しました 。"}}
        ]
    """)

    user_content = dict(sentence=sentence)

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": dump_data(user_content)}
        ],
        response_format=Furigana
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_data(out))

    return response


class SplitIn(BaseModel):
    vocabulary: str
    sentence: str


def split_sentences(input: [SplitIn]) -> [Triplet]:
    class Response(BaseModel):
        split_sentences: List[Triplet]

    system_content = dedent("""
        split each sentence into prefix, middle and suffix
        conditions:
        - sentence = prefix + middle + suffix
        - middle: expression in sentence equivalent to vocabulary
        - preserve whitespace

        examples: [
            {"input":[{"vocabulary":"正式","sentence":"アメリカ軍はＵＡＰの存在を正式に認め“宇宙軍”を再編成しました。"},{"vocabulary":"正式","sentence":"<ruby>アメリカ<rt>あめりか</rt></ruby> <ruby>軍<rt>ぐん</rt></ruby> は ＵＡＰ の <ruby>存在<rt>そんざい</rt></ruby> を <ruby>正式<rt>せいしき</rt></ruby> に <ruby>認<rt>みと</rt></ruby>め “ <ruby>宇宙軍<rt>うちゅうぐん</rt></ruby> ” を <ruby>再編成<rt>さいへんせい</rt></ruby> しました 。"},{"vocabulary":"正式","sentence":"The U.S. military has officially acknowledged the existence of UAPs and reformed the Space Force!"}],"output":{"split_sentences":[{"prefix":"アメリカ軍はＵＡＰの存在を","middle":"正式","suffix":"に認め“宇宙軍”を再編成しました。"},{"prefix":"<ruby>アメリカ<rt>あめりか</rt></ruby> <ruby>軍<rt>ぐん</rt></ruby> は ＵＡＰ の <ruby>存在<rt>そんざい</rt></ruby> を ","middle":"<ruby>正式<rt>せいしき</rt></ruby>","suffix":" に <ruby>認<rt>みと</rt></ruby>め “ <ruby>宇宙軍<rt>うちゅうぐん</rt></ruby> ” を <ruby>再編成<rt>さいへんせい</rt></ruby> しました 。"},{"prefix":"The U.S. military has ","middle":"officially","suffix":" acknowledged the existence of UAPs and reformed the Space Force!"}]}}
        ]
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

    sentence_furigana = augment_furigana(extracted.sentence_japanese)

    split_in = [
        SplitIn(vocabulary=input.vocabulary,
                sentence=extracted.sentence_japanese),
        SplitIn(vocabulary=input.vocabulary,
                sentence=sentence_furigana.furigana),
        SplitIn(vocabulary=input.vocabulary,
                sentence=extracted.sentence_english),
    ]
    split_out = split_sentences(split_in)
    [sentence_japanese_split, sentence_furigana_split,
        sentence_english_split] = split_out

    audio = extract_relevant_audio(
        extracted.sentence_japanese,
        input.audio)

    return Output(
        sentence_japanese=sentence_japanese_split,
        sentence_furigana=sentence_furigana_split,
        sentence_english=sentence_english_split,
        sentence_audio=audio,
    )
