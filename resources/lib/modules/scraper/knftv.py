#!/usr/bin/python

from .. tools import *
from dateutil import parser
from xml.etree import ElementTree as ET

class Scraper():

    def __init__(self):

        # Properties

        self.enabled = True
        self.baseurl = 'https://www.staff.hs-mittweida.de/~jesch/knftv'
        self.lang = 'de_DE'
        self.rssurl = 'https://www.staff.hs-mittweida.de/~jesch/knftv/broadcasts.php'
        self.friendlyname = 'KN Community freeTV Highlights'
        self.shortname = 'Kodinerds freeTV'
        self.icon = 'knftv.png'
        self.selector = '<knftv>'
        self.detailselector = None
        self.err404 = 'knftv_dummy.jpg'


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
        knftv = ET.fromstring((self.selector + content).replace('</events>', ''))
        try:
            self.channel = knftv.findtext('ChannelName')
            self.title = knftv.findtext('Title') or knftv.findtext('EpgEventTitle') or None
            self.thumb = knftv.findtext('Icon')
            self.genre = knftv.findtext('Genre')
            
            try:
                self.rating = float(knftv.findtext('Rating'))
            except ValueError:
                pass

            _v = list()
            for voter in knftv.find('Recommendations').findall('User'): _v.append(voter.text)
            if len(_v) > 0:
                plot = ('%s\n\nEmpfohlen von %s' % (knftv.find('Plot').text, ', '.join(_v))).split('\n')
            else:
                plot = knftv.findtext('Plot').split('\n')
            p = list()
            for line in plot:
                p.append(line.strip())
            self.plot = '\n'.join(p)

            self.startdate = parser.parse(knftv.findtext('Date'), dayfirst=True)
            self.enddate = self.startdate.replace(hour=int(knftv.findtext('EndTime')[:2]), minute=int(knftv.findtext('EndTime')[-2:]))
            if self.startdate > self.enddate: self.enddate += datetime.timedelta(days=1)
            self.runtime = int((self.enddate - self.startdate).seconds)

            self.thumb = checkResource(self.thumb, self.err404)

        except Exception as e:
            print (e)
