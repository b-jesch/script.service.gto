#!/usr/bin/python
# -*- coding: utf-8 -*-

from resources.lib.tools import *

import urllib
import urllib2
import ssl
import sys
import socket
import xbmcvfs
import xbmcplugin
import time

from dateutil import parser

OPT_ENABLE_INFO = getAddonSetting('enableinfo', BOOL)
OPT_PREFER_HD = getAddonSetting('prefer_hd', BOOL)
OPT_MDELAY = getAddonSetting('mdelay', NUM, 60)
OPT_PVR_ONLY = getAddonSetting('pvronly', BOOL)
OPT_SCREENREFRESH = getAddonSetting('screenrefresh', NUM, 60)
REFRESH_RATIO = OPT_MDELAY / OPT_SCREENREFRESH
OPT_PREFERRED_SCRAPER = getAddonSetting('scraper')

LOCAL_DATE_FORMAT = getDateFormat()
LOCAL_TIME_FORMAT = getTimeFormat()

try:
    mod = __import__(OPT_PREFERRED_SCRAPER, locals(), globals(), fromlist=['Scraper'])
except ImportError:
    mod = __import__(SCRAPER_DEFAULT, locals(), globals(), fromlist=['Scraper'])
Scraper = getattr(mod, 'Scraper')

if not os.path.isfile(USER_TRANSLATIONS):
    xbmcvfs.copy(os.path.join(ADDON_PATH, 'ChannelTranslate.json'), USER_TRANSLATIONS)

writeLog('Getting PVR translations from %s' % USER_TRANSLATIONS, xbmc.LOGDEBUG)
with open(USER_TRANSLATIONS, 'r') as transfile:
    ChannelTranslate = transfile.read().rstrip('\n')

infoprops = ['Title', 'Picture', 'Subtitle', 'Description', 'Channel', 'ChannelID', 'Logo', 'Date', 'StartTime',
             'RunTime', 'EndTime', 'Genre', 'Cast', 'isRunning', 'isInFuture', 'isInDB', 'dbTitle', 'dbOriginalTitle',
             'Fanart', 'dbTrailer', 'dbRating', 'dbUserRating', 'BroadcastID', 'hasTimer', 'BlobID']

# convert HTML Entities to unicode chars

entities = {'&lt;': '<', '&gt;': '>', '&nbsp;': ' ', '&amp;': '&', '&quot;': '"'}
tags = {'<br/>': ' ', '<hr/>': ''}


def entity2unicode(text):
    for entity in entities.iterkeys():
        text = text.replace(entity, entities[entity])

    # 2nd pass to eliminate html like '<br/>'

    for tag in tags.iterkeys():
        text = text.replace(tag, tags[tag])
    return text

# get remote URL, replace '\' and optional split into css containers


def getUnicodePage(url, container=None):
    try:
        req = urllib2.urlopen(url.encode('utf-8'), timeout=30)
    except UnicodeDecodeError:
        req = urllib2.urlopen(url)
    except ValueError:
        return False
    except urllib2.URLError, e:
        writeLog(str(e.reason), xbmc.LOGERROR)
        return False
    except socket.timeout:
        writeLog('Socket timeout', xbmc.LOGERROR)
        return False
    except ssl.SSLError, e:
        writeLog(str(e), xbmc.LOGERROR)
        return False

    encoding = 'utf-8'
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
    content = unicode(req.read(), encoding).replace("\\", "")
    if container is None: return content
    return content.split(container)

# get parameter hash, convert into parameter/value pairs, return dictionary


def ParamsToDict(parameters):
    params = dict()
    if parameters:
        pairs = parameters.split("&")
        for pair in pairs:
            key_value = pair.split('=')
            if (len(key_value)) == 2:
                params.update({key_value[0]: key_value[1]})
    return params

# determine and change scraper modules

