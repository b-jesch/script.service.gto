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
OPT_PREFER_HD = getAddonSetting('prefer_hd', BOOL)
OPT_MDELAY = getAddonSetting('mdelay', NUM, 60)
OPT_PVR_ONLY = getAddonSetting('pvronly', BOOL)
OPT_SCREENREFRESH = getAddonSetting('screenrefresh', NUM, 60)
REFRESH_RATIO = OPT_MDELAY / OPT_SCREENREFRESH
OPT_PREFERRED_SCRAPER = getAddonSetting('scraper')

def loadSettings():

    global OPT_PREFER_HD
    global OPT_ENABLE_INFO
    global OPT_PVR_ONLY
    global OPT_PREFERRED_SCRAPER
    global OPT_SCREENREFRESH
    global OPT_MDELAY
    global REFRESH_RATIO

    OPT_ENABLE_INFO = getAddonSetting('enableinfo', BOOL)
    OPT_PREFER_HD = getAddonSetting('prefer_hd', BOOL)
    OPT_PVR_ONLY = getAddonSetting('pvronly', BOOL)
    OPT_PREFERRED_SCRAPER = getAddonSetting('scraper')
    OPT_MDELAY = getAddonSetting('mdelay', NUM, 60)
    OPT_SCREENREFRESH = getAddonSetting('screenrefresh', NUM, 60)
    REFRESH_RATIO = OPT_MDELAY / OPT_SCREENREFRESH

    writeLog('Settings (re)loaded')
    writeLog('preferred scraper module: %s' % (OPT_PREFERRED_SCRAPER))
    writeLog('Show notifications:       %s' % (OPT_ENABLE_INFO))
    writeLog('Prefer HD channels:       %s' % (OPT_PREFER_HD))
    writeLog('Prefer PVR channels only: %s' % (OPT_PVR_ONLY))
    writeLog('Refresh interval content: %s secs' % (OPT_MDELAY))
    writeLog('Refresh interval widget:  %s secs' % (OPT_SCREENREFRESH))
    writeLog('Refreshing ratio:         %s' % (REFRESH_RATIO))

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

LOCAL_DATE_FORMAT = getDateFormat()
LOCAL_TIME_FORMAT = getTimeFormat()

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
    except (urllib2.HTTPError, urllib2.URLError), e:
        writeLog('Ressource %s not available: %s' % (resource, e.message), xbmc.LOGERROR)
        if e.code == '404': writeLog('Access forbidden: %s' % (e.code), xbmc.LOGERROR)
        return fallback
    return resource


# End Helpers
