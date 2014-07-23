import tweepy
import os

consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

class tweet_poster(object):
    def __init__(self):

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def post_tweet(self, text, image=None):
        if image:
            #
            image = str(image)
            tweet = self.api.update_with_media(image, text) 
        else:
            tweet = self.api.update_status(text)
        return tweet.id