def changeScraper():
    _scrapers = []
    _scraperdict = []
    for module in os.listdir(SCRAPER_FOLDER):
        if module in (['__init__.py', 'tools.py']) or module[-3:] != '.py': continue
        writeLog('Found Scraper Module %s' % (module))
        mod = __import__('%s.%s' % (SCRAPER_MODULPATH, module[:-3]), locals(), globals(), fromlist=['Scraper'])
        ScraperClass = getattr(mod, 'Scraper')

        if not ScraperClass().enabled: continue
        _scraperdict.append({'name': ScraperClass().friendlyname,
                             'shortname': ScraperClass().shortname,
                             'baseurl': ScraperClass().baseurl,
                             'icon': ScraperClass().icon,
                             'module': '%s.%s' % (SCRAPER_MODULPATH, module[:-3])})

    _scraperdict.sort()
    for scrapers in _scraperdict:
        liz = xbmcgui.ListItem(label=scrapers['name'], label2=scrapers['baseurl'], iconImage=getScraperIcon(scrapers['icon']))
        _scrapers.append(liz)
    _idx = xbmcgui.Dialog().select(LOC(30111), _scrapers, useDetails=True)
    if _idx > -1:
        writeLog('selected scrapermodule is %s' % (_scraperdict[_idx]['module']))
        ADDON.setSetting('scraper', _scraperdict[_idx]['module'])
        ADDON.setSetting('setscraper', _scraperdict[_idx]['shortname'])
        HOME.setProperty('GTO.timestamp', str(int(time.time())))

# convert datetime string to timestamp with workaround python bug (http://bugs.python.org/issue7980) - Thanks to BJ1

def utc_to_local_datetime(utc_datetime):
    delta = utc_datetime - EPOCH
    utc_epoch = 86400 * delta.days + delta.seconds
    time_struct = time.localtime(utc_epoch)
    dt_args = time_struct[:6] + (delta.microseconds,)
    return datetime.datetime(*dt_args)

# get pvr channelname, translate from Scraper to pvr channelname if necessary

def channelName2pvrId(channelname):
    translations = json.loads(str(ChannelTranslate))
    for translation in translations:
        for names in translation['name']:
            if channelname.lower() == names.lower():
                writeLog("Translating %s to %s" % (channelname, translation['pvrname']))
                channelname = translation['pvrname']
                break

    query = {
            "method": "PVR.GetChannels",
            "params": {"channelgroupid": "alltv"},
            }
    res = jsonrpc(query)
    try:
        for channels in res.get('channels'):

            # prefer HD Channel if available

            if OPT_PREFER_HD and  (channelname + " HD").lower() == channels.get('label').lower():
                writeLog("GTO found HD priorized channel %s" % (channels.get('label')))
                return channels.get('channelid')

            if channelname.lower() == channels.get('label').lower():
                writeLog("GTO found channel %s" % (channels.get('label')))
                return channels.get('channelid')
    except AttributeError, e:
        writeLog('Could not get ID from %s: %s' % (channelname, e.message), xbmc.LOGERROR)
    return False

# get pvr channelname by id

def getPvrChannelName(channelid, fallback):
    query = {
            "method": "PVR.GetChannels",
            "params": {"channelgroupid": "alltv"},
            }
    res = jsonrpc(query)
    try:
        for channels in res.get('channels'):
            if channels.get('channelid') == channelid:
                writeLog("GTO found id for channel %s" % (channels.get('label')))
                return channels.get('label')
    except AttributeError, e:
        writeLog('Could not get station name: %s' % (e.message), level=xbmc.LOGERROR)
    return fallback + '*'

# get pvr channel logo url

def getStationLogo(channelid, fallback):
    query = {
            "method": "PVR.GetChannelDetails",
            "params": {"channelid": channelid, "properties": ["thumbnail"]},
            }
    res = jsonrpc(query)
    try:
        return urllib.unquote_plus(res.get('channeldetails').get('thumbnail')).split('://', 1)[1][:-1]
    except (AttributeError, IndexError,), e:
        writeLog('Could not get station logo: %s' % (e.message), level=xbmc.LOGERROR)
    return fallback

