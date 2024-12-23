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

        examples: [
            {"input": {"vocabulary": "正式", "guide": "‎ＵＡＰの存在を正式に認め", "subtitle_japanese": "‎ねえ ウザいんだけど<br>‎アメリカ軍は<br>‎ＵＡＰの存在を正式に認め<br>‎“宇宙軍”を再編成しました", "subtitle_english": "Hey, you're being a pest.<br>The U.S. military has officially<br>acknowledged the existence of UAPs<br>and reformed the Space Force!"},
                "output": {"sentence_japanese": "アメリカ軍はＵＡＰの存在を正式に認め“宇宙軍”を再編成しました。", "sentence_english": "The U.S. military has officially acknowledged the existence of UAPs and reformed the Space Force!"}}
            {"input": {"vocabulary": "遭遇", "guide": "遭遇しただけでした！", "subtitle_japanese": "‎たぶん ジブンの見間違えっす<br>‎ただのエロい おばあちゃんに<br>‎遭遇しただけでした！<br>‎‎そこのヤツには<br>‎絶対 抜かれちゃダメだって", "subtitle_english":
                "I'm pretty sure I misunderstood something.<br>I simply bumped into a lewd granny!<br>They say you can't let her<br>outrun you at any cost!"}, "output": {"sentence_japanese": "ただのエロいおばあちゃんに遭遇しただけでした！", "sentence_english": "I simply bumped into a lewd granny!"}}
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
            {"role": "user",   "content": dump_dict(user_content)},
        ],
        response_format=Extracted
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_dict(out))

    return response


def augment_furigana(sentence: str) -> str:
    system_content = dedent("""
        augment given sentence with furigana using html ruby tags,
        identify words and add whitespace between words

        examples: [
            {"input": {"sentence": "アメリカ軍はＵＡＰの存在を正式に認め“宇宙軍”を再編成しました。"}, "output": {
                "furigana": "<ruby>アメリカ<rt>あめりか</rt></ruby> <ruby>軍<rt>ぐん</rt></ruby> は ＵＡＰ の <ruby>存在<rt>そんざい</rt></ruby> を <ruby>正式<rt>せいしき</rt></ruby> に <ruby>認<rt>みと</rt></ruby>め “ <ruby>宇宙軍<rt>うちゅうぐん</rt></ruby> ” を <ruby>再編成<rt>さいへんせい</rt></ruby> しました 。"}}
        ]
    """)

    user_content = dict(sentence=sentence)

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": dump_dict(user_content)}
        ],
        response_format=Furigana
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_dict(out))

    return response


def split_sentence(vocabulary: str, sentence: str) -> Triplet:
    system_content = dedent("""
        split given sentence into prefix, middle and suffix
        conditions:
        - sentence = prefix + middle + suffix
        - middle: expression in sentence equivalent to vocabulary
        - preserve whitespace

        examples: [
            {"input": {"vocabulary": "正式", "sentence": "アメリカ軍はＵＡＰの存在を正式に認め“宇宙軍”を再編成しました。"}, "output": {
                "prefix": "アメリカ軍はＵＡＰの存在を", "middle": "正式", "suffix": "に認め“宇宙軍”を再編成しました。"}},
            {"input": {"vocabulary": "正式", "sentence": "The U.S. military has officially acknowledged the existence of UAPs and reformed the Space Force."}, "output": {
                "prefix": "The U.S. military has ", "middle": "officially", "suffix": " acknowledged the existence of UAPs and reformed the Space Force."}},
            {"input": {"vocabulary": "正式", "sentence": "アメリカ <ruby>軍<rt>ぐん</rt></ruby> は ＵＡＰ の <ruby>存在<rt>そんざい</rt></ruby> を <ruby>正式<rt>せいしき</rt></ruby> に <ruby>認<rt>みと</rt></ruby>め “<ruby>宇宙<rt>うちゅう</rt></ruby> 軍<rt>ぐん</rt>” を <ruby>再編成<rt>さいへんせい</rt></ruby>しました。"},
                "output": {"prefix": "アメリカ <ruby>軍<rt>ぐん</rt></ruby> は ＵＡＰ の <ruby>存在<rt>そんざい</rt></ruby> を ", "middle": "<ruby>正式<rt>せいしき</rt></ruby>", "suffix": " に <ruby>認<rt>みと</rt></ruby>め “<ruby>宇宙<rt>うちゅう</rt></ruby> 軍<rt>ぐん</rt>” を <ruby>再編成<rt>さいへんせい</rt></ruby>しました。"}},
            {"input": {"vocabulary": "遭遇", "sentence": "I simply bumped into a lewd granny!"}, "output": {
                "prefix": "I simply ", "middle":"bumped into", "suffix":" a lewd granny!"}}
        ]
    """)

    user_content = dict(vocabulary=vocabulary, sentence=sentence)

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": dump_dict(user_content)}
        ],
        response_format=Triplet
    )

    response = completion.choices[0].message.parsed

    if dump_inout:
        out = dict(input=user_content, output=response.model_dump())
        print()
        print(fmt_dict(out))

    assert sentence == response.prefix + response.middle + response.suffix

    return response


def process(input: Input) -> Output:
    extracted = extract_sentences(input)

    sentence_furigana = augment_furigana(extracted.sentence_japanese)

    sentence_japanese_split = split_sentence(
        input.vocabulary, extracted.sentence_japanese)
    sentence_furigana_split = split_sentence(
        input.vocabulary, sentence_furigana.furigana)
    sentence_english_split = split_sentence(
        input.vocabulary, extracted.sentence_english)

    audio = extract_relevant_audio(
        extracted.sentence_japanese,
        input.audio)

    # sentence = "アメリカ軍はＵＡＰの存在を正式に認め“宇宙軍”を再編成しました。"
    # sentence_audio = extract_relevant_audio(sentence, input.audio)

    return Output(
        sentence_japanese=sentence_japanese_split,
        sentence_furigana=sentence_furigana_split,
        sentence_english=sentence_english_split,
        sentence_audio=audio,
    )


# input = Input(
#    vocabulary="正式",
#    guide="‎ＵＡＰの存在を正式に認め",
#    subtitle_japanese="‎ねえ ウザいんだけど<br>‎アメリカ軍は<br>‎ＵＡＰの存在を正式に認め<br>‎“宇宙軍”を再編成しました",
#    subtitle_english="Hey, you're being a pest.<br>The U.S. military has officially<br>acknowledged the existence of UAPs<br>and reformed the Space Force!"
# )
# input = Input(
#    vocabulary="遭遇",
#    guide="遭遇しただけでした！",
#    subtitle_japanese="‎たぶん ジブンの見間違えっす<br>‎ただのエロい おばあちゃんに<br>‎遭遇しただけでした！<br>‎‎そこのヤツには<br>‎絶対 抜かれちゃダメだって",
#    subtitle_english="I'm pretty sure I misunderstood something.<br>I simply bumped into a lewd granny!<br>They say you can't let her<br>outrun you at any cost!"
# )

# output = process(input)

# print(fmt_dict(output.model_dump()))

#
