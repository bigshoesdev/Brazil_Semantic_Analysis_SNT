import argparse

import nltk
import numpy as np
import re
from collections import defaultdict

from utils.utils import get_posts
from gensim import corpora
from string import digits
from config import config

connection = config.initdb()
db = connection.scope_db


def filter_by_length_and_lang(percent, lang, tweets, sns_name):
    tweets.rewind()

    if sns_name == 'twitter':
        field_name = 'tweet'
        id_field = 'id'
    else:
        field_name = 'status_message'
        id_field = 'status_id'

    # exclude 25% of documents with little content
    len_text = [len(tw[field_name]) for tw in tweets
                if len(tw[field_name]) > 0]
    threshold = np.percentile(len_text, percent)

    tweets.rewind()
    # filter on lang and
    documents = [{'id': tw[id_field], 'text': tw[field_name]}
                 for tw in tweets
                 if (len(tw[field_name]) > threshold)
                 ]
    # Keep documents in English or Undefined lang and with enough content
    return documents


# --------------------------------------
#  Clean documents functions
# --------------------------------------

def remove_urls(text):
    text = re.sub(r"(?:\@|http?\://)\S+", "", text)
    text = re.sub(r"(?:\@|https?\://)\S+", "", text)
    return text


def doc_rm_urls(documents):
    return [{'id': doc['id'], 'text': remove_urls(doc['text'])}
            for doc in documents]


def stop_words_list():
    '''
        A stop list specific to the observed timelines composed of noisy words
        This list would change for different set of timelines
    '''
    return ['amp', 'get', 'got', 'hey', 'hmm', 'hoo', 'hop', 'iep', 'let', 'ooo', 'par',
            'pdt', 'pln', 'pst', 'wha', 'yep', 'yer', 'aest', 'didn', 'nzdt', 'via',
            'one', 'com', 'new', 'like', 'great', 'make', 'top', 'awesome', 'best',
            'good', 'wow', 'yes', 'say', 'yay', 'would', 'thanks', 'thank', 'going',
            'new', 'use', 'should', 'could', 'really', 'see', 'want', 'nice',
            'while', 'know', 'free', 'today', 'day', 'always', 'last', 'put', 'live',
            'week', 'went', 'wasn', 'was', 'used', 'ugh', 'try', 'kind', 'http', 'much',
            'need', 'next', 'app', 'ibm', 'appleevent', 'using',
            'a', 'a fim de', 'a par de', 'a respeito de', 'abaixo de', 'acerca de',
            'acima de', 'afora', 'além de', 'andando', 'andar', 'andava', 'andou',
            'ante', 'antes de', 'ao invés de', 'ao lado de', 'apesar de', 'após',
            'até', 'atrás de', 'através de', 'com', 'comigo', 'como', 'conforme',
            'consoante', 'contigo', 'continua', 'continuando', 'continuar',
            'continuava', 'contra', 'de', 'de acordo com', 'de cima de', 'debaixo de',
            'dentro de', 'depois de', 'desde', 'diante de', 'durante', 'é', 'em',
            'em frente de', 'em lugar de', 'em vez de', 'entre', 'entre', 'era', 'esta',
            'estando', 'estar', 'estava', 'esteve', 'exceto', 'feito', 'fica', 'ficando',
            'ficar', 'ficava', 'foi', 'graças a', 'me', 'mediante', 'menos', 'mim',
            'para', 'parece', 'parecer', 'pareceu', 'parecia', 'perante', 'permacener',
            'perto de', 'por', 'por causa de', 'por entre', 'por que', 'porque', 'quando',
            'salvo', 'se', 'segundo', 'sem', 'senão', 'ser', 'será', 'sob', 'sobre',
            'tirante', 'torna', 'tornar', 'tornou', 'trás', 'vista', 'visto', 'ola',
            'nesta', 'desta', 'deste', 'daquele', 'meu', 'minha', 'desse', 'sobre', 'pessoas',
            'emoji', 'ser', 'pic', 'twitter', 'ser']


def all_stopwords(tokenized_documents):
    '''
        Builds a stoplist composed of stopwords in several languages,
        tokens with one or 2 words and a manually created stoplist
    '''
    # tokens with 1 characters
    unigrams = [w for doc in tokenized_documents for w in doc['tokens']
                if len(w) == 1]
    # print ('unigrams', unigrams)

    # tokens with 2 characters
    bigrams = [w for doc in tokenized_documents for w in doc['tokens']
               if len(w) == 2]
    # print ('bigrams', bigrams)

    # Compile global list of stopwords
    stoplist = set(nltk.corpus.stopwords.words("english")
                   + nltk.corpus.stopwords.words("portuguese")
                   + nltk.corpus.stopwords.words("french")
                   + nltk.corpus.stopwords.words("german")
                   + stop_words_list()
                   + unigrams + bigrams)
    return stoplist


