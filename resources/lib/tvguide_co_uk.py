#!/usr/bin/python

from tools import *
from dateutil import parser

class Scraper():

    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'http://www.tvguide.co.uk'
        self.lang = 'en_GB'
        self.rssurl = 'http://www.tvguide.co.uk/TVhighlights.asp'
        self.friendlyname = 'TVGuide.co.uk - TV Highlights'
        self.shortname = 'TVGuide.co.uk'
        self.icon = 'tvguide.uk_logo.png'
        self.selector = '<span class=programmeheading'
        self.subselector = 'id="table1"'
        self.detailselector = '<div id="divLHS">'
        self.err404 = 'tvguide.uk_logo.png'


    def reset(self):

        # Items

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
            self.channel = re.compile('<span class="tvchannel">(.+?)</span>', re.DOTALL).findall(content)[-1]
            self.detailURL = re.compile('<a href="(.+?)" title="Click to rate and review">', re.DOTALL).findall(content)[0]
            self.title = re.compile('<span id=programmeheading class="programmeheading">(.+?)</span>', re.DOTALL).findall(content)[0]
            self.thumb = re.compile('background-image: url\((.+?)\)', re.DOTALL).findall(content)[0]
        except IndexError:
            pass

        self.thumb = checkResource(self.thumb, self.err404)
        try:
            self.plot = re.compile('<span class="programmetext">(.+?)</span>', re.DOTALL).findall(content)[0]
        except IndexError:
            pass

        try:
            self.startdate = parser.parse((re.compile('<span class="datetime">(.+?)</span>', re.DOTALL).findall(content)[0]))
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                # Broadcast Info (stop)

                try:
                    _stop = re.compile('<br>(.+?)<span style="color:#999">', re.DOTALL).findall(content)[0]
                    _pos = _stop.rfind('<br>') + 4
                    self.enddate = parser.parse(_stop[_pos:].split('-')[1])
                except IndexError:
                    self.enddate = self.startdate

                if self.startdate > self.enddate: self.enddate += datetime.timedelta(days=1)
                self.runtime = str((self.enddate - self.startdate).seconds / 60)

                # Genre
                try:
                    self.genre = re.compile('Category: (.+?)</br>', re.DOTALL).findall(content)[0]

                    # Cast
                    self.cast = ', '.join(re.compile('<td class="actor">(.+?)</td>', re.DOTALL).findall(content))
                except IndexError:
                    pass

        except TypeError:
            pass

