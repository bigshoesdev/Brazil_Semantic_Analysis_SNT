import pandas as pd
import re
import time
import nltk

from sentiment_analysis.hashtag_separator import infer_spaces
from nltk.corpus import stopwords
from unicodedata import numeric


def remove_non_characters(tweet):
    """
    Removes non-characters from a tweet.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet with non-characters removed
    """
    tweet = re.sub("[\"\'\.\,\:\;\@\_\-\+\*\\\/\%\_\(\)\[\]\{\}\&\!\?\~\=\^]", '', tweet)
    return ' '.join([w if w != '<' and w != '>' else '' for w in re.split(r'\s+', tweet)])


def remove_urls(tweet):
    tweet = re.sub(r"(?:\@|http?\://)\S+", "", tweet)
    tweet = re.sub(r"(?:\@|https?\://)\S+", "", tweet)
    return tweet


def remove_numbers(tweet):
    """
    Replaces all numbers in a tweet with the word
    'number'.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet with all numbers removed
    """
    words = re.split(r'\s+', tweet)
    new_words = []

    for word in words:
        if bool(re.search(r'\d', word)):
            new_words.append('number')
        else:
            new_words.append(word)

    return ' '.join(new_words)


def remove_small_words(tweet):
    """
    Removes small words from a tweet. Small words are those with
    only one character.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet filtered from small words
    """
    return ' '.join([word for word in tweet.split() if not word.isalpha() or len(word) > 1])


def remove_stopwords(tweet, list_of_stopwords=None):
    """
    Removes stopwords from the tweet. Arbitrary stopword list 
    can be specified through the second method argument. List 
    of english stopwords will be used if no other stopwords 
    are specified.
    INPUT:
        tweet: original tweet as a string
        list_of_stopwords: list of stopwords
    OUTPUT:
        tweet filtered from stopwords
    """
    words = re.split(r'\s+', tweet)
    if list_of_stopwords == None:
        list_of_stopwords = stopwords.words('portuguese')
    words = list(filter(lambda x: x not in list_of_stopwords, words))
    return ' '.join(words)


def remove_url(tweet):
    """
    Removes '<url>' tag from a tweet.
    INPUT: 
        tweet: original tweet as a string
    OUTPUT: 
        tweet with <url> tags removed
    """
    return tweet.replace('<url>', '')


def remove_user(tweet):
    """
    Removes '<user>' tag from a tweet.
    INPUT: 
        tweet: original tweet as a string
    OUTPUT: 
        tweet with <user> tags removed
    """
    return tweet.replace('<user>', '')


def replace_emoticons(tweet):
    """
    Replaces emoticons in a tweet with descriptive word.
    INPUT:
        tweet: original tweet as a string
    OUTPU:
        tweet with emoticons replaced
    """
    heart_emoticons = ['<3', '❤']

    positive_emoticons = [
        ':)', ':-)', ';-)', ":')", ':*', ':-*', '[:', '[-:', ';)', '=)',
        ':D', ':-D', '8-D', 'xD', 'XD', ':P', ':-P', ':p', ':-p', ':d', ';d',
        '(:', '(;', '(-:', '(-;', "(':", '*:', '*-:', '(=', ':]', ':-]'
    ]

    negative_emoticons = [
        ':(', ':((', ';(', ':-(', ":'(", '=(',
        '):', ')):', ');', ')-:', ")':", ')='
    ]

    words = re.split(r'\s+', tweet)
    new_words = []

    for word in words:
        if word in heart_emoticons or word in positive_emoticons:
            new_words.append('positive')
        elif word in negative_emoticons:
            new_words.append('negative')
        else:
            new_words.append(word)

    return ' '.join(new_words)


