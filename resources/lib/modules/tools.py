import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import datetime
from dateutil import parser
import json
import os
import re
import requests
import time
from urllib.parse import unquote_plus
import html

# Constants

STRING = 0
BOOL = 1
NUM = 2

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
ADDON_PROFILES = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
LOC = ADDON.getLocalizedString

HOME = xbmcgui.Window(10000)
OSD = xbmcgui.Dialog()

EPOCH = datetime.datetime(1970, 1, 1)
RSS_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
RSS_TIME_FORMAT_WOS = '%Y-%m-%d %H:%M'

SCRAPER_FOLDER = os.path.join(ADDON_PATH, 'resources', 'lib', 'modules', 'scraper')
SCRAPER_MODULPATH = 'resources.lib.modules.scraper'
SCRAPER_DEFAULT = '%s.%s' % (SCRAPER_MODULPATH, 'klack_de')
SCRAPER_CONTENT = os.path.join(ADDON_PROFILES, 'content.json')
INFO_XML = xbmcvfs.translatePath('special://skin').split(os.sep)[-2] + '.script-gto-info.xml'
USER_TRANSLATIONS = os.path.join(ADDON_PROFILES, 'translations.json')
FANART = os.path.join(ADDON_PATH, 'fanart.jpg')

monitor = xbmc.Monitor()


def strToBool(par):
    return True if par.upper() == 'TRUE' else False


def getAddonSetting(setting, sType=STRING, multiplicator=1):
    if sType == BOOL:
        return strToBool(ADDON.getSetting(setting))
    elif sType == NUM:
        try:
            return int(re.match('\d+', LOC(int(ADDON.getSetting(setting)))).group()) * multiplicator
        except AttributeError:
            writeLog('Couldn\'t read NUM setting: %s' % setting)
            return 0
    else:
        return ADDON.getSetting(setting)


OPT_PREFER_HD = getAddonSetting('prefer_hd', BOOL)
OPT_ENABLE_INFO = getAddonSetting('enableinfo', BOOL)
OPT_PVR_ONLY = getAddonSetting('pvronly', BOOL)

# get used dateformat of kodi


def getDateFormat():
    df = xbmc.getRegion('dateshort')
    return '%s %s' % (df, getTimeFormat())


def getTimeFormat():
    tf = xbmc.getRegion('time').split(':')
    try:
        return '%s:%s %s' % (tf[0][0:2], tf[1], tf[2].split()[1])    # time format is 12h with am/pm
    except IndexError:
        return '%s:%s' % (tf[0][0:2], tf[1])                         # time format is 24h with or w/o leading zero


LOCAL_DATE_FORMAT = getDateFormat()
LOCAL_TIME_FORMAT = getTimeFormat()

# Helpers
# convert HTML Entities to chars

tags = {'<br/>': '\n', '<hr/>': ''}


def entity2char(text):
    unescaped = html.unescape(text)

    # 2nd pass to eliminate html like '<br/>'

    for tag in tags.keys():
        text = unescaped.replace(tag, tags[tag])
    return text


def getScraperIcon(icon):
    return os.path.join(ADDON_PATH, 'resources', 'lib', 'media', icon)


def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO, disp=4000, enabled=OPT_ENABLE_INFO):
    if enabled:
        OSD.notification(header, message, icon, disp)


def writeLog(message, level=xbmc.LOGDEBUG):
        try:
            xbmc.log('[%s %s]: %s' % (ADDON_ID, ADDON_VERSION,  message), level)
        except Exception:
            xbmc.log('[%s %s]: %s' % (ADDON_ID, ADDON_VERSION,  'Fatal: Message couldn\'t displayed'), xbmc.LOGERROR)


def utc_to_local_datetime(utc_datetime):
    delta = utc_datetime - EPOCH
    utc_epoch = 86400 * delta.days + delta.seconds
    time_struct = time.localtime(utc_epoch)
    dt_args = time_struct[:6] + (delta.microseconds,)
    return datetime.datetime(*dt_args)


def convert_dateformat(datestring, dt_in=RSS_TIME_FORMAT, dt_out=LOCAL_DATE_FORMAT):
    dt = time.strptime(datestring, dt_in)
    return time.strftime(dt_out, dt)


def jsonrpc(query):
    querystring = {"jsonrpc": "2.0", "id": 1}
    querystring.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(querystring)))
        if 'result' in response: return response['result']
    except TypeError as e:
        writeLog('Error executing JSON RPC: {}'.format(e.args), xbmc.LOGFATAL)
    return None

# Scraper helpers


def get_feed(resource, container=None):
    try:
        req = requests.get(resource)
        req.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        writeLog('Response from {}: {}'.format(resource, e.response), xbmc.LOGERROR)
        return None

    if container is None:
        return req.text
    else:
        content = req.text.split(container)
        content.pop(0)
        return content


def checkResource(resource, fallback):
    if not resource: return fallback
    try:
        req = requests.get(resource, timeout=5)
        req.raise_for_status()
    except requests.HTTPError as e:
        writeLog('Resource {} not available: {}'.format(resource, e.args), xbmc.LOGERROR)
        return fallback
    return resource

