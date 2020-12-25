import pymongo
from elasticsearch import Elasticsearch

class Config(object):
    debug = True

    ## SCRAPING TIMEDELTA FROM CURRENT TIME (Years)
    timedelta_facebook = 3
    timedelta_twitter = 4

    ## Facebook APP
    app_id = "253032921939778"
    app_secret = "7c7762f66dc7c08b4f46c17ec8b59083"  # DO NOT SHARE WITH ANYONE!
    access_token = app_id + '|' + app_secret
    # access_token = "EAADmIdFtv0IBAJZBmrv6EOSMsn3SK4OIDCPkfTYNmlGZAOFj1DXx2lGsrqWXZAaboWA24ZAuYQKxZCs4OiTwWVb2iYqSB5SYz8rIw3drZAqF0PAeEitX6frKYcXEowvZANjDx5QVcIEvan8qaXU8LMH7XDDahmZCkVsqLZBKoD08cmQZDZD"

    ## TWITTTER API
    twitter_api = {
        'consumer_key': "3C7pZdnXpxLydhas6wkAe11yM",
        'consumer_secret': "WGvyQ52zuIo6RbmsdGrmSsoS6P2s93yriIJZzFJVTKeMeIQ9Kl",
        'access_token': "1093968159890128897-TzuvGyaVrKWfyW3dTEFQSZOs0dCKic",
        'access_token_secret': "jv71F9F6OKOoowNFJ4iJL8plAUQ1tZiYOE8s9aqxVrhL0"
    }

    ## Painel Facebook Page Access Token Acces
    access_token_api_url = 'https://painel.scopo.online/api/getdeep_info/get_sm_info'
    access_token_api_token = '6ec41948bf5f9c42c3a9a2407b0663ddbae6b455'

    ##COMMENTS PER_PAGE
    comments_per_page = 50

    ## SENTIMENT_CHECKPOINT
    sentiment_checkpoint = '1589341780'

    ## SENTIMENT_TRAIN_PARAMETER
    train_preprocess_parameters = {
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

    ## SENTIMENT_PREDICT_PARAMETER
    predict_preprocess_parameters = {
        'filter_duplicates': False,
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

    # SCHEDULE JOB
    delta_time = 1080
    offset_time = 60
    num_job = 1

    if debug:
        project_path = ''
    else:
        project_path = '/opt/sm-scopo/scopo_deep/'

    # DB
    def initdb(self):
        '''
        Creates a new mongodb database or connects to an existing one.
        '''
        if self.debug:
            uri = 'mongodb://localhost:27017'
        else:
            uri = 'mongodb://scopodeep:Dasfadas%402020%23%21a@scopodeep-shard-00-00.xckgj.mongodb.net:27017,scopodeep-shard-00-01.xckgj.mongodb.net:27017,scopodeep-shard-00-02.xckgj.mongodb.net:27017/test?ssl=true&replicaSet=atlas-rjve2f-shard-0&authSource=admin&retryWrites=true&w=majority'

        connection = pymongo.MongoClient(uri)

        return connection

    es_index_name = 'news'

    # ElasticSearch
    def init_elastic(self):
        es_object = Elasticsearch(hosts=[{"host": "localhost", "port": 9200}], )

        return es_object

config = Config()