# This returns a list of tokens / single words for each user
def tokenize_doc(documents):
    '''
        Tokenizes the raw text of each document
    '''
    tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
    return [{'id': doc['id'],
             'tokens': tokenizer.tokenize(doc['text'].lower())
             }
            for doc in documents]


def count_token(tokenized_documents):
    '''
        Calculates the number of occurence of each word across the whole corpus
    '''
    token_frequency = defaultdict(int)
    for doc in tokenized_documents:
        for token in doc['tokens']:
            token_frequency[token] += 1
    return token_frequency


def token_condition(token, stoplist, token_frequency):
    '''
        Only keep a token that is not in the stoplist,
        and with frequency > 1 among all documents
    '''
    return (token not in stoplist and len(token.strip(digits)) == len(token)
            and token_frequency[token] > 5)


def keep_best_tokens(tokenized_documents, stoplist, token_frequency):
    '''
        Removes all tokens that do not satistify a certain condition
    '''
    return [{'id': doc['id'],
             'tokens': [token for token in doc['tokens']
                        if token_condition(token, stoplist, token_frequency)]
             }
            for doc in tokenized_documents]


# ---------------------------------------------------------
#  Main
# ---------------------------------------------------------

def tokenize(candidate, sns_name):
    # Initialize
    tweets = get_posts(candidate, sns_name)

    if not tweets.count():
        return {
            'status': 404,
            'message': "Wrong SNS name"
        }

    print('============tokenize tweets count================', tweets.count())

    # ---------------------------------------------------------
    #  Documents / timelines selection and clean up
    # ---------------------------------------------------------

    # Keep 1st Quartile of documents by length and filter out non-English words
    documents = filter_by_length_and_lang(5, ['pt', 'und'], tweets, sns_name)

    # Remove urls from each document
    documents = doc_rm_urls(documents)

    print("\nWe have " + str(len(documents)) + " documents in portuguese ")

    # ---------------------------------------------------------
    #  Tokenize documents
    # ---------------------------------------------------------

    # At this point tokenized_documents.keys() == ['user_id', 'tokens']
    tokenized_documents = tokenize_doc(documents)

    token_frequency = count_token(tokenized_documents)
    stoplist = all_stopwords(tokenized_documents)

    tokenized_documents = keep_best_tokens(tokenized_documents, stoplist, token_frequency)

    # ---------------------------------------------------------
    #  Save tokenized docs in database
    # ---------------------------------------------------------
    # for visualization purposes only
    for doc in tokenized_documents:
        doc['tokens'].sort()

        if len(doc['tokens']) > 0:
            update = {'tokens': doc['tokens'],
                      'has_tokens': True,
                      'len_tokens': len(doc['tokens'])
                      }

            if sns_name == 'twitter':
                db.twitter_tweets.update_one(
                    {'id': doc['id']},
                    {"$set": update}
                )
            elif sns_name == 'facebook':
                db.fb_posts.update_one(
                    {'status_id': doc['id']},
                    {"$set": update}
                )
        else:
            pass

    relation = db.sns_relation.find_one({"$and": [{"user_id": candidate}, {"type": sns_name}]}, no_cursor_timeout=True)
    user_list = relation['user_list']

    if sns_name == 'twitter':
        tweets = db.twitter_tweets.count({"$and": [{'user': {"$in": user_list}}, {'has_tokens': True}]})
    elif sns_name == 'facebook':
        tweets = db.fb_posts.count({"$and": [{'page_id': {"$in": user_list}}, {'has_tokens': True}]})

    print("\nWe have %s tokenized documents in the database" % tweets)

    # ---------------------------------------------------------
    #  Dictionary and Corpus
    # ---------------------------------------------------------

    # build the dictionary
    dictionary = corpora.Dictionary([doc['tokens'] for doc in tokenized_documents])
    dictionary.compactify()

    # We now have a dictionary with N unique tokens
    print("Dictionary: ", end=' ')
    print(dictionary)

    dict_filename = config.project_path + 'topic_modeling/data/' + candidate + '_' + sns_name + '_dictionary.dict'
    # and save the dictionary for future use
    print("dictionary saved in %s " % dict_filename)
    dictionary.save(dict_filename)

    # Build the corpus: vectors with occurence of each word for each document
    # and convert tokenized documents to vectors
    corpus = [dictionary.doc2bow(doc['tokens']) for doc in tokenized_documents]

    corpus_filename = config.project_path + 'topic_modeling/data/' + candidate + '_' + sns_name + '_corpus.mm'
    # and save in Market Matrix format
    print("corpus saved in %s " % corpus_filename)
    corpora.MmCorpus.serialize(corpus_filename, corpus)

    return {
        'dict': dict_filename,
        'corpus': corpus_filename
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", help="type of SNS: facebook, twitter")
    ap.add_argument("-u", help="User's Tweets you want to tokenize.")

    arg = ap.parse_args()

    # Initialize
    if arg.u and arg.t:
        candidate = arg.u
        sns_name = arg.t
    else:
        candidate = 'RogerioMLisboa'
        sns_name = 'twitter'

    tokenize(candidate, sns_name)
