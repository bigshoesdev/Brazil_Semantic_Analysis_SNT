# Load the corpus and dictionary
import argparse

from gensim import corpora, models
import pyLDAvis.gensim
from config import config


def display(data):
    corpus = corpora.MmCorpus(
        config.project_path + 'topic_modeling/data/' + data['name'] + '_' + data['type'] + '_corpus.mm')
    dictionary = corpora.Dictionary.load(
        config.project_path + 'topic_modeling/data/' + data['name'] + '_' + data['type'] + '_dictionary.dict')

    # First LDA model with 10 topics, 10 passes, alpha = 0.001
    lda = models.LdaModel.load(
        config.project_path + 'topic_modeling/data/' + data['name'] + '_' + data['type'] + '.lda')
    vis_data = pyLDAvis.gensim.prepare(lda, corpus, dictionary, mds='mmds')
    visJsonfile = config.project_path + 'topic_modeling/data/' + data['name'] + '_' + data['type'] + '.json'
    pyLDAvis.save_json(vis_data, visJsonfile)

    html = pyLDAvis.prepared_data_to_html(vis_data)
    return html


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", help="type of SNS: facebook, twitter")
    ap.add_argument("-u", help="User's Tweets you want to tokenize.")

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

    display(data)