# PVR helpers

# get pvr channelname, translate from Scraper to pvr channelname if necessary


def channelName2pvrId(channelname):
    with open(USER_TRANSLATIONS, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    for translation in translations:
        for names in translation['name']:
            if channelname.lower() == names.lower():
                writeLog("Translating {} to {}".format(channelname, translation['pvrname']))
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

            if channelname.lower() == channels.get('label').lower():
                writeLog("GTO found channel {}".format(channels.get('label')))
                return channels.get('channelid')

            if OPT_PREFER_HD and (channelname + " HD").lower() == channels.get('label').lower():
                writeLog("GTO found HD priorized channel {}".format(channels.get('label')))
                return channels.get('channelid')

    except AttributeError:
        writeLog('Could not get ID from {}'.format(channelname), xbmc.LOGERROR)
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
                writeLog("found id for channel {}".format(channels.get('label')))
                return channels.get('label')
    except AttributeError as e:
        writeLog('Could not get channel: {}'.format(e.args), level=xbmc.LOGERROR)
    return fallback + '*'

# get pvr channel logo url

def getStationLogo(channelid, fallback):
    query = {
            "method": "PVR.GetChannelDetails",
            "params": {"channelid": channelid, "properties": ["thumbnail"]},
            }
    res = jsonrpc(query)
    try:
        return unquote_plus(res.get('channeldetails').get('thumbnail', fallback))
    except AttributeError:
        return fallback


def switchToChannel(pvrid, item):
    """
    :param pvrid:       str PVR-ID of the broadcast station
    :return:            none
    """
    query = {
        "method": "Player.Open",
        "params": {"item": {"channelid": int(pvrid)}}
        }
    res = jsonrpc(query)
    if res == 'OK':
        writeLog('Switch to channel id {} of item #{}'.format(pvrid, item))
    else:
        writeLog('Couldn\'t switch to channel id {}'.format(pvrid))


def getBroadcast(pvrid, datetime2):
    """
    :param pvrid:       str PVR-ID of the broadcast station
    :param datetime2:   str datetime in TIME_FORMAT e.g. '2017-07-20 20:15:00'
    :return:            dict: int unique broadcastID of the broadcast or None
    """
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
                _ltt = utc_to_local_datetime(parser.parse(broadcast['starttime'])).strftime(RSS_TIME_FORMAT_WOS)
                if _ltt == datetime2:
                    params.update({'broadcastid': broadcast['broadcastid']})
                    writeLog('Broadcast #{} of ChannelID #{} found'.format(broadcast['broadcastid'], pvrid))
                    break
        except (TypeError, AttributeError, KeyError):
            writeLog('Couldn\'t determine broadcast of ChannelID #{}'.format(pvrid), xbmc.LOGERROR)
    return params


def hasTimer(broadcastid):
    """
    :param broadcastid: str Broadcast-ID (or epguid)
    :return:            bool hastimer of the broadcast or False
    """
    if not broadcastid: return False

    query = {
        "method": "PVR.GetTimers",
        "params": {"properties": ["broadcastid", "isreminder", "title"]}
    }
    hastimer = False
    try:
        res = jsonrpc(query)
        for timer in res.get('timers'):
            if timer['broadcastid'] == broadcastid:
                reminder = "reminder" if timer['isreminder'] else "timer"
                writeLog('active {} for broadcast #{} ({})'.format(reminder,
                                                                   timer['broadcastid'],
                                                                   timer['title']))
                hastimer = True
    except (TypeError, AttributeError,) as e:
        writeLog('Error while executing JSON request PVR.GetTimers: {}'.format(e.args), xbmc.LOGERROR)
    return hastimer


def setTimer(broadcastId, item, reminder=False):
    """
    :param broadcastId: str unique broadcastID of the broadcast
    :return:            bool (true on success, else false)
    """
    query = {
        "method": "PVR.AddTimer",
        "params": {"broadcastid": int(broadcastId), "reminder": reminder, "timerrule": False}
    }
    res = jsonrpc(query)
    if res == 'OK':
        writeLog('Timer/reminder of item #{} added'.format(item))
        return True
    else:
        writeLog('Timer/reminder for broadcast #{} couldn\'t set'.format(broadcastId), xbmc.LOGERROR)
        return False


def hasPVR(timeout=30):
    _attempts = timeout / 5
    pvr = False
    while not pvr and _attempts > 0:
        query = {'method': 'PVR.GetProperties',
                 'params': {'properties': ['available']}}
        response = jsonrpc(query)
        pvr = True if (response is not None and response.get('available', False)) else False
        if pvr or monitor.waitForAbort(5): break
        _attempts -= 1
    return pvr


def waitForScraper(timeout=60):
    isBusy = True
    attempts = timeout / 5
    while attempts > 0:
        if monitor.waitForAbort(5):
            writeLog('Abort requested')
            break
        isBusy = strToBool(HOME.getProperty('GTO.busy'))
        if not isBusy: break
        writeLog('Scraper is busy...')
        attempts -= 1
    return isBusy