def switchToChannel(pvrid):
    '''
    :param pvrid:       str PVR-ID of the broadcast station
    :return:            none
    '''
    writeLog('Switch to channel id %s' % (pvrid))
    query = {
        "method": "Player.Open",
        "params": {"item": {"channelid": int(pvrid)}}
        }
    res = jsonrpc(query)
    if res == 'OK':
        writeLog('Successfull switched to channel id %s' % (pvrid))
    else:
        writeLog('Couldn\'t switch to channel id %s' % (pvrid))


def getBroadcast(pvrid, datetime2):
    '''
    :param pvrid:       str PVR-ID of the broadcast station
    :param datetime2:   str datetime in TIME_FORMAT e.g. '2017-07-20 20:15:00'
    :return:            dict: int unique broadcastID of the broadcast or None
    '''
    params = {'broadcastid': None}
    if not pvrid: return params
    query = {
        "method": "PVR.GetBroadcasts",
        "params": {"channelid": pvrid,
                   "properties": ["title", "starttime"]}
    }
    res = jsonrpc(query)
    if res.get('broadcasts', False):
        try:
            for broadcast in res.get('broadcasts'):
                _ltt = utc_to_local_datetime(parser.parse(broadcast['starttime'])).strftime(LOCAL_DATE_FORMAT)
                if _ltt == datetime2:
                    params.update({'broadcastid': broadcast['broadcastid']})
                    writeLog('Broadcast #%s of ChannelID #%s found' % (broadcast['broadcastid'], pvrid))
                    break
        except (TypeError, AttributeError,), e:
            writeLog('Could not determine broadcast of ChannelID %s: %s' % (pvrid, e.message), xbmc.LOGERROR)
    return params


def hasTimer(pvrid, broadcastid):
    '''
    :param pvrid:       str PVR-ID of the broadcast station
    :param broadcastid: str Broadcast-ID (or epguid)
    :return:            dict: bool hastimer of the broadcast or False
    '''
    params = {'hastimer': False}
    if not pvrid or not broadcastid: return params

    query = {
        "method": "PVR.getTimers",
        "params": {"properties": ["title", "channelid", "epguid"]}
    }
    res = jsonrpc(query)
    if res.get('timers', False):
        try:
            for timer in res.get('timers'):
                if timer['channelid'] == pvrid and timer['epguid'] == broadcastid:
                    params.update({'hastimer': True})
                    writeLog('Timer active for broadcast #%s (%s) on pvrID #%s' % (timer['epguid'], timer['title'], timer['channelid']))
                    break
        except (TypeError, AttributeError,), e:
            writeLog('Error while executing JSON request PVR.GetTimers: %s' %  (e.message), xbmc.LOGERROR)
    return params


def setTimer(broadcastId, blobId):
    '''
    :param broadcastId: str unique broadcastID of the broadcast
    :return:            none
    '''
    query = {
        "method": "PVR.AddTimer",
        "params": {"broadcastid": int(broadcastId)}
    }
    res = jsonrpc(query)
    if res == 'OK':
        HOME.setProperty('GTO.timestamp', str(int(time.time())))
        xbmc.executebuiltin('Container.Refresh')
        writeLog('Timer of blob #%s added' % (blobId))
    else:
        writeLog('Timer couldn\'t set', xbmc.LOGERROR)


