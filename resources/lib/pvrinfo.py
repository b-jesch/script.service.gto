import xbmc
import xbmcgui


class InfoWin(xbmcgui.WindowXML):
    def __init__(self, xmlFilename: str, scriptPath: str):
        super().__init__(xmlFilename, scriptPath)

    def onInit(self):
        # xbmc.executebuiltin('Container.SetViewMode(50)')
        # self.clearList()
        li = xbmcgui.ListItem('Titel der Sendung', '31.12.2020 - 20:15')
        li.setInfo('pvr', {'plot': 'Plot of broadcast', 'ChannelName': 'BBC', 'genre': 'Crime', 'rating': '5'})

        self.dialog = xbmcgui.Dialog()
        self.dialog.info(li)

    def display(self):
        self.doModal()
