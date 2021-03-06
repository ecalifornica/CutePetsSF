import logging
import os
import random
from urlparse import urlparse

from bs4 import BeautifulSoup
import pickle
from PIL import Image
import requests

import twitter_oauth

logging.basicConfig(level=logging.DEBUG, filename='cuties.log')
logging.debug('Cuties start')


class Dog(object):
    '''
    Scrapes the SF SPCA adoptions pages.
    Returns a list of URLs.
    '''
    def __init__(self, testing=False, refresh=True):
        self.dog_list = self.make_dog_list(refresh)
        self.name = 'barf'
        self.dog_info(testing)

    def scrape(self, page=0):
        logging.debug('Making a request.')
        dog_page = requests.get('https://www.sfspca.org/adoptions/dogs?'
                                'page={}'.format(page))
        dog_soup = BeautifulSoup(dog_page.text)
        dogs = dog_soup.findAll('div', class_='node-animal')
        if len(dogs) == 0:
            return []
        else:
            urls = [dog.img['src'] for dog in dogs]

        return urls + self.scrape(page+1)

    def make_dog_list(self, refresh):
        '''
        Calls scrape or loads a list of dog image urls.
        Parses the list and outputs a list of dictionaries.
        Each dictionary is dog_id: dog_image_filename.
        '''
        if refresh:
            dogs = self.scrape()
            logging.debug('Currently available pups: {}'.format(len(dogs)))
        else:
            with open('dog_image_urls.txt', 'r') as f:
                dogs = pickle.load(f)
        dog_list = []
        for url in dogs:
            path = urlparse(url)[2]
            filename = path.split('/').pop()
            filename_components = filename.split('-')
            # TODO
            if filename_components[1] != 'photo.jpg':
                dog_id = filename_components[0]
                dog = {dog_id: filename}
                dog_list.append(dog)
            else:
                pass
        logging.debug('Number of dogs with photos: {}'.format(len(dog_list)))

        return dog_list

    def choose_dog(self, testing=False):
        '''
        Takes a list of dictionaries that represent dogs.
        Returns a random dog.
        '''
        logging.debug('Choosing a random dog.')
        choice = random.randrange(len(self.dog_list))
        lucky_dog = self.dog_list[choice]
        self.dog_id = lucky_dog.keys()[0]
        self.image = lucky_dog.values()[0]

        with open('tweeted_dogs.csv', 'r') as f:
            tweeted_dogs = f.read()

        if self.dog_id in tweeted_dogs:
            logging.debug('Repeat dog, choosing another')
            os.remove(self.image)

            return self.choose_dog()

        elif not testing:
            with open('tweeted_dogs.csv', 'a') as f:
                logging.debug('Dog ID {} tweet recorded'.format(self.dog_id))
                f.write(self.dog_id + '\n')
        logging.debug('New dog id: {}'.format(self.dog_id))

        return self.dog_id

    def dog_image(self):
        image_path = ('https://www.sfspca.org/sites/default/files/styles/'
                      '480_width/public/images/animals' +
                      self.image)
        image_file = requests.get(image_path)

        with open(self.image, 'wb') as f:
            for chunk in image_file.iter_content(chunk_size=1024):
                f.write(chunk)

        im = Image.open(self.image)
        im = im.convert('RGBA')
        out = Image.new(size=(450, 240), color='white', mode='RGBA')
        out.paste(im, (85, 0), im)
        out.save(self.image)

        return self.image

    def age_parse(self, age):
        quantity = ''

        for i in age:
            if i == 'Y':
                scale = 'year'
                break
            elif i == 'M':
                scale = 'month'
                break
            if i.isdigit:
                quantity += i

        if quantity == '1':
            age_string = 'a {}'.format(scale)
        elif quantity in ('8', '11'):
            age_string = 'an {} {}'.format(quantity, scale)
        else:
            age_string = 'a {} {}'.format(quantity, scale)

        return age_string

    def dog_info(self, testing):
        self.choose_dog(testing)
        self.dog_image()
        self.profile_url = ('https://www.sfspca.org/adoptions/pet-details/' +
                            self.dog_id)
        dog_profile = requests.get(self.profile_url)
        profile_soup = BeautifulSoup(dog_profile.text)
        stats = profile_soup.find_all('span', class_='field-label')

        try:
            self.name = profile_soup.find('h1').text
            age = stats[1].next_sibling.next_sibling.text.strip('\n ')
            self.age = self.age_parse(age)
            self.gender = stats[2].next_sibling \
                                  .next_sibling \
                                  .text.strip('\n') \
                                  .strip(' ') \
                                  .lower()

            # self.personality
            try:
                energy = stats[3].next_sibling.next_sibling.text
                self.energy = energy.strip('\n').strip(' ').lower()
            except:
                self.energy = None
        except:
            logging.debug('No info for dog, choosing another.')
            os.remove(self.image)
            self.dog_info()


class Tweet(object):
    '''
    Image filename, name, age, gender, energy, personality
    '''
    def __init__(self, testing=False):
        self.lucky_dog = Dog(testing)
        self.text = self.from_dog()
        self.image = self.lucky_dog.image

    def from_dog(self):
        name = self.lucky_dog.name
        age = self.lucky_dog.age
        gender = self.lucky_dog.gender
        energy = self.lucky_dog.energy
        url = self.lucky_dog.profile_url
        if energy is not None:
            if energy in ('low', 'medium', 'high'):
                text = 'Hi! I\'m {}, {} old {} energy {}. {}'.format(name,
                                                                     age,
                                                                     energy,
                                                                     gender,
                                                                     url)
            else:
                text = 'Hi! I\'m {}, {} old {} {}. {}'.format(name,
                                                              age,
                                                              energy,
                                                              gender,
                                                              url)
            return text
        else:
            text = 'Hi! I\'m {}, {} old {}. {}'.format(name,
                                                       age,
                                                       gender,
                                                       url)
            return text

    def post_to_Twitter(self):
        twitter_api = twitter_oauth.TweetPoster()
        tweet_id = twitter_api.post_tweet(self.text, self.image)
        os.remove(self.image)
        return tweet_id


cutepetssf_tweet = Tweet()
tweet_id = cutepetssf_tweet.post_to_Twitter()
logging.debug('Success! Tweet ID: {}'.format(tweet_id))
