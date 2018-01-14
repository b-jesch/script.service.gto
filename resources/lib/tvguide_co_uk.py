#!/usr/bin/python

import re
import urllib2
import datetime
from dateutil import parser

RSS_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

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


    def checkResource(self, resource, fallback):
        if not resource: return fallback
        _req = urllib2.Request(resource)
        try:
            _res = urllib2.urlopen(_req, timeout=5)
        except urllib2.HTTPError as e:
            if e.code == '404': return fallback
        except urllib2.URLError as e:
            return fallback
        else:
            return resource
        return fallback

    def scrapeRSS(self, content):

        self.reset()

        try:
            self.channel = re.compile('<span class="tvchannel">(.+?)</span>', re.DOTALL).findall(content)[-1]
            self.detailURL = re.compile('<a href="(.+?)" title="Click to rate and review">', re.DOTALL).findall(content)[0]
            self.title = re.compile('<span id=programmeheading class="programmeheading">(.+?)</span>', re.DOTALL).findall(content)[0]
            self.thumb = re.compile('background-image: url\((.+?)\)', re.DOTALL).findall(content)[0]
        except IndexError:
            pass

        self.thumb = self.checkResource(self.thumb, self.err404)
        try:
            self.plot = re.compile('<span class="programmetext">(.+?)</span>', re.DOTALL).findall(content)[0]
        except IndexError:
            pass

        try:
            self.startdate = (re.compile('<span class="datetime">(.+?)</span>', re.DOTALL).findall(content)[0])
        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                # Broadcast Info (stop)

                _start = parser.parse(self.startdate)
                try:
                    _stop = re.compile('<br>(.+?)<span style="color:#999">', re.DOTALL).findall(content)[0]
                    _pos = _stop.rfind('<br>') + 4
                    _stop = parser.parse(_stop[_pos:].split('-')[1])
                except IndexError:
                    _stop = _start

                if _start > _stop: _stop += datetime.timedelta(days=1)
                self.enddate = datetime.datetime.strftime(_stop, RSS_TIME_FORMAT)
                self.runtime = str((_stop - _start).seconds / 60)

                # Genre
                try:
                    self.genre = re.compile('Category: (.+?)</br>', re.DOTALL).findall(content)[0]

                    # Cast
                    self.cast = ', '.join(re.compile('<td class="actor">(.+?)</td>', re.DOTALL).findall(content))
                except IndexError:
                    pass

        except TypeError:
            pass

