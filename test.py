from polyglot.downloader import downloader

# print(downloader.supported_languages_table("sentiment2", 3))

from polyglot.text import Text

text = Text(
    "Nós não vemos nada. Está nublado.")

# blob = ("Barack Obama gave a fantastic speech last night. "
#         "Reports indicate he will move next to New Hampshire.")
# text = Text(blob)
print("{:<16}{}".format("Word", "Polarity") + "\n" + "-" * 30)
for w in text.words:
    print("{:<16}{:>2}".format(w, w.polarity))


first_sentence = text.sentences[0]
print(first_sentence)
print(first_sentence.language)

first_entity = first_sentence.entities[0]
print(first_entity)

print(first_entity.positive_sentiment)
print(first_entity.negative_sentiment)

for sentence in text.sentences:
    print("=============={}".format(sentence))

    for entity in sentence.entities:
        print('************** Entity: {} Positive: {} Negative: {}'.format(entity, entity.positive_sentiment,
                                                                           entity.negative_sentiment))
