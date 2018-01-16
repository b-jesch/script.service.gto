#!/usr/bin/python

from tools import *
from dateutil import parser

class Scraper():

    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'http://www.klack.de'
        self.lang = 'de_DE'
        self.rssurl = 'http://www.klack.de/xml/motorsportRSS.xml'
        self.friendlyname = 'klack.de - Motorsport'
        self.shortname = 'klack.de - Motorsport'
        self.icon = 'klack.png'
        self.selector = '<item>'
        self.detailselector = '<table id="content">'
        self.err404 = 'klackde_dummy.jpg'


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
            self.channel = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ')[0]
            self.detailURL = re.compile('<link>(.+?)</link>', re.DOTALL).findall(content)[0]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(': ')[1]
            self.thumb = re.compile('<img align="left" src="(.+?)"', re.DOTALL).findall(content)[0].replace('150x100.jpg', '500x333.jpg')
        except IndexError:
            pass

        self.thumb = checkResource(self.thumb, self.err404)
        try:
            self.plot = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0].split('</a>')[1][:-3]
        except IndexError:
            self.plot = re.compile('<description>(.+?)</description>', re.DOTALL).findall(content)[0].split('<br>')[1][:-3]

        try:
            self.startdate = parser.parse((re.compile('<dc:date>(.+?)</dc:date>', re.DOTALL).findall(content)[0][0:19]).replace('T', ' '))
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
                    _s = re.compile('<span style="color: #d10159!important">(.+?)</span>', re.DOTALL).findall(content)[0].split()[2]
                    self.enddate = self.startdate.replace(hour=int(_s[0:2]), minute=int(_s[3:5]))
                except IndexError:
                    self.enddate = self.startdate

                if self.startdate > self.enddate: self.enddate += datetime.timedelta(days=1)
                self.runtime = str((self.enddate - self.startdate).seconds / 60)

                # Genre

                try:
                    self.genre = re.compile('<span>(.+?)</span>', re.DOTALL).findall(content)[4].strip()

                    # Cast
                    self.cast = ', '.join(re.compile('<td class="actor">(.+?)</td>', re.DOTALL).findall(content))
                except IndexError:
                    pass

        except TypeError:
            pass

