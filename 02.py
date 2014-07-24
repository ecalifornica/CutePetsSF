import os
import random
from urlparse import urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image
import twitter_oauth

class dog(object):
    '''
    Scrapes the SF SPCA adoptions pages. 
    Returns a list of URLs.
    '''
    def __init__(self, refresh=False):
        self.dog_list = self.make_dog_list(refresh)
        self.name = ''

    def scrape(self, page=0):
        dog_page = requests.get('https://www.sfspca.org/adoptions/dogs?page={}'.format(page))
        soup = BeautifulSoup(dog_page.text)
        dogs = soup.findAll('div', class_='node-animal')
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
            # Call scrape()
            dogs = self.scrape()
        else:
            import pickle
            with open('dog_image_urls.txt', 'r') as f:
                dogs = pickle.load(f)
        dog_list = []
        for url in dogs:
            path = urlparse(url)[2]
            filename = path.split('/').pop()
            filename_components = filename.split('-')
            # Dogs without a photo have a default image that ends in photo
            if filename_components[1] != 'photo.jpg':
                dog_id = filename_components[0]
                #
                dog = dict(dog_id=filename)
                dog_list.append(dog)
            else:
                pass
        return dog_list

    def choose_dog(self):
        '''
        Takes a list of dictionaries that represent dogs.
        Returns a random dog.
        '''
        choice = random.randrange(len(self.dog_list))
        lucky_dog = self.dog_list[choice]
        self.dog_id = lucky_dog.keys()[0]
        self.image = lucky_dog.values()[0]
        with open('tweeted_dogs.csv', 'r') as f:
            tweeted_dogs = f.read()
        if self.dog_id in tweeted_dogs:
            return self.pick_random_dog()
        else:
            with open('tweeted_dogs.csv', 'a') as f:
                f.write(self.dog_id + '\n')
            return self.dog_id
        
    def image(self):
        image_file = requests.get('https://www.sfspca.org/sites/default/' +
            'files/styles/480_width/public/images/animals/' +
            self.image)
        with open(self.image, 'wb') as f:
            for chunk in image_file.iter_content(chunk_size=1024):
                f.write(chunk)
        im = Image.open(self.image)
        im = im.convert('RGBA')
        out = Image.new(size=(450, 240), color='white', mode='RGBA')
        out.paste(im, (85, 0), im)
        out.save(self.image)

    def age_parse(self, age):
        years = ''
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

    def dog_info(self):
        self.choose_dog()
        self.image()
        self.profile_url = 'https://www.sfspca.org/' + 'adoptions/pet-details/' + self.dog_id

        dog_profile = requests.get(self.profile_url)
        profile_soup = BeautifulSoup(dog_profile.text)
        stats = soup.find_all('span', class_='field-label')
        try:
            self.name = soup.find('h1').text
            print self.name
            age = stats[1].next_sibling.next_sibling.text
            self.age = age_parse(age)
            self.gender = stats[2].next_sibling.next_sibling.text.strip('\n').strip(' ').lower()
            #self.personality
            try:
                energy = stats[3].next_sibling.next_sibling.text
                self.energy = energy.strip('\n').strip(' ').lower()
            except:
                self.energy = None
        except:
            self.dog_info()

# Public knowledge of dog:
# Image filename, name, age, gender, energy, personality
class tweet(object):
    def __init__(self):
        self.lucky_dog = dog()
        self.text = self.from_dog()
        self.image = lucky_dog.image

    def from_dog(self):
        name = self.lucky_dog.name
        print name
        age = self.lucky_dog.age
        gender = self.lucky_dog.gender
        energy = self.lucky_dog.energy
        url = self.lucky_dog.profile_url
        if energy != None:
            text = 'Hi! I\'m {}, {} old {} energy {}. {}'.format(name, age, energy, gender, url)
            return text
        else:
            text = 'Hi! I\'m {}, {} old {}. {}'.format(name, age, gender, url)
            return text

    def post_to_Twitter(self):
        twitter_api = twitter_oauth.tweet_poster()
        tweet_id = twitter_api.post_tweet(self.text, self.image)
        os.remove(tweet.image)
        return tweet_id



tweet_id = tweet().post_to_Twitter()
print('Success! Tweet ID: {}'.format(tweet_id))
