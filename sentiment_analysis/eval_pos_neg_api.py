#! /usr/bin/env python

import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.contrib import learn
from bson.objectid import ObjectId
from sentiment_analysis.tweet_preprocessing import preprocess_tweets
from sentiment_analysis.data_helpers import batch_iter
from config import config
from utils.utils import get_posts

connection = config.initdb()
db = connection.scope_db


def sentimetal_analysis(candidate, sns_type):
    print(
        "##########################Sentimental Analysis {0} {1} ##########################".format(candidate, sns_type))
    posts = []

    sns_relation = db.sns_relation.find_one({'user_id': candidate}, {'user_list'})

    if not sns_relation:
        return

    if sns_type == 'twitter':
        tweets = get_posts(candidate, sns_type)
        for tweet in tweets:
            if tweet['tweet'] is not '':
                posts.append({'text': tweet['tweet'], 'type': 'twitter', 'id': tweet['_id']})
    elif sns_type == 'facebook':
        fposts = get_posts(candidate, sns_type)
        for post in fposts:
            if post['status_message'] is not '':
                posts.append({'text': post['status_message'], 'type': 'facebook', 'id': post['_id']})

    if len(posts) == 0:
        return

    if sns_type == 'facebook':
        db.fb_posts.update_many({'page_id': {"$in": sns_relation['user_list']}},
                                {'$unset': {'has_sentiment': None, 'sentiment_value': None}})
    elif sns_type == 'twitter':
        db.twitter_tweets.update_many({'user': {"$in": sns_relation['user_list']}},
                                      {'$unset': {'has_sentiment': None, 'sentiment_value': None}})

    print("Post Count {0}".format(len(posts)))

    BATCH_SIZE = 64
    CHECKPOINT_DIR = config.project_path + "sentiment_analysis/runs/" + config.sentiment_checkpoint
    ALLOW_SOFT_PLACEMENT = True
    LOG_DEVICE_PLACEMENT = False

    pdPosts = pd.DataFrame(posts)
    pos_df = preprocess_tweets(pdPosts, 'text', parameters=config.predict_preprocess_parameters)

    x_raw = [s[0].strip() for s in pos_df.values]

    # Map data into vocabulary
    vocab_path = os.path.join(CHECKPOINT_DIR, 'vocab')
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform(x_raw)))

    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint(CHECKPOINT_DIR + '/checkpoints')
    graph = tf.Graph()
    with graph.as_default():
        session_conf = tf.ConfigProto(
            allow_soft_placement=ALLOW_SOFT_PLACEMENT,
            log_device_placement=LOG_DEVICE_PLACEMENT)
        sess = tf.Session(config=session_conf)
        with sess.as_default():
            # Load the saved meta graph and restore variables
            saver = tf.train.import_meta_graph("{}.meta".format(checkpoint_file))
            saver.restore(sess, checkpoint_file)

            # Get the placeholders from the graph by name
            input_x = graph.get_operation_by_name("input_x").outputs[0]
            # input_y = graph.get_operation_by_name("input_y").outputs[0]
            dropout_keep_prob = graph.get_operation_by_name("dropout_keep_prob").outputs[0]

            # Tensors we want to evaluate
            predictions = graph.get_operation_by_name("output/predictions").outputs[0]

            # Generate batches for one epoch
            batches = batch_iter(list(x_test), BATCH_SIZE, 1, shuffle=False)

            # Collect the predictions here
            all_predictions = []
            print('step 7', batches)
            for x_test_batch in batches:
                batch_predictions = sess.run(predictions, {input_x: x_test_batch, dropout_keep_prob: 1.0})
                print('loop: ', batch_predictions)
                all_predictions = np.concatenate([all_predictions, batch_predictions])

    print("Prediction Count {0}".format(len(all_predictions)))
    for i in range(len(all_predictions)):
        sentiment_value = int(all_predictions[i])
        post = posts[i]

        if post['type'] == 'facebook':
            db.fb_posts.update_one({"_id": ObjectId(post["id"])},
                                   {"$set": {'has_sentiment': True, 'sentiment_value': sentiment_value}})
        elif post['type'] == 'twitter':
            db.twitter_tweets.update_one({"_id": ObjectId(post["id"])},
                                         {"$set": {'has_sentiment': True, 'sentiment_value': sentiment_value}})


