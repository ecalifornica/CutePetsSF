from bs4 import BeautifulSoup
import requests
from urlparse import urlparse
import pickle
import random
import twitter_oauth
import os


class cuties(object):
    def __init__(self):
        self.dogs = None
        self.image_base = (
                        'https://www.sfspca.org/sites/default/files/styles/' +
                        '480_width/public/images/animals/')
        self.profile_base = 'https://www.sfspca.org/adoptions/pet-details/'

        self.get_fresh_data()
        self.make_dog_lists()

    def scrape(self, page=0):
        dog_page = requests.get('https://www.sfspca.org/adoptions/dogs?page={}'.format(page))
        soup = BeautifulSoup(dog_page.text)
        dogs = soup.findAll('div', class_='node-animal')
        if len(dogs) == 0:
            return []
        else:
            urls = [dog.img['src'] for dog in dogs]
        return urls + self.scrape(page+1)

    def get_fresh_data(self, refresh=False):
        if refresh:
            self.dogs = self.scrape()
            with open('dog_image_urls.txt', 'w') as f:
                pickle.dump(self.dogs, f)
        elif self.dogs is None:
            with open('dog_image_urls.txt', 'r') as f:
                self.dogs = pickle.load(f)
        else:
            return self.dogs
                
    def make_dog_lists(self):
        self.image_urls = []
        self.profile_urls = []
        for url in self.dogs:
            path = urlparse(url)[2]
            filename = path.split('/').pop()
            has_photos, dog_id = self.has_photo(filename)
            if has_photos:
                self.image_urls.append(filename)
                self.profile_urls.append(dog_id)
                #return dog_id, self.base_image_url + filename
            else:
                #return None
                pass

    def has_photo(self, filename):
        filename = filename.split('-')
        return filename[1] != 'photo.jpg', filename[0]

    def timer(self):
        pass

    def random_pooch(self):
        pooch = random.randrange(len(self.image_urls))
        pooch_url = self.profile_urls[pooch]
        self.pooch_image = self.image_urls[pooch]
        with open('tweeted_dogs.csv', 'r') as f:
            tweeted_dogs = f.read()
        if pooch_url in tweeted_dogs:
            return self.random_pooch()
        else:
            with open('tweeted_dogs.csv', 'a') as f:
                f.write(pooch_url + '\n')
            return self.profile_base + pooch_url, self.pooch_image

    def pooch_info(self):
        pass

    def resize_image(self, pooch_image):
        from PIL import Image
        im = Image.open(pooch_image)
        #
        im = im.convert('RGBA')
        out = Image.new(size=(450, 240), color='white', mode='RGBA')
        out.paste(im, (85, 0), im)
        #out.save('/var/www/ecal/blametommy.com/public/barf5.jpg')
        out.save(pooch_image)

    def compose_tweet(self):
        pooch_url, self.pooch_image = cuties_in_sf.random_pooch()
        pooch_page = requests.get(pooch_url)
        image_file = requests.get(self.image_base + self.pooch_image)
        with open(self.pooch_image, 'wb') as f:
            for chunk in image_file.iter_content(chunk_size=1024):
                f.write(chunk)

        # Resize image.
        self.resize_image(self.pooch_image)

        soup = BeautifulSoup(pooch_page.text)
        try:
            age = soup.find_all('span', class_='field-label')[1].next_sibling.next_sibling.text
        except:
            # Add logging.
            # This excludes dogs without an age listed, not fair.
            print('No age, dog profile removed? Retrying...')
            return compose_tweet()
        gender = soup.find_all('span', class_='field-label')[2].next_sibling.next_sibling.text
        name = soup.find('h1').text
        try:
            energy = soup.find_all('span', class_='field-label')[3].next_sibling.next_sibling.text
            energy = energy.strip('\n').strip(' ').lower()
        except:
            energy = None
        years = ''
        quantity = ''
        for i in age:
            if i == 'Y':
                scale = 'year'
                break
            elif i == 'M':
                scale = 'month'
                break
            if i in '0123456789':
                quantity += i
        if quantity == '1':
            age_string = 'a {}'.format(scale)
        elif quantity in ('8', '11'):
            age_string = 'an {} {}'.format('eight', scale)
        else:
            age_string = 'a {} {}'.format(quantity, scale)
        gender = gender.strip('\n').strip(' ').lower()
        # personality
        # print soup.find(attrs={"name": "description"})
        if energy != None:
            tweet_text = 'Hi, I\'m {}, {} old {} energy {}. {}'.format(name, age_string, energy, gender, pooch_url)
        else:
            tweet_text = 'Hi, I\'m {}, {} old {}. {}'.format(name, age_string, gender, pooch_url)
        return self.pooch_image, tweet_text


cuties_in_sf = cuties()
tweet_image, tweet_text = cuties_in_sf.compose_tweet()
poster = twitter_oauth.tweet_poster()
tweet_id = poster.post_tweet(tweet_text, tweet_image)
os.remove(tweet_image)
print('Success! Tweet ID: {}'.format(tweet_id))