def replace_emoticons_with_tags(tweet):
    """
    Replaces emoticons in a tweet with tags.
    INPUT:
        tweet: original tweet as a string
    OUTPU:
        tweet with emoticons replaced
    """
    hearts = set(['<3', '❤'])

    happy_faces = set([
        ':)', ":')", '=)', ':-)', ':]', ":']", '=]', ':-]', ':d',
        '(:', "(':", '(=', '(-:', '[:', "[':", '[=', '[-:'
    ])

    sad_faces = set([
        ':(', ":'(", '=(', ':-(', ':[', ":'[", '=[', ':-[',
        '):', ")':", ')=', ')-:', ']:', "]':", ']=', ']-:'
    ])

    neutral_faces = set([
        ':/', ':\\', ':|',
        '/:', '\\:', '|:'
    ])

    cheeky_faces = set([
        ':P', ':p', ":'P", ":'p", '=P', '=p', ':-P', ":-p"
    ])

    words = re.split(r'\s+', tweet)
    new_words = []

    for word in words:
        if word in hearts:
            new_words.append('<heart>')
        elif word in happy_faces:
            new_words.append('<smile>')
        elif word in neutral_faces:
            new_words.append('<neutralface>')
        elif word in sad_faces:
            new_words.append('<sadface>')
        elif word in cheeky_faces:
            new_words.append('<lolface>')
        else:
            new_words.append(word)

    return ' '.join(new_words)


def split_hashtags(tweet):
    """
    Splits all tweet hashtags into words that are
    mentioned in those hashtags.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet with hashtags replaced with words
        mentioned in those hashtags
    """
    words = re.split(r'\s+', tweet)
    new_words = []

    for word in words:
        if word and word[0] != '#':
            new_words.append(word)
            continue

        new_words.append(word)
        hash_words = infer_spaces(word[1:].lower()).split(' ')
        if len(hash_words) > 1:
            for hash_word in hash_words:
                if (len(hash_word) == 1):
                    continue
                new_words.append(hash_word)
        else:
            new_words.append(word[1:])
    return ' '.join(new_words)


def stem(tweet, stemmer=None):
    """
    Stemms all words in a tweet with the given stemmer. 
    If no stemmer is provided, default 'LancasterStemmer'
    is used.
    INPUT:
        tweet: tweet with words to be stemmed
        stemmer: stemmer to be used for stemming
    OUPUT:
        original tweet with all its words stemmed
    """

    def stem_single(word, stemmer):
        if word:
            return stemmer.stem(word)
        else:
            return ''

    words = re.split(r'\s+', tweet)
    if stemmer == None:
        stemmer = LancasterStemmer()
    words = list(map(lambda x: stem_single(x, stemmer), words))
    return ' '.join(words)


def tag_hashtags(tweet):
    """
    Marks hashtags in tweet.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet with hashtags marked
    """
    words = re.split(r'\s+', tweet)
    new_words = []

    for word in words:
        if word and word[0] == '#':
            new_words.append('<hashtag>')
        new_words.append(word)

    return ' '.join(new_words)


def tag_numbers(tweet):
    """
    Marks numbers in tweet.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet with numbers marked
    """

    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            pass
        try:
            numeric(s)
            return True
        except (TypeError, ValueError):
            pass
        return False

    words = re.split(r'\s+', tweet)
    new_words = []

    for word in words:
        trimmed = re.sub('[,\.:%_\-\+\*\/\%\_]', '', word)
        if is_number(trimmed):
            new_words.append('<number>')
        else:
            new_words.append(word)

    return ' '.join(new_words)


def tag_repeated_characters(tweet):
    """
    Marks words with repeating characters in tweet.
    Repetition needs to be greater or equal than three.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet with words with repeating characters marked
    """

    def tag_repeated(word):
        return re.sub(r'([a-z])\1\1+$', r'\1 <elong>', word)

    words = re.split(r'\s+', tweet)
    words = list(map(tag_repeated, words))
    return ' '.join(words)


def tag_repeated_punctuations(tweet):
    """
    Marks repeated punctuations in tweet.
    INPUT:
        tweet: original tweet as a string
    OUTPUT:
        tweet with repeating punctuations marked
    """
    for symb in ['!', '?', '.', ',']:
        regex = '(\\' + symb + '( *)){2,}'
        tweet = re.sub(regex, symb + ' <repeat> ', tweet)
    return tweet


def tag_all_words_with_digits(tweet):
    words = re.split(r'\s+', tweet)
    new_words = []
    for word in words:
        if any(char.isdigit() for char in word):
            new_words.append('<number>')
        else:
            new_words.append(word)
    return ' '.join(new_words)


