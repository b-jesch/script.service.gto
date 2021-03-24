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
        except IndexError:
            pass
        try:
            self.startdate = parser.parse(re.compile('<div class="highlight-time">(.+?)</div>', re.DOTALL).findall(content)[0])
        except IndexError:
            pass
        try:
            _string = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(content)[0].split(' | ')
            self.genre =_string[0]
            self.cast = (' | ').join(_string[1:-1])
            self.runtime = int(_string[-1].split()[0])
            self.enddate = self.startdate + datetime.timedelta(minutes=self.runtime)
        except (IndexError, ValueError):
            pass
        try:
            self.thumb = re.compile('<img src="(.+?)"', re.DOTALL).findall(content)[0]
        except (IndexError, TypeError):
            pass
        try:
            self.plot = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(content)[1]
        except (IndexError, TypeError):
            pass
