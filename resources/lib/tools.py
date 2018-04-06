import xbmc
import xbmcaddon
import xbmcgui
import datetime
import json
import os
import re
import urllib2

# Constants

STRING = 0
BOOL = 1
NUM = 2

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PROFILES = ADDON.getAddonInfo('profile')
LOC = ADDON.getLocalizedString

HOME = xbmcgui.Window(10000)
OSD = xbmcgui.Dialog()

EPOCH = datetime.datetime(1970, 1, 1)
RSS_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

SCRAPER_MODULPATH = 'resources.lib'
SCRAPER_FOLDER = os.path.join(ADDON_PATH, 'resources', 'lib')
SCRAPER_DEFAULT = '%s.%s' % (SCRAPER_MODULPATH, 'klack_de')

INFO_XML = xbmc.translatePath('special://skin').split(os.sep)[-2] + '.script-gto-info.xml'
USER_TRANSLATIONS = xbmc.translatePath(os.path.join(ADDON_PROFILES, 'ChannelTranslate.json'))


def strToBool(par):
    return True if par.upper() == 'TRUE' else False


def getAddonSetting(setting, sType=STRING, multiplicator=1):
    if sType == BOOL:
        return strToBool(ADDON.getSetting(setting))
    elif sType == NUM:
        try:
            return int(re.match('\d+', ADDON.getSetting(setting)).group()) * multiplicator
        except AttributeError:
            writeLog('Could not read setting type NUM: %s' %(setting))
            return 0
    else:
        return ADDON.getSetting(setting)

OPT_ENABLE_INFO = getAddonSetting('enableinfo', BOOL)

# Helpers

def getScraperIcon(icon):
    return os.path.join(ADDON_PATH, 'resources', 'lib', 'media', icon)

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO, disp=4000, enabled=OPT_ENABLE_INFO):
    if enabled:
        OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon, disp)

def writeLog(message, level=xbmc.LOGDEBUG):
        try:
            xbmc.log('[%s %s]: %s' % (ADDON_ID, ADDON_VERSION,  message.encode('utf-8')), level)
        except Exception:
            xbmc.log('[%s %s]: %s' % (ADDON_ID, ADDON_VERSION,  'Fatal: Message could not displayed'), xbmc.LOGERROR)


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

def jsonrpc(query):
    querystring = {"jsonrpc": "2.0", "id": 1}
    querystring.update(query)
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(querystring, encoding='utf-8')))
        if 'result' in response: return response['result']
    except TypeError, e:
        writeLog('Error executing JSON RPC: %s' % (e.message), xbmc.LOGFATAL)
    return None

# Scraper helpers


def checkResource(resource, fallback):
    if not resource: return fallback
    _req = urllib2.Request(resource)
    try:
        urllib2.urlopen(_req, timeout=5)
    except urllib2.HTTPError, e:
        writeLog('Resource %s not available: %s' % (resource, e.message), xbmc.LOGERROR)
        return fallback
    except urllib2.URLError:
        writeLog('Request failed for %s, resource possibly unavailable' % (resource), xbmc.LOGERROR)
    return resource
