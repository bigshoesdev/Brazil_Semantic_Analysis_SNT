import os.path
from flask_restful import Resource
from flask import jsonify, request, Response
from config import config

from topic_modeling.tm_tokenize import tokenize
from topic_modeling.tm_lda import run_lda
from topic_modeling.tm_run import display
from utils.utils import get_posts


def html(content):
    return '<html><body>' + content + '</body></html>'


class TopicModelingAPI(Resource):
    def get(self):
        data = request.args
        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            candidate = data.get("name")
            sns_type = data.get("type")

            if sns_type == 'twitter':
                tweets_test = get_posts(candidate, sns_type)
                print('tweets count', tweets_test.count())
                if tweets_test.count() == 0:
                    return Response(html("This candidate is not valid."))
            elif sns_type == 'facebook':
                posts_test = get_posts(candidate, sns_type)
                print('posts count', posts_test.count())
                if posts_test.count() == 0:
                    return Response(html("This candidate is not valid."))
            else:
                return Response(html("The SNS name is not valid. please use either of facebook or twitter."))

            corpus_filename = config.project_path + 'topic_modeling/data/' + candidate + '_' + sns_type + '_corpus.mm'
            lda_filename = config.project_path + 'topic_modeling/data/' + candidate + '_' + sns_type + '.lda'

            if os.path.isfile(corpus_filename):
                print('corpus file exists')
                if os.path.isfile(lda_filename):
                    print('lda file exists')
                    pass
                else:
                    print("corpus file doesn't exist")
                    run_lda({'name': candidate, 'type': sns_type})
            else:
                print("corpus file doesn't exist")
                tokenize(candidate, sns_type)
                run_lda({'name': candidate, 'type': sns_type})

            result = display(data)

            return Response(html(result))