def isInVideoDB(title):
    '''
    search for a title if already present in database, search with different fuzzy parameters in 4 steps:
    1. match exact
    2. match contains
    3. replace all occurences of ' - ' with ': ' (planet of the apes - revolution -> planet of the apes: revolution), match contains
    4. split title on ':' and '-', search first part (planet of the apes), match contains

    :param title:       str title of broadcast e.g. 'Planet of the apes - Revolution'
    :return:            dictionary {'isInDB': 'no'} or {'isInDB': 'yes', 'title: 'originaltitle': 'fanart': 'trailer': 'rating': 'userrating':}
    '''
    writeLog('Check if \'%s\' is in database' % (title))

    titlepart = re.findall('[:-]', title)
    params = {'isInDB': False}
    query = {"method": "VideoLibrary.GetMovies"}
    rpcQuery = [{"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "is", "value": title}}},
                {"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "contains", "value": title}}},
                {"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "contains", "value": title.replace(' - ', ': ')}}}]
    if len(titlepart) > 0:
        rpcQuery.append({"params": {"properties": ["title", "originaltitle", "fanart", "trailer", "rating", "userrating"],
                       "sort": {"method": "label"},
                       "filter": {"field": "title", "operator": "contains", "value": title.split(titlepart[0])[0].strip()}}})

    for i in range(0, len(rpcQuery) + 1):
        if i == 0:
            writeLog('Try exact matching of search pattern')
        elif i == 1:
            writeLog('No movie(s) with exact pattern found, try fuzzy filters')
            if len(title.split()) < 3:
                writeLog('Word count to small for fuzzy filters')
                return params
        elif i == 2:
            writeLog('No movie(s) with similar pattern found, replacing special chars')
        elif i == 3:
            writeLog('Split title into titleparts')
            if len(titlepart) == 0:
                writeLog('Sorry, splitting isn\'t possible')
                return params
            writeLog('Search for \'%s\'' % (title.split(titlepart[0])[0].strip()))
        else:
            writeLog('Sorry, no matches')
            return params

        query.update(rpcQuery[i])
        res = jsonrpc(query)
        if 'movies' in res: break

    writeLog('Found %s matches for movie(s) in database, select first' % (len(res['movies'])))

    try:
        _fanart = urllib.unquote_plus(res['movies'][0]['fanart']).split('://', 1)[1][:-1]
    except IndexError:
        writeLog('Fanart: %s' % (urllib.unquote_plus(res['movies'][0]['fanart'])))
        _fanart = ''

    _userrating = '0'
    if res['movies'][0]['userrating'] != '': _userrating = res['movies'][0]['userrating']
    params.update({'isInDB': True,
                   'db_title': unicode(res['movies'][0]['title']),
                   'db_originaltitle': unicode(res['movies'][0]['originaltitle']),
                   'db_fanart': unicode(_fanart),
                   'db_trailer': unicode(res['movies'][0]['trailer']),
                   'db_rating': round(float(res['movies'][0]['rating']), 1),
                   'db_userrating': int(_userrating)})
    return params

# clear all info properties (info window) in Home Window

def clearInfoProperties():
    writeLog('clear all info properties (used in info popup)')
    for property in infoprops:
        HOME.clearProperty('GTO.Info.%s' % (property))

def refreshWidget(handle=None, notify=OPT_ENABLE_INFO):

    isbusy = waitForScraper()

    blobs = int(HOME.getProperty('GTO.blobs') or '0')
    if blobs == 0 or isbusy:
        writeLog('Scraper is busy or returns no data, aborting', xbmc.LOGERROR)
        notifyOSD(LOC(30010), LOC(30132), enabled=True)
        return

    notifyOSD(LOC(30010), LOC(30109) % ((Scraper().shortname).decode('utf-8')), icon=getScraperIcon(Scraper().icon), enabled=notify)

    widget = 1
    for i in range(1, blobs + 1, 1):

        writeLog('Processing blob GTO.%s for item #%s' % (i, widget))
        try:
            blob = eval(HOME.getProperty('GTO.%s' % (i)))
        except SyntaxError:
            writeLog('Could not read blob #%s properly' % (i))
            continue

        if OPT_PVR_ONLY and hasPVR(timeout=10) and not blob['pvrid']:
            writeLog("Channel %s isn't in PVR or PVR not ready, discard entry" % (blob['channel']))
            continue

        if time.mktime(parser.parse(blob['enddate'], dayfirst=True).timetuple()) < time.time():
            writeLog('Discard blob, outdated')
            continue

        wid = xbmcgui.ListItem(label=blob['title'], label2=blob['pvrchannel'])
        wid.setInfo('video', {'title': blob['title'], 'genre': blob['genre'], 'plot': blob['plot'],
                              'cast': blob['cast'].split(','), 'duration': int(blob['runtime'])*60})
        wid.setArt({'thumb': blob['thumb'], 'logo': blob['logo']})

        if handle is None:

            # check for broadcasts and timers

            writeLog('')

            blob.update(getBroadcast(blob['pvrid'], blob['datetime']))
            blob.update(hasTimer(blob['pvrid'], blob['broadcastid']))

            writeLog('Broadcast ID:    %s' % (blob['broadcastid']))
            writeLog('has Timer:       %s' % (blob['hastimer']))

            wid.setProperty('hasTimer', str(blob['hastimer']))

            # check for titles in videoDB

            blob.update(isInVideoDB(blob['title']))

            writeLog('is in Database:  %s' % (blob['isInDB']))
            if blob['isInDB']:
                writeLog('   Title:        %s' % blob['db_title'])
                writeLog('   orig. Title:  %s' % blob['db_originaltitle'])
                writeLog('   Fanart:       %s' % blob['db_fanart'])
                writeLog('   Trailer:      %s' % blob['db_trailer'])
                writeLog('   Rating:       %s' % blob['db_rating'])
                writeLog('   User rating:  %s' % blob['db_userrating'])

                wid.setProperty('dbTitle', blob['db_title'])
                wid.setInfo('video', {'originaltitle': blob['db_originaltitle'],
                                      'trailer': blob['db_trailer'], 'rating': blob['db_rating'],
                                      'userrating': blob['db_userrating']})
                wid.setArt({'fanart': blob['db_fanart']})

            writeLog('')
            HOME.setProperty('GTO.%s' % (i), str(blob))

        wid.setProperty('DateTime', blob['datetime'])
        wid.setProperty('StartTime', datetime.datetime.strftime(parser.parse(blob['datetime']), getTimeFormat()))
        wid.setProperty('EndTime', datetime.datetime.strftime(parser.parse(blob['enddate']), getTimeFormat()))
        wid.setProperty('RunTime', str(blob['runtime']))
        wid.setProperty('ChannelID', str(blob['pvrid']))
        wid.setProperty('BlobID', str(i))

        if handle is not None: xbmcplugin.addDirectoryItem(handle=handle, url='', listitem=wid)
        widget += 1

    if handle is not None:
        xbmcplugin.endOfDirectory(handle=handle, updateListing=True)
        writeLog('Widget with handle #%s filled' % (handle))
    else:
        HOME.setProperty('GTO.timestamp', str(int(time.time())))
        xbmc.executebuiltin('Container.Refresh')
        writeLog('Finished, initiate container refresh')


def scrapeGTOPage(enabled=OPT_ENABLE_INFO):

    HOME.setProperty('GTO.provider', LOC(30105))
    HOME.setProperty('GTO.busy', 'true')
    data = Scraper()
    data.err404 = os.path.join(ADDON_PATH, 'resources', 'lib', 'media', data.err404)

    notifyOSD(LOC(30010), LOC(30018) % ((data.shortname).decode('utf-8')), icon=getScraperIcon(data.icon), enabled=enabled)
    writeLog('Start scraping from %s' % (data.rssurl))

    content = getUnicodePage(data.rssurl, container=data.selector)
    if not content: return

    blobs = int(HOME.getProperty('GTO.blobs') or '0') + 1
    for idx in range(1, blobs, 1):
        HOME.clearProperty('GTO.%s' % (idx))

    idx = 1
    content.pop(0)

    if hasattr(data, 'subselector'):
        content = content[0].split(data.subselector)
        content.pop(0)

    HOME.setProperty('GTO.blobs', '0')

    for container in content:

        data.scrapeRSS(container)

        pvrid = channelName2pvrId(data.channel)
        logoURL = getStationLogo(pvrid, data.err404)
        channel = getPvrChannelName(pvrid, data.channel)
        details = getUnicodePage(data.detailURL)

        if hasattr(data, 'scrapeDetailPage') and callable(getattr(data, 'scrapeDetailPage')) and details:
            writeLog('Scraping details from %s' % (data.detailURL))
            data.scrapeDetailPage(details, data.detailselector)

        if not isinstance(data.enddate, datetime.datetime):
            writeLog('No endtime available, discard blob')
            continue

        blob = {
                'title': unicode(entity2unicode(data.title)),
                'thumb': unicode(data.thumb),
                'datetime': datetime.datetime.strftime(data.startdate, LOCAL_DATE_FORMAT),
                'runtime': data.runtime,
                'enddate': datetime.datetime.strftime(data.enddate, LOCAL_DATE_FORMAT),
                'channel': unicode(data.channel),
                'pvrchannel': unicode(channel),
                'pvrid': pvrid,
                'logo': unicode(logoURL),
                'genre': unicode(entity2unicode(data.genre)),
                'plot': unicode(entity2unicode(data.plot)),
                'cast': unicode(entity2unicode(data.cast)),
                'rating': data.rating
               }

        writeLog('')
        writeLog('blob:            #%s' % (idx))
        writeLog('Title:           %s' % (blob['title']))
        writeLog('Thumb:           %s' % (blob['thumb']))
        writeLog('Date & time:     %s' % (blob['datetime']))
        writeLog('End date:        %s' % (blob['enddate']))
        writeLog('Running time:    %s' % (blob['runtime']))
        writeLog('Channel (GTO):   %s' % (blob['channel']))
        writeLog('Channel (PVR):   %s' % (blob['pvrchannel']))
        writeLog('ChannelID (PVR): %s' % (blob['pvrid']))
        writeLog('Channel logo:    %s' % (blob['logo']))
        writeLog('Genre:           %s' % (blob['genre']))
        writeLog('Plot:            %s...' % (blob['plot'][0:40]))
        writeLog('Cast:            %s' % (blob['cast']))
        writeLog('Rating:          %s' % (blob['rating']))
        writeLog('')

        HOME.setProperty('GTO.%s' % (idx), str(blob))
        idx += 1

    HOME.setProperty('GTO.provider', data.shortname)
    HOME.setProperty('GTO.blobs', str(idx - 1))
    HOME.setProperty('GTO.busy', 'false')
    writeLog('%s items scraped and written to blobs' % (idx - 1))
    if (idx - 1) == 0:
        writeLog('Scraper returns no data', xbmc.LOGERROR)
        notifyOSD(LOC(30010), LOC(30132), icon=getScraperIcon(Scraper().icon), enabled=True)

# Set details to Window (INFO Labels)

def showInfoWindow(blobId, showWindow=True):
    writeLog('Collect and set details to home/info screen for blob #%s' % (blobId or '<unknown>'))

    if blobId is '' or None:
        writeLog('No ID provided', level=xbmc.LOGFATAL)
        return False

    blob = eval(HOME.getProperty('GTO.%s' % (blobId)))

    blob.update(getBroadcast(blob['pvrid'], blob['datetime']))
    blob.update(hasTimer(blob['pvrid'], blob['broadcastid']))

    clearInfoProperties()

    if blob['pvrid']:
        if blob['broadcastid']:
            writeLog('PVR recording possible (BroadcastID %s)' % (blob['broadcastid']))
            HOME.setProperty("GTO.Info.BroadcastID", str(blob['broadcastid']))
            HOME.setProperty("GTO.Info.hasTimer", str(blob['hastimer']))

        _now = datetime.datetime.now()
        _start = parser.parse(blob['datetime'])
        _end = parser.parse(blob['enddate'])

        if _start >= _now:
            writeLog('Start time of title \'%s\' is @%s, enable switchtimer button' % (blob['title'], blob['datetime']))
            HOME.setProperty("GTO.Info.isInFuture", "True")
        elif _start < _now < _end:
            writeLog('Title \'%s\' is currently running, enable switch button' % (blob['title']))
            HOME.setProperty("GTO.Info.isRunning", "True")

    HOME.setProperty("GTO.Info.BlobID", str(blobId))
    HOME.setProperty("GTO.Info.Title", blob['title'])
    HOME.setProperty("GTO.Info.Picture", blob['thumb'])
    HOME.setProperty("GTO.Info.Description", blob['plot'] or LOC(30140))
    HOME.setProperty("GTO.Info.Channel", blob['pvrchannel'])
    HOME.setProperty("GTO.Info.ChannelID", str(blob['pvrid']))
    HOME.setProperty("GTO.Info.Logo", blob['logo'])
    HOME.setProperty("GTO.Info.Date", blob['datetime'])
    HOME.setProperty("GTO.Info.RunTime", blob['runtime'])
    HOME.setProperty("GTO.Info.EndTime", datetime.datetime.strftime(parser.parse(blob['enddate']), LOCAL_TIME_FORMAT))
    if blob['rating'] is None or blob['rating'] == '':
        HOME.setProperty("GTO.Info.Genre", blob['genre'])
    else:
        HOME.setProperty('GTO.Info.Genre', blob['genre'] + ' | IMDb: ' + blob['rating'])
    HOME.setProperty("GTO.Info.Cast", blob['cast'])
    HOME.setProperty("GTO.Info.Rating", blob['rating']),
    HOME.setProperty("GTO.Info.isInDB", str(blob['isInDB']))
    if blob['isInDB']:
        HOME.setProperty("GTO.Info.dbTitle", blob['db_title'])
        HOME.setProperty("GTO.Info.dbOriginalTitle", blob['db_originaltitle'])
        HOME.setProperty("GTO.Info.Fanart", blob['db_fanart'])
        HOME.setProperty("GTO.Info.dbTrailer", blob['db_trailer'])
        HOME.setProperty("GTO.Info.dbRating", str(blob['db_rating']))
        HOME.setProperty("GTO.Info.dbUserRating", str(blob['db_userrating']))

    if showWindow:
        Popup = xbmcgui.WindowXMLDialog(INFO_XML, ADDON_PATH)
        Popup.doModal()
        del Popup

    HOME.setProperty('GTO.%s' % (blobId), str(blob))

# _______________________________
#
#           M A I N
# _______________________________

action = None
blob = None
pvrid = None
broadcastid = None

arguments = sys.argv

if len(arguments) > 1:

    if arguments[0][0:6] == 'plugin':
        writeLog('calling script as plugin source')
        _addonHandle = int(arguments[1])
        arguments.pop(0)
        arguments[1] = arguments[1][1:]

    params = ParamsToDict(arguments[1])
    action = urllib.unquote_plus(params.get('action', ''))
    blob = urllib.unquote_plus(params.get('blob', ''))
    pvrid = urllib.unquote_plus(params.get('pvrid', ''))
    broadcastid = urllib.unquote_plus(params.get('broadcastid', ''))

    writeLog('provided parameter hash: %s' % (arguments[1]))
    monitor = xbmc.Monitor()

    if action == 'scrape':
        scrapeGTOPage()
        if not waitForScraper(timeout=180): refreshWidget()

    elif action == 'getcontent':
        refreshWidget(handle=_addonHandle, notify=False)

    elif action == 'refresh':
        refreshWidget()

    elif action == 'infopopup':
        showInfoWindow(blob)

    elif action == 'sethomecontent':
        showInfoWindow(blob, showWindow=False)

    elif action == 'switch_channel':
        switchToChannel(pvrid)

    elif action == 'change_scraper':
        changeScraper()

    elif action == 'record':
        setTimer(broadcastid, blob)
