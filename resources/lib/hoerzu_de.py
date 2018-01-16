#!/usr/bin/python
# -*- coding: utf-8 -*-

from tools import *
from dateutil import parser

class Scraper():
    def __init__(self):


        # Properties

        self.enabled = True
        self.baseurl = 'https://www.hoerzu.de'
        self.lang = 'de_DE'
        self.rssurl = 'https://www.hoerzu.de/rss/tipp/spielfilm/'
        self.friendlyname = 'HÖRZU Spielfilm Highlights'
        self.shortname = 'HÖRZU'
        self.icon = 'hoerzu.png'
        self.selector = '<item>'
        self.detailselector = '<div id="main-content">'
        self.err404 = 'hoerzu_dummy.jpg'


    def reset(self):
        self.channel = ''
        self.title = ''
        self.thumb = False
        self.detailURL = ''
        self.startdate = ''
        self.enddate = ''
        self.runtime = '0'
        self.genre = ''
        self.plot = ''
        self.cast = ''
        self.rating = ''


    def scrapeRSS(self, content):

        self.reset()

        try:
            self.channel = re.compile('<dc:subject>(.+?)</dc:subject>', re.DOTALL).findall(content)[0]
            self.genre = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' - ')[1]
            self.detailURL = re.compile('<link>(.+?)</link>', re.DOTALL).findall(content)[0]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ', 1)[1]
        except IndexError:
            pass

        try:
            self.startdate = parser.parse((re.compile('<dc:date>(.+?)</dc:date>',
                                                  re.DOTALL).findall(content)[0][0:19]).replace('T', ' ').replace('.', '-'))
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                try:
                    self.plot = re.compile('<p itemprop="description">(.+?)</p>', re.DOTALL).findall(content)[0]
                except IndexError:
                    pass

                # Cast
                try:
                    castlist = re.compile('<h2>Stars</h2>(.+?)</ul>', re.DOTALL).findall(content)[0]
                    cast = re.compile('<span itemprop="name">(.+?)</span>', re.DOTALL).findall(castlist)
                    self.cast = ', '.join(cast)
                except IndexError:
                    pass

                # Thumbnail
                try:
                    self.thumb = re.compile('<img src="(.+?)" itemprop="image"', re.DOTALL).findall(content)[0]
                except IndexError:
                    self.thumb = 'image://%s' % (self.err404)

                self.thumb = checkResource(self.thumb, self.err404)

                # Enddate

                try:
                    _s = re.compile('<div class="day">(.+?)<div class="labels">',
                                    re.DOTALL).findall(content)[0].split('/')[1].split(' - ')[1].strip()
                    self.enddate = self.startdate.replace(hour=int(_s[0:2]), minute=int(_s[3:5]))
                except IndexError:
                    self.enddate = self.startdate

                if self.startdate > self.enddate: self.enddate += datetime.timedelta(days=1)
                self.runtime = str((self.enddate - self.startdate).seconds / 60)

        except TypeError:
            pass

