#!/usr/bin/python

from .. tools import *
from dateutil import parser


class Scraper():

    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'http://www.tvguide.co.uk'
        self.lang = 'en'
        self.rssurl = 'http://www.tvguide.co.uk/TVhighlights.asp'
        self.friendlyname = 'TVGuide.co.uk - TV Highlights'
        self.shortname = 'TVGuide.co.uk'
        self.icon = 'tvguide.uk_logo.png'
        self.preselector = '<div  style="background:black; width:100%;">'
        self.postselector = '<div id="blog-entries">'
        self.subselector = '<div style="margin-top: 50px; background-image:'
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
        self.runtime = 0
        self.genre = ''
        self.plot = ''
        self.cast = ''
        self.rating = None

    def scrapeRSS(self, content):

        self.reset()

        try:
            self.channel = re.compile('<span class=tvchannel>(.+?)</span>', re.DOTALL).findall(content)[0]
            self.detailURL = re.compile('href="(.+?)"', re.DOTALL).findall(content)[0]
            self.title = re.compile('title="Click to rate and review">(.+?)</a>', re.DOTALL).findall(content)[0]
            self.thumb = re.compile('url\((.+?)\)', re.DOTALL).findall(content)[0]
            self.rating = re.compile('<span class="programmeheading">(.+?)</span>', re.DOTALL).findall(content)[0]
        except IndexError:
            writeLog('main parsing of \'%s\' incomplete' % self.shortname, level=xbmc.LOGWARNING)

        self.thumb = checkResource(self.thumb, self.err404)
        try:
            self.plot = re.compile('<div class="programmetext">(.+?)</div>', re.DOTALL).findall(content)[0]
        except IndexError:
            pass

        try:
            self.startdate = parser.parse((re.compile('<span class=datetime>(.+?)</span>', re.DOTALL).findall(content)[0]))
        except ValueError:
            self.startdate = parser.parse((re.compile('<span class="datetime">(.+?)</span>', re.DOTALL).findall(content)[0]).split()[0])
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
                self.runtime = int((self.enddate - self.startdate).seconds)

                # Genre
                try:
                    self.genre = re.compile('Category:(.+?)<br>', re.DOTALL).findall(content)[0].strip()
                except IndexError:
                    pass

        except TypeError:
            pass