def sentimetal_analysis_comments(candidate, sns_type):
    print(
        "##########################Sentimental Comments Analysis {0} {1} ##########################".format(candidate,
                                                                                                            sns_type))
    posts = []

    sns_relation = db.sns_relation.find_one({'user_id': candidate}, {'user_list'})

    if not sns_relation:
        return

    if sns_type == 'twitter':
        tweet_replies = db.twitter_replies.find(
            {'user': {"$in": sns_relation['user_list']}, 'tweet': {"$exists": True, "$ne": ""}},
            no_cursor_timeout=True)
        for reply in tweet_replies:
            if reply['tweet'] is not '':
                posts.append({'text': reply['tweet'], 'type': 'twitter', 'id': reply['_id']})
    elif sns_type == 'facebook':
        fcomments = db.fb_comments.find(
            {'page_id': {"$in": sns_relation['user_list']}, 'comment_message': {"$exists": True, "$ne": ""}},
            no_cursor_timeout=True)
        for fcomment in fcomments:
            if fcomment['comment_message'] is not '':
                posts.append({'text': fcomment['comment_message'], 'type': 'facebook', 'id': fcomment['_id']})

    if len(posts) == 0:
        return

    if sns_type == 'facebook':
        db.fb_comments.update_many({'page_id': {"$in": sns_relation['user_list']}},
                                   {'$unset': {'has_sentiment': None, 'sentiment_value': None}})
    elif sns_type == 'twitter':
        db.twitter_replies.update_many({'user': {"$in": sns_relation['user_list']}},
                                       {'$unset': {'has_sentiment': None, 'sentiment_value': None}})

    print("Post Count {0}".format(len(posts)))

    BATCH_SIZE = 64
    CHECKPOINT_DIR = config.project_path + "sentiment_analysis/runs/" + config.sentiment_checkpoint
    ALLOW_SOFT_PLACEMENT = True
    LOG_DEVICE_PLACEMENT = False

    pdPosts = pd.DataFrame(posts)
    pos_df = preprocess_tweets(pdPosts, 'text', parameters=config.predict_preprocess_parameters)

    x_raw = [s[0].strip() for s in pos_df.values]

    # Map data into vocabulary
    vocab_path = os.path.join(CHECKPOINT_DIR, 'vocab')
    vocab_processor = learn.preprocessing.VocabularyProcessor.restore(vocab_path)
    x_test = np.array(list(vocab_processor.transform(x_raw)))

    # Evaluation
    # ==================================================
    checkpoint_file = tf.train.latest_checkpoint(CHECKPOINT_DIR + '/checkpoints')
    graph = tf.Graph()
    with graph.as_default():
        session_conf = tf.ConfigProto(
            allow_soft_placement=ALLOW_SOFT_PLACEMENT,
            log_device_placement=LOG_DEVICE_PLACEMENT)
        sess = tf.Session(config=session_conf)
        with sess.as_default():
            # Load the saved meta graph and restore variables
            saver = tf.train.import_meta_graph("{}.meta".format(checkpoint_file))
            saver.restore(sess, checkpoint_file)

            # Get the placeholders from the graph by name
            input_x = graph.get_operation_by_name("input_x").outputs[0]
            # input_y = graph.get_operation_by_name("input_y").outputs[0]
            dropout_keep_prob = graph.get_operation_by_name("dropout_keep_prob").outputs[0]

            # Tensors we want to evaluate
            predictions = graph.get_operation_by_name("output/predictions").outputs[0]

            # Generate batches for one epoch
            batches = batch_iter(list(x_test), BATCH_SIZE, 1, shuffle=False)

            # Collect the predictions here
            all_predictions = []
            print('step 7', batches)
            for x_test_batch in batches:
                batch_predictions = sess.run(predictions, {input_x: x_test_batch, dropout_keep_prob: 1.0})
                print('loop: ', batch_predictions)
                all_predictions = np.concatenate([all_predictions, batch_predictions])

    print("Prediction Count {0}".format(len(all_predictions)))
    for i in range(len(all_predictions)):
        sentiment_value = int(all_predictions[i])
        post = posts[i]

        if post['type'] == 'facebook':
            db.fb_comments.update_one({"_id": ObjectId(post["id"])},
                                      {"$set": {'has_sentiment': True, 'sentiment_value': sentiment_value}})
        elif post['type'] == 'twitter':
            db.twitter_replies.update_one({"_id": ObjectId(post["id"])},
                                          {"$set": {'has_sentiment': True, 'sentiment_value': sentiment_value}})


if __name__ == '__main__':
    # candidate = 'RogerioLisboaOFICIAL'
    # sns_type = 'facebook'
    #
    # sentimetal_analysis(candidate, sns_type)
    # sentimetal_analysis_comments(candidate, sns_type)

    # candidate = 'RogerioMLisboa'
    # sns_type = 'twitter'
    #
    # sentimetal_analysis(candidate, sns_type)
    # sentimetal_analysis_comments(candidate, sns_type)

    sns_relation_data = list(db.sns_relation.find({}))
    for i in range(len(sns_relation_data)):
        sns_relation = sns_relation_data[i]
        print("=========================== : " + sns_relation['user_id'])
        sentimetal_analysis_comments(sns_relation['user_id'], sns_relation['type'])
