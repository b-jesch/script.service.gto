#!/usr/bin/python

from resources.lib.tools import *


__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__path__ = __addon__.getAddonInfo('path')
__LS__ = __addon__.getLocalizedString
__icon__ = xbmc.translatePath(os.path.join(__path__, 'icon.png'))

HOME = xbmcgui.Window(10000)
DELAY = 15                      # wait for PVR content
CYCLE = 60                      # poll cycle
OSD = xbmcgui.Dialog()

OPT_SCREENREFRESH = 0
REFRESH_RATIO = 0

def getSettings():
    global OPT_SCREENREFRESH
    global REFRESH_RATIO

    OPT_ENABLE_INFO = getAddonSetting('enableinfo', BOOL)
    OPT_PREFER_HD = getAddonSetting('prefer_hd', BOOL)
    OPT_MDELAY = getAddonSetting('mdelay', NUM, 60)
    OPT_SCREENREFRESH = getAddonSetting('screenrefresh', NUM, 60)
    REFRESH_RATIO = OPT_MDELAY / OPT_SCREENREFRESH
    OPT_PREFERRED_SCRAPER = getAddonSetting('scraper')

    writeLog('Settings (re)loaded')
    writeLog('preferred scraper module: %s' % (OPT_PREFERRED_SCRAPER))
    writeLog('Show notifications:       %s' % (OPT_ENABLE_INFO))
    writeLog('Prefer HD channel:        %s' % (OPT_PREFER_HD))
    writeLog('Refresh interval content: %s secs' % (OPT_MDELAY))
    writeLog('Refresh interval widget:  %s secs' % (OPT_SCREENREFRESH))
    writeLog('Refreshing ratio:         %s' % (REFRESH_RATIO))

    xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=scrape)')


class MyMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs ):
        xbmc.Monitor.__init__(self)
        self.settingsChanged = False

    def onSettingsChanged(self):
        self.settingsChanged = True
        getSettings()
        # xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=scrape)')


class Starter():

    def __init__(self):
        pass

    def start(self):
        writeLog('Starting %s V.%s' % (ADDON_NAME, ADDON_VERSION), level=xbmc.LOGNOTICE)
        getSettings()

        HOME.setProperty('PVRisReady', 'no')

        _c = 0
        _attempts = 4

        monitor = MyMonitor()

        while not monitor.abortRequested():

            if monitor.settingsChanged:
                _c = 0
                _attempts = 4
                monitor.settingsChanged = False

            while HOME.getProperty('PVRisReady') == 'no' and _attempts > 0:
                if monitor.waitForAbort(DELAY): return
                if HOME.getProperty('PVRisReady') == 'yes': break
                xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=refresh)')
                _attempts -= 1

            writeLog('Next action %s seconds remaining' % (OPT_SCREENREFRESH))
            if monitor.waitForAbort(OPT_SCREENREFRESH): break
            _c += 1

            if _c >= REFRESH_RATIO:
                writeLog('Scraping feeds')
                xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=scrape)')
                _c = 0

            writeLog('Refresh content')
            xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=refresh)')

if __name__ == '__main__':
    starter = Starter()
    starter.start()
    HOME.setProperty('GTO.blobs', '0')
    HOME.clearProperty('GTO.timestamp')
    del starter
