#!/usr/bin/python

from resources.lib.modules.tools import *


class Starter:

    class PvrResponseTimeout(Exception):
        pass

    class Monitor(xbmc.Monitor):

        def __init__(self):
            xbmc.Monitor.__init__(self)
            self.settingsChanged = False
            self.scraper = getAddonSetting('scraper')

        def onSettingsChanged(self):
            self.settingsChanged = True
            if self.scraper != getAddonSetting('scraper'):
                xbmc.executebuiltin('RunPlugin(plugin://script.service.gto/?action=scrape&source=starter)')
                self.scraper = getAddonSetting('scraper')

    def __init__(self, scrape=True):
        self.OPT_MDELAY = getAddonSetting('mdelay', NUM, 60)
        self.OPT_SDELAY = getAddonSetting('sdelay', NUM, 1000, False)
        self.OPT_SCREENREFRESH = getAddonSetting('screenrefresh', NUM, 60)
        self.REFRESH_RATIO = self.OPT_MDELAY / self.OPT_SCREENREFRESH
        if scrape:
            writeLog('Delaying %s msecs' % self.OPT_SDELAY)
            xbmc.sleep(self.OPT_SDELAY)
            xbmc.executebuiltin('RunPlugin(plugin://script.service.gto/?action=scrape&source=init)')
            self.OPT_SDELAY = 0

    def start(self):
        writeLog('Starting %s V.%s' % (ADDON_NAME, ADDON_VERSION), level=xbmc.LOGINFO)
        HOME.setProperty('GTO.timestamp', str(int(time.time())))
        _c = 0
        gto_monitor = self.Monitor()

        if self.OPT_SDELAY > 0:
            writeLog('Delaying %s msecs' % self.OPT_SDELAY)
            xbmc.sleep(self.OPT_SDELAY)

        while not gto_monitor.abortRequested():

            try:
                if not hasPVR():
                    raise self.PvrResponseTimeout('PVR not available or responsible')
                writeLog('PVR presence checked: available')
            except self.PvrResponseTimeout as e:
                writeLog(e, xbmc.LOGERROR)

            writeLog('Next action %s seconds remaining' % self.OPT_SCREENREFRESH)
            if gto_monitor.waitForAbort(self.OPT_SCREENREFRESH):
                break

            if gto_monitor.settingsChanged:
                _c = 0
                self.__init__(scrape=False)
                gto_monitor.settingsChanged = False

            if _c >= self.REFRESH_RATIO:
                writeLog('Service initiates content scraping')
                xbmc.executebuiltin('RunPlugin(plugin://script.service.gto/?action=scrape&source=starter)')
                _c = 0

            else:
                if waitForScraper(timeout=180):
                    continue

                writeLog('Service initiates content refresh')
                xbmc.executebuiltin('RunPlugin(plugin://script.service.gto/?action=getcontent)')
                _c += 1


if __name__ == '__main__':
    starter = Starter()
    starter.start()
    HOME.clearProperty('GTO.timestamp')
    if os.path.isfile(SCRAPER_CONTENT):
        os.remove(SCRAPER_CONTENT)
    del starter