def preprocess_tweets(tweets, text_column, train=True, parameters=None):
    """
    Performs tweet preprocessing on the data frame passed
    as the first argument with column containing tweets specified.
    Default preprocessing parameters are:
        'filter_duplicates': True,
        'remove_url_tags': True,
        'remove_user_tags': True,
        'replace_emoticons_with_tags': True,
        'tag_hashtags': True,
        'tag_numbers': True,
        'tag_repeated_characters': True,
        'tag_repeated_punctuations': True,
        'split_hashtags': True,
        'remove_stopwords': True,
        'remove_non_characters': True,
        'remove_small_words': True,
        'remove_numbers': True,
        'replace_emoticons': True,
        'tag_all_words_with_digits': True,
        'stem': True
    Custom preprocessing parameters can be specified.
    INPUT
        tweets: data frame containing original tweets
        text_column: column name containing tweet content in the data frame
        train: specifies whether tweets being processed belong to the training set
        parameters: custom preprocessing parameters
    OUTPUT:
        data frame containing processed tweets
    """

    if parameters == None:  # Set of default parameters
        parameters = {
            'filter_duplicates': True,
            'remove_url_tags': True,
            'remove_user_tags': True,
            'replace_emoticons_with_tags': True,
            'tag_hashtags': True,
            'tag_numbers': True,
            'tag_repeated_characters': True,
            'tag_repeated_punctuations': True,
            'split_hashtags': True,
            'remove_stopwords': True,
            'remove_non_characters': True,
            'remove_small_words': True,
            'remove_numbers': True,
            'replace_emoticons': True,
            'tag_all_words_with_digits': True,
            'stem': True
        }

    start_time = time.time()
    content = tweets[text_column].copy()

    if parameters['filter_duplicates'] and train:
        content = content.drop_duplicates()
        print('Filtering duplicates: FINISHED')

    if parameters['remove_url_tags']:
        content = list(map(remove_url, content))
        content = list(map(remove_urls, content))
        print('Removing URL tags: FINISHED')

    if parameters['remove_user_tags']:
        content = list(map(remove_user, content))
        print('Removing USER tags: FINISHED')

    if parameters['replace_emoticons_with_tags']:
        content = list(map(replace_emoticons_with_tags, content))
        print('Replacing emoticons with tags: FINISHED')

    if parameters['tag_hashtags']:
        content = list(map(tag_hashtags, content))
        print('Tagging hashtags: FINISHED')

    if parameters['tag_numbers']:
        content = list(map(tag_numbers, content))
        print('Tagging numbers: FINISHED')

    if parameters['tag_repeated_characters']:
        content = list(map(tag_repeated_characters, content))
        print('Tagging repeated characters: FINISHED')

    if parameters['tag_repeated_punctuations']:
        content = list(map(tag_repeated_punctuations, content))
        print('Tagging repeated punctuations: FINISHED')

    if parameters['split_hashtags']:
        content = list(map(split_hashtags, content))
        print('Splitting hashtags: FINISHED')

    if parameters['remove_stopwords']:
        list_of_stopwords = stopwords.words('english') + stopwords.words('english')
        content = list(map(lambda x: remove_stopwords(x, list_of_stopwords), content))
        print('Removing stopwords: FINISHED')

    if parameters['remove_small_words']:
        content = list(map(remove_small_words, content))
        print('Removing small words: FINISHED')

    if parameters['remove_numbers']:
        content = list(map(remove_numbers, content))
        print('Removing numbers: FINISHED')

    if parameters['replace_emoticons']:
        content = list(map(replace_emoticons, content))
        print('Replacing emoticons: FINISHED')

    if parameters['remove_non_characters']:
        content = list(map(remove_non_characters, content))
        print('Removing non-characters: FINISHED')

    if parameters['stem']:
        stemmer = nltk.stem.RSLPStemmer()
        content = list(map(lambda x: stem(x, stemmer), content))
        print('Stemming: FINISHED')

    if parameters['tag_all_words_with_digits']:
        content = list(map(tag_all_words_with_digits, content))
        print('Tagging all words with digits: FINISHED')

    end_time = time.time()
    print('Time elapsed (s): {}'.format(end_time - start_time))

    return pd.DataFrame({'parsed': content})
