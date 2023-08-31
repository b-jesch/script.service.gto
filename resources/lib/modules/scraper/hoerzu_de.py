#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc

from .. tools import *
from dateutil import parser


class Scraper():
    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'https://www.hoerzu.de'                              # base URL of scraper
        self.lang = 'de'                                                    # audience language
        self.rssurl = 'https://www.hoerzu.de/tv-tipps/'                     # scraper main content
        self.friendlyname = 'HÖRZU Spielfilm Highlights'
        self.shortname = 'HÖRZU'
        self.icon = 'hoerzu.png'
        self.preselector = '<div class="o-tv-tips o-tv-tips--tipsPage">'    # discard content before this selector
        self.postselector = '<div id="loading" class="modal-loading">'      # discard content after this selector
        self.subselector = '<div class="uk-width-1-2 uk-width-1-4@s">'      # split content into parts on this selector
        self.detailselector = '/head>'                                      # discard content before this selector on detail pages
        self.err404 = 'hoerzu_dummy.jpg'                                    # dummy picture

    def reset(self):
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
            self.startdate = parser.parse((re.compile('<div class="m-epg-program-card__time">(.+?)</div',
                                                      re.DOTALL).findall(content)[0]))
            self.channel = re.compile('<div class="m-epg-program-card__channel-name">(.+?)</div>',
                                      re.DOTALL).findall(content)[0]
            self.detailURL = self.baseurl + \
                             re.compile('<a class="m-epg-program-card" data-controller="ControllerEpgProgramCard" '
                                        'href="(.+?)"', re.DOTALL).findall(content)[0]
            self.title = re.compile('<h3 class="a-headline seriesName">(.+?)</h3>', re.DOTALL).findall(content)[0]
            self.thumb = re.compile('<source srcset="(.+?)" media="\(min-width: 960px\)" />',
                                    re.DOTALL).findall(content)[0].replace('202x147', '1280x720')
            self.thumb = checkResource(self.thumb, self.err404)

        except IndexError:
            writeLog('main parsing of \'%s\' incomplete' % self.shortname, level=xbmc.LOGWARNING)

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = container[0]

                try:
                    self.plot = re.compile('<p><strong>Beschreibung</strong></p><p>(.+?)</p></div>',
                                           re.DOTALL).findall(content)[0]
                except IndexError:
                    pass

                # Cast
                try:
                    self.cast = re.compile('<strong>Schauspieler:</strong></div></div><div '
                                           'class="m-accordion__item-name"><div '
                                           'class="m-accordion__only-stars">(.+?)</div>',
                                           re.DOTALL).findall(content)[0].strip()
                except IndexError:
                    pass

                # Enddate

                try:
                    _s = re.compile('<span class="o-epg_stage__time--hidden">(.+?)</span>',
                                    re.DOTALL).findall(content)[0].split()[-1]
                    self.enddate = self.startdate.replace(hour=int(_s[0:2]), minute=int(_s[3:5]))
                except IndexError:
                    self.enddate = self.startdate

                if self.startdate > self.enddate: self.enddate += datetime.timedelta(days=1)
                self.runtime = int((self.enddate - self.startdate).seconds)

                # Genre

                try:
                    self.genre = re.compile('<div class="o-epg_stage__series-info">(.+?)</div>',
                                            re.DOTALL).findall(content)[0].split(' • ')[0].strip()
                except IndexError:
                    pass

        except TypeError:
            pass
