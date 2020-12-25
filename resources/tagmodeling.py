import os.path
import json
from flask_restful import Resource
from flask import jsonify, request, Response, send_file
from config import config
import io

from topic_modeling.tm_tokenize import tokenize
from topic_modeling.tm_tagcloud import word_tag_cloud
from utils.utils import get_posts


def html(content):
    return '<html><body>' + content + '</body></html>'


class TagModelingAPI(Resource):
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

            if os.path.isfile(corpus_filename):
                print('corpus file exists')
                pass
            else:
                print("corpus file doesn't exist")
                tokenize(candidate, sns_type)

            result = word_tag_cloud(candidate, sns_type)
            output = io.BytesIO()
            result.convert('RGBA').save(output, format='PNG')
            output.seek(0, 0)

            return send_file(output, mimetype='image/png', as_attachment=False)
