from flask_restful import Resource
from config import config
from bson.json_util import dumps
from flask import request, Response


class ArticleSearchAPI(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            data = {"response": "ERROR"}
            return Response(dumps(data))
        else:
            keywords = data['keywords']
            sources = data['sources']
            size = data['size']

            if not size:
                size = 20

            result = article_search(keywords, sources, size)
            return Response(dumps(result))


class CandidateSearchAPI(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            data = {"response": "ERROR"}
            return Response(dumps(data))
        else:
            start = data['start']
            end = data['end']
            keyword = data['keyword']
            result = candidate_search(keyword, start, end)

            return Response(dumps({'exist': result}))


def article_search(keywords, sources, size):
    es_object = config.init_elastic()

    should_query = []

    for keyword in keywords:
        should_query.append({
            "multi_match": {
                "query": keyword,
                "type": "phrase",
                "fields": [
                    "title",
                    "call",
                    "text"
                ]
            }
        })

    result_search = es_object.search(
        index=config.es_index_name,
        body={
            'query': {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": should_query
                            }
                        }
                    ],
                    "filter": [
                        {
                            "terms": {
                                "source": sources
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "pre_tags": [
                    "<mark>"
                ],
                "post_tags": [
                    "</mark>"
                ],
                "number_of_fragments": 0,
                "fields": {
                    "title": {},
                    "call": {},
                    "text": {}
                }
            },
            'size': size
        },
        filter_path=['hits.hits._source', 'hits.hits.highlight', 'hits.hits._score']
    )

    if not result_search:
        result_search = es_object.search(
            index=config.es_index_name,
            body={
                'query': {
                    "bool": {
                        "filter": [
                            {
                                "terms": {
                                    "source": sources
                                }
                            }
                        ]
                    }
                },
                "sort": [
                    {"last_updated": {"order": "desc"}},
                ],
                "highlight": {
                    "pre_tags": [
                        "<mark>"
                    ],
                    "post_tags": [
                        "</mark>"
                    ],
                    "number_of_fragments": 0,
                    "fields": {
                        "title": {},
                        "call": {},
                        "text": {}
                    }
                },
                'size': 20,
            },
            filter_path=['hits.hits._source', 'hits.hits.highlight', 'hits.hits._score']
        )

    ary = []

    try:
        for result in result_search['hits']['hits']:
            source = result['_source']

            if 'highlight' in result:
                highlight = result['highlight']
            else:
                highlight = {}

            if 'call' in highlight:
                source['call'] = highlight['call'][0]

            if 'title' in highlight:
                source['title'] = highlight['title'][0]

            if 'text' in highlight:
                source['text'] = highlight['text'][0]

            ary.append(source)
    except Exception as e:
        import traceback
        import logging
        logging.error(traceback.format_exc())

    return ary


def candidate_search(keyword, start, end):
    es_object = config.init_elastic()

    result = es_object.count(
        index=config.es_index_name,
        body={
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": keyword,
                                "type": "phrase",
                                "fields": [
                                    "title",
                                    "call",
                                    "text"
                                ]
                            }
                        },
                        {
                            "range": {
                                "last_updated": {
                                    "gte": start,
                                    "lte": end,
                                    "format": "yyyy-MM-dd||dd/MM/yyyy||yyyy"
                                }
                            }
                        }
                    ]
                }
            }
        },
        filter_path=['count']
    )

    if result['count'] > 0:
        return True
    else:
        return False


if __name__ == "__main__":
    print(candidate_search("Governo e ministros", "2020-09-26", "2020-09-27"))
