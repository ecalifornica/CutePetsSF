import tweepy
import os

consumer_key = os.environ.get('CUTIESINSF_CONSUMER_KEY')
consumer_secret = os.environ.get('CUTIESINSF_CONSUMER_SECRET')
access_token = os.environ.get('CUTIESINSF_ACCESS_TOKEN')
access_token_secret = os.environ.get('CUTIESINSF_ACCESS_TOKEN_SECRET')

class tweet_poster(object):
    def __init__(self):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def post_tweet(self, text, image=None):
        self.status_count = self.api.me().statuses_count
        if self.status_count % 30 == 0:
            tweet = self.api.update_status('I\'m a bot that tweets about pets available for adoption at sfspca.org You can find my source code at github.com/ecalifornica/CutiesInSF')
        elif image:
            image = str(image)
            tweet = self.api.update_with_media(image, text) 
        else:
            tweet = self.api.update_status(text)
        return tweet.id

    def follow_followers(self):
        pass

    def about_bot(self):
        return self.api.me()
