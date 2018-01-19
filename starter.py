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

class MyMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs ):
        xbmc.Monitor.__init__(self)
        self.settingsChanged = False


    def onSettingsChanged(self):
        self.settingsChanged = True


class Starter():

    def __init__(self):
        pass

    def loadSettings(self):
        self.OPT_MDELAY = getAddonSetting('mdelay', NUM, 60)
        self.OPT_SCREENREFRESH = getAddonSetting('screenrefresh', NUM, 60)
        self.REFRESH_RATIO = self.OPT_MDELAY / self.OPT_SCREENREFRESH
        xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=scrape)')


    def start(self):
        writeLog('Starting %s V.%s' % (ADDON_NAME, ADDON_VERSION), level=xbmc.LOGNOTICE)
        self.loadSettings()
        xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=refresh)')

        _c = 0

        monitor = MyMonitor()

        while not monitor.abortRequested():

            if monitor.settingsChanged:
                _c = 0
                self.loadSettings()
                monitor.settingsChanged = False

            writeLog('Next action %s seconds remaining' % (self.OPT_SCREENREFRESH or 120))
            if monitor.waitForAbort(self.OPT_SCREENREFRESH or 120): break
            _c += 1

            if _c >= self.REFRESH_RATIO:
                writeLog('Service initiates scraping of content provider')
                xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=scrape)')
                _c = 0

            writeLog('Service initiates refreshing of content')
            xbmc.executebuiltin('XBMC.RunScript(script.service.gto,action=refresh)')

if __name__ == '__main__':
    starter = Starter()
    starter.start()
    HOME.setProperty('GTO.blobs', '0')
    HOME.clearProperty('GTO.timestamp')
    del starter
