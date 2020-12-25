import argparse

from wordcloud import WordCloud
from utils.utils import get_posts


def get_token_list_str(tweets, sns_name):
    tw_token = []
    tweets.rewind()

    if sns_name == 'twitter':
        field_name = 'tokens'
    else:
        field_name = 'tokens'

    for tw in tweets:
        if tw[field_name] is not '':
            tw_token.append(', '.join(tw[field_name]))

    token_str = ', '.join(tw_token)

    return token_str


def word_tag_cloud(candidate, sns_name):
    tweets = get_posts(candidate, sns_name)

    if not tweets:
        return {
            'status': 404,
            'message': "Wrong SNS name"
        }

    print('tweets', tweets.count())

    token_str = get_token_list_str(tweets, sns_name)

    # Create a WordCloud object
    wordcloud = WordCloud(background_color="white", max_words=5000, contour_width=3, contour_color='steelblue',
                          width=576, height=240, collocations=False)

    # Generate a word cloud
    wordcloud.generate(token_str)
    # Visualize the word cloud
    return wordcloud.to_image()


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

    word_tag_cloud(candidate, sns_name)
