#!/usr/bin/python

from tools import *


class Scraper():
    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'http://www.tvspielfilm.de'
        self.lang = 'de_DE'
        self.rssurl = 'http://www.tvspielfilm.de/tv-programm/rss/filme.xml'
        self.friendlyname = 'TV Spielfilm Highlights'
        self.shortname = 'TV Spielfilm'
        self.icon = 'tvspielfilm.png'
        self.selector = '<item>'
        self.detailselector = '<section id="content">'
        self.err404 = 'tvspielfilm_dummy.jpg'

    def reset(self):

        # Items, do not change!

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
            _ts = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[0]
            _ds = datetime.datetime.today()
            self.startdate = _ds.replace(hour=int(_ts[0:2]), minute=int(_ts[3:5]))
            self.channel = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[1]
            self.title = re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)[0].split(' | ')[2]
            self.detailURL = re.compile('<link>(.+?)</link>', re.DOTALL).findall(content)[0]

        except IndexError:
            pass

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                try:
                    self.plot = re.compile('<div class="description-text">(.+?)</p>', re.DOTALL).findall(content)[0].split('<p>')[1]
                    self.genre = re.compile('<span class="genre">(.+?)</span>', re.DOTALL).findall(content)[0].split(', ')[0]
                except IndexError:
                    pass

                # Broadcast Info (stop)

                try:
                    _s = re.compile('<span class="time">(.+?)</span>', re.DOTALL).findall(content)[2].split(' - ')[1]
                    self.enddate = self.startdate.replace(hour=int(_s[0:2]), minute=int(_s[3:5]))
                except IndexError:
                    self.enddate = self.startdate

                if self.startdate > self.enddate: self.enddate += datetime.timedelta(days=1)
                self.runtime = str((self.enddate - self.startdate).seconds / 60)

                # Cast
                try:
                    castlist = re.compile('<span class="name">(.+?)</span>', re.DOTALL).findall(content)
                    cast = []
                    for _cast in castlist: cast.append(re.sub('<[^>]*>', '', _cast))
                    self.cast = ', '.join(cast)
                except IndexError:
                    pass

                # Thumbnail
                try:
                    self.thumb = re.compile('<div class="gallery-box">(.+?)</div', re.DOTALL).findall(content)[0]
                    self.thumb = re.compile('href="(.+?)"', re.DOTALL).findall(self.thumb)[0]

                except IndexError:
                    self.thumb = 'image://%s' % (self.err404)

                self.thumb = checkResource(self.thumb, self.err404)

        except TypeError:
            pass

