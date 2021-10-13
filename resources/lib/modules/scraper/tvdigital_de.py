#!/usr/bin/python

from .. tools import *
from dateutil import parser

class Scraper():
    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'https://www.tvdigital.de'
        self.lang = 'de_DE'
        self.rssurl = 'https://www.tvdigital.de/tv-tipps/heute/spielfilm/'
        self.friendlyname = 'TV Digital Spielfilm Highlights'
        self.shortname = 'TV Digital'
        self.icon = 'tvd.png'
        self.selector = '<div id="content-left" class="tv-highlights">'
        self.subselector = '<div class="highlight-container">'
        self.detailselector = '<div class="rating-container">'
        self.err404 = 'tvd_dummy.jpg'

    def reset(self):

        # Items

        self.channel = ''
        self.title = ''
        self.thumb = False
        self.detailURL = ''
        self.startdate = ''
        self.enddate = ''
        self.runtime = 0
        self.genre = ''
        self.plot = ''
        self.cast = ''
        self.rating = 0


    def scrapeRSS(self, content):

        self.reset()
        try:
            self.channel = re.compile('<div class="highlight-channel">(.+?)</div>', re.DOTALL).findall(content)[0]
            self.title = re.compile('<a title="(.+?) "', re.DOTALL).findall(content)[0].split(':')[0]
            self.detailURL = self.baseurl + re.compile('href="(.+?)" name', re.DOTALL).findall(content)[0]
        except IndexError:
            pass
        try:
            self.startdate = parser.parse(re.compile('<div class="highlight-time">(.+?)</div>', re.DOTALL).findall(content)[0])
        except IndexError:
            pass
        try:
            _string = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(content)[0].split(' | ')
            self.genre =_string[0]
            self.runtime = int(_string[-1].split()[0]) * 60
            self.enddate = self.startdate + datetime.timedelta(seconds=self.runtime)
        except (IndexError, ValueError):
            pass
        try:
            self.thumb = re.compile('<img src="(.+?)"', re.DOTALL).findall(content)[0]
        except (IndexError, TypeError):
            pass

    def scrapeDetailPage(self, content, contentID):

        if contentID in content:
            container = content.split(contentID)
            container.pop(0)
            content = container[0]
        try:
            self.plot = re.compile('<p>(.+?)</p>', re.DOTALL).findall(content)[0]
        except (IndexError, TypeError):
            pass

        try:
            # calculate rating
            rating = re.compile('<span itemprop="ratingValue">(.+?)</span>', re.DOTALL).findall(content)[0]
            bestrating = re.compile('<span itemprop="bestRating">(.+?)</span>', re.DOTALL).findall(content)[0]
            self.rating = '{0:2.1f}'.format((int(rating) / int(bestrating)) * 10)
        except (IndexError, TypeError):
            pass
