#!/usr/bin/python
# -*- coding: utf-8 -*-
import re

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
        self.preselector = '<div class="o-tv-tips__grid-wrapper">'     # discard content before this selector
        self.postselector = '<div id="loading" class="modal-loading">'      # discard content after this selector
        self.subselector = '<a class="m-epg-program-card"'      # split content into parts on this selector
        self.detailselector = '<div id="siteWrapper" class="">'             # discard content before this selector on detail pages
        self.err404 = 'hoerzu_dummy.jpg'                                    # dummy picture

    def reset(self):
        self.channel = ''
        self.title = ''
        self.thumb = False
        self.detailURL = ''
        self.startdate = None
        self.enddate = None
        self.runtime = 0
        self.genre = ''
        self.year = ''
        self.plot = ''
        self.cast = ''
        self.rating = None

    def scrapeRSS(self, content):
        self.reset()
        # cleanup from multiple spaces

        content = re.sub('\s{2,}', ' ', content)
        # print(content)
        try:
            parser_error = 'startdate'
            self.startdate = parser.parse((re.compile('<div class="m-epg-program-card__time">(.+?)</div',
                                                      re.DOTALL).findall(content)[0]))
            parser_error = 'channel'
            self.channel = re.compile('<div class="m-epg-program-card__channel-name">(.+?)</div>',
                                      re.DOTALL).findall(content)[0]
            parser_error = 'detailURL'
            self.detailURL = self.baseurl + \
                             re.compile('data-controller=\'ControllerEpgProgramCard\' '
                                        'href=\'(.+?)\'', re.DOTALL).findall(content)[0]
            parser_error = 'thumb'
            self.thumb = re.compile('<source srcset="(.+?)" media="\(min-width: 960px\)"/>',
                                    re.DOTALL).findall(content)[0].replace('278x202', '1280x720')
            self.thumb = checkResource(self.thumb, self.err404)

        except IndexError:
            writeLog('main parsing of \'%s\' breaks at %s' % (self.shortname, parser_error), level=xbmc.LOGWARNING)

    def scrapeDetailPage(self, content, contentID):

        try:
            if contentID in content:

                container = content.split(contentID)
                container.pop(0)
                content = re.sub('\s{2,}', ' ', container[0])

                try:
                    parser_error = 'title'
                    self.title = re.compile('data-keyword="(.+?)">', re.DOTALL).findall(content)[0]

                    parser_error = 'plot'
                    self.plot = re.compile('id=\'beschreibung\'><p>(.+?)</p></div>',
                                           re.DOTALL).findall(content)[0]

                    parser_error = 'cast'
                    self.cast = re.compile('<strong>Schauspieler:</strong></div><div class="m-person-list__entries">(.+?)</div>',
                                           re.DOTALL).findall(content)[0].strip()

                    parser_error = 'enddate'
                    _s = re.compile('<span class="o-epg_stage__time--hidden">(.+?)</span>',
                                    re.DOTALL).findall(content)[0]
                    _s = re.findall(r'\d{1,2}:\d{1,2}', _s)[0]
                    self.enddate = self.startdate.replace(hour=int(_s[0:2]), minute=int(_s[3:5]))

                    if self.startdate > self.enddate: self.enddate += timedelta(days=1)
                    self.runtime = int((self.enddate - self.startdate).seconds)

                    parser_error = 'genre'
                    self.genre = re.compile('<div class="o-epg_stage__series-info">(.+?)</div>',
                                            re.DOTALL).findall(content)[0].split(' • ')[0].strip()

                    parser_error = 'year'
                    self.year = re.compile('<div class="o-epg_stage__series-info">(.+?)</div>',
                                            re.DOTALL).findall(content)[0].split(' • ')[1]
                except IndexError:
                    writeLog('detail parsing of \'%s\' breaks at %s' % (self.shortname, parser_error),
                             level=xbmc.LOGWARNING)
        except TypeError:
            pass
