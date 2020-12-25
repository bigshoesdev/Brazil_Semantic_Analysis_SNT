import argparse

from gensim import corpora, models
from config import config
from utils.utils import get_posts


def run_lda(data):
    posts = get_posts(data['name'], data['type'])
    print("Corpus of %s documents" % posts.count())

    corpus_filename = config.project_path + 'topic_modeling/data/' + data['name'] + '_' + data['type'] + '_corpus.mm'
    dict_filename = config.project_path + 'topic_modeling/data/' + data['name'] + '_' + data[
        'type'] + '_dictionary.dict'
    lda_filename = config.project_path + 'topic_modeling/data/' + data['name'] + '_' + data['type'] + '.lda'
    lda_params = {'num_topics': 40, 'passes': 20, 'alpha': 0.001}

    # Load the corpus and Dictionary
    corpus = corpora.MmCorpus(corpus_filename)
    dictionary = corpora.Dictionary.load(dict_filename)

    print("Running LDA with: %s  " % lda_params)
    lda = models.LdaModel(corpus, id2word=dictionary,
                          num_topics=lda_params['num_topics'],
                          passes=lda_params['passes'],
                          alpha=lda_params['alpha'])

    lda.print_topics()
    lda.save(lda_filename)
    print("lda saved in %s " % lda_filename)

    return {
        'status': 200,
        'lda_file': lda_filename
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", help="type of SNS: facebook, twitter")
    ap.add_argument("-u", help="User's Tweets you want to create LDA.")

    arg = ap.parse_args()

    # Initialize
    if arg.u and arg.t:
        data = {
            'name': arg.u,
            'type': arg.t
        }
    else:
        data = {
            'name': 'RogerioMLisboa',
            'type': 'twitter'
        }

    run_lda(data)
