#!/usr/bin/env python

import re
import os
import pickle
from lxml import html
from requests import get


SAVEOFFLINE_URL = 'http://www.saveitoffline.com/process/?url={}&type=json'
LABEL = '360p - mp4'
def get_vimeo_download_url(url):
    r = get(SAVEOFFLINE_URL.format(url))
    dl_urls = r.json()['urls']
    for u in dl_urls:
        if u['label'] == LABEL:
            return u['id']


CLIENT_ID = '3GtnQtvbxU1K5jhCPJcq2xyZ6xtctDIc'
SOUNDCLOUD_API = 'http://api.soundcloud.com/tracks/{}/streams?client_id={}&secret_token={}'
PATTERN = re.compile(r'^.+/tracks/(?P<track_id>\d+)%3Fsecret_token%3D(?P<secret_token>[^&]+)')
def get_soundcloud_download_url(url):
    m = PATTERN.search(url)
    canonical_url = SOUNDCLOUD_API.format(m.group('track_id'), CLIENT_ID, m.group('secret_token'))
    r = get(canonical_url).json()
    return r['http_mp3_128_url'].replace('https', 'http')


articles = []
try:
    print('Trying to load articles from disk...')
    articles = pickle.load(open("articles.pickle", "rb"))
except:
    print('Failed. Fetching them from the source...')
    PAGE_URL = 'http://resolu.co/page/{}'
    COOKIES = {
            'wordpress_logged_in_29e7fd7ad9b0ecf426ff3ce0ce82daf7': 'gabin1504595%7C1521315177%7C19TWmaIwTkApY5cRcxjqgIitUTiUTnQeXOU6qAyG31n%7Cae513891b6b314acff0a831843aa9b56015148e611effa7c05d7fa41de123aba'
    }
    page = 1
    while page <= 8:
        print('Fetching articles for page {}...'.format(page))
        r = get(PAGE_URL.format(page), cookies=COOKIES)
        tree = html.fromstring(r.content)
        for article in tree.xpath('//article'):
            articles.append({
                'title': article.xpath('.//h2/a/text()')[0].strip(),
                'date': article.xpath('.//ul[contains(@class, "post-metadatas")]/li[1]/text()')[0].strip(),
                'category': article.xpath('.//ul[contains(@class, "post-metadatas")]/li[last()]/a/text()')[0].strip(),
                'url': article.xpath('.//iframe/@src')[0],
            })
        page += 1

    print('Retrieving their download URL...')
    for article in articles:
        if 'vimeo' in article['url']:
            article['url'] = get_vimeo_download_url(article['url'])
            article['type'] = 'mp4'
        elif 'soundcloud' in article['url']:
            article['url'] = get_soundcloud_download_url(article['url'])
            article['type'] = 'mp3'
    
    print('Dumping the list of articles to disk...')
    with open("articles.pickle", "wb") as f:
        pickle.dump(articles, f, pickle.HIGHEST_PROTOCOL)

print('Found {} articles.'.format(len(articles)))

root_dir = os.path.dirname(os.path.realpath(__file__))
for article in articles:
    print('Downloading {}...'.format(article['title']))
    filename = os.path.join(root_dir, u'output/{category}/{title} ({date}).{type}'.format(**article))
    if os.path.exists(filename):
        print('|-> Already downloaded.')
        continue

    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    r = get(article['url'])
    with open(filename, 'wb') as f:
        f.write(r.content)

print('Scraping completed.')
