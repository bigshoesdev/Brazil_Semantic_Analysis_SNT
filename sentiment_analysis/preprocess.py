from os import path
import pandas as pd
from sentiment_analysis.tweet_preprocessing import preprocess_tweets

from config import config


def main():
    parameters = config.train_preprocess_parameters

    process_train_data(
        input_pos_name='train500.pos',
        input_neg_name='train500.neg',
        input_neu_name='train500.neu',
        parameters=parameters
    )

    process_test_data(
        input_pos_name='test.pos',
        input_neg_name='test.neg',
        input_neu_name='test.neu',
        parameters=parameters
    )


def process_train_data(input_pos_name='polarity.pos', input_neg_name='polarity.neg', input_neu_name='polarity.neu',
                       parameters=None):
    path_read_pos_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'dataset', input_pos_name)
    pos_df = read_train_data(path_read_pos_train)
    print('Positive training tweets read. Count: {}'.format(len(pos_df)))

    path_read_neg_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'dataset', input_neg_name)
    neg_df = read_train_data(path_read_neg_train)
    print('Negative training tweets read. Count: {}'.format(len(neg_df)))

    path_read_neu_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'dataset', input_neu_name)
    neu_df = read_train_data(path_read_neu_train)
    print('Neu training tweets read. Count: {}'.format(len(neu_df)))

    print('Processing positive tweets...')
    pos_df = preprocess_tweets(pos_df, 'text', parameters=parameters)
    print('Processing negative tweets...')
    neg_df = preprocess_tweets(neg_df, 'text', parameters=parameters)
    print('Processing neu tweets...')
    neu_df = preprocess_tweets(neu_df, 'text', parameters=parameters)

    path_save_pos_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'train', input_pos_name)
    pos_df.to_csv(path_save_pos_train, header=False, index=False)
    path_save_neg_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'train', input_neg_name)
    neg_df.to_csv(path_save_neg_train, header=False, index=False)
    path_save_neu_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'train', input_neu_name)
    neu_df.to_csv(path_save_neu_train, header=False, index=False)
    print('Processed training tweets have been successfully saved.')


def process_test_data(input_pos_name='test.pos', input_neg_name='test.neg', input_neu_name='test.neu',
                      parameters=None):
    path_read_pos_test = path.join(config.project_path, 'sentiment_analysis', 'data', 'dataset', input_pos_name)
    pos_df = read_train_data(path_read_pos_test)
    print('Positive test tweets read. Count: {}'.format(len(pos_df)))

    path_read_neg_test = path.join(config.project_path, 'sentiment_analysis', 'data', 'dataset', input_neg_name)
    neg_df = read_train_data(path_read_neg_test)
    print('Negative test tweets read. Count: {}'.format(len(neg_df)))

    path_read_neu_test = path.join(config.project_path, 'sentiment_analysis', 'data', 'dataset', input_neu_name)
    neu_df = read_train_data(path_read_neu_test)
    print('Neu test tweets read. Count: {}'.format(len(neu_df)))

    print('Processing positive tweets...')
    pos_df = preprocess_tweets(pos_df, 'text', parameters=parameters)
    print('Processing negative tweets...')
    neg_df = preprocess_tweets(neg_df, 'text', parameters=parameters)
    print('Processing neu tweets...')
    neu_df = preprocess_tweets(neu_df, 'text', parameters=parameters)

    path_save_pos_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'test', input_pos_name)
    pos_df.to_csv(path_save_pos_train, header=False, index=False)
    path_save_neg_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'test', input_neg_name)
    neg_df.to_csv(path_save_neg_train, header=False, index=False)
    path_save_neu_train = path.join(config.project_path, 'sentiment_analysis', 'data', 'test', input_neu_name)
    neu_df.to_csv(path_save_neu_train, header=False, index=False)
    print('Processed test tweets have been successfully saved.')


def read_train_data(file_path):
    """
    Reads training tweets.
    INPUT:
        file_path: path to file containing training set of tweets
    OUTPUT:
        data frame containing training set of tweets
    """
    with open(file_path, 'r', encoding='utf8') as f:
        train_data = f.read().splitlines()
    return pd.DataFrame({'text': train_data})


if __name__ == "__main__":
    main()
