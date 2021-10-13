from resources.lib.modules.tools import *
import sys
import os
from urllib.parse import parse_qsl, urlencode
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs

OPT_MDELAY = getAddonSetting('mdelay', NUM, 60)
OPT_ENABLE_INFO = getAddonSetting('enableinfo', BOOL)
OPT_PREFER_HD = getAddonSetting('prefer_hd', BOOL)
OPT_PREFERRED_SCRAPER = getAddonSetting('preferred')

# Prerequisites

if not os.path.isfile(USER_TRANSLATIONS):
    xbmcvfs.copy(os.path.join(ADDON_PATH, 'resources', 'ChannelTranslate.json'), USER_TRANSLATIONS)

writeLog('Getting PVR translations from %s' % USER_TRANSLATIONS, xbmc.LOGDEBUG)

window_properties = ['Title', 'Picture', 'Subtitle', 'Description', 'Channel', 'ChannelID', 'Logo', 'Date', 'StartTime',
                     'RunTime', 'EndTime', 'Genre', 'isRunning', 'isInFuture', 'BroadcastID', 'hasTimer', 'Item']

_url = sys.argv[0]
_handle = int(sys.argv[1])


class UnknownParameterException(Exception):
    pass


def get_parameters(params):
    return ','.join(urlencode(params).split('&'))


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def list_offers():
    if not os.path.isfile(SCRAPER_CONTENT):
        loop = 30
        while loop > 0:
            if xbmc.Monitor().abortRequested(): break
            xbmc.sleep(2000)
            if HOME.getProperty('GTO.busy') == 'false': break
            loop -= 1
        if loop == 0 or not os.path.isfile(SCRAPER_CONTENT):
            writeLog('No scraper data to display', xbmc.LOGERROR)
            return

    with open(SCRAPER_CONTENT, 'r', encoding='utf-8') as f:
        content = json.load(f)

    xbmcplugin.setPluginCategory(_handle, content['scraper'])
    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.setPluginFanart(_handle, FANART)
    for item in content['items']:
        if OPT_PVR_ONLY and not item.get('pvrid', False): continue
        liz = xbmcgui.ListItem()
        liz.setLabel('{} ({})'.format(item.get('pvrchannel', item.get('channel')),
                                      convert_dateformat(item.get('datetime'), dt_out=LOCAL_TIME_FORMAT)))
        liz.setLabel2('{}'.format(item.get('title')))
        liz.setInfo('video', {'genre': item.get('genre'),
                              'plot': item.get('plot'),
                              'duration': item.get('runtime'),
                              'rating': item.get('rating'),
                              'mediatype': 'video'})
        liz.setArt({'icon': item.get('thumb'), 'thumb': item.get('thumb'), 'poster': item.get('thumb'),
                    'fanart': item.get('thumb'), 'logo': item.get('logo')})
        liz.setProperty('StartTime', convert_dateformat(item.get('datetime')))
        liz.setProperty('EndTime', convert_dateformat(item.get('enddate')))
        liz.setProperty('RunTime', str(item.get('runtime') // 60))
        liz.setProperty('HasTimer', str(hasTimer(item.get('broadcastid', None))))
        liz.setProperty('Item', str(item.get('item')))
        liz.setProperty('IsPlayable', 'true')
        url = get_url(action='info', item=item.get('item'))
        xbmcplugin.addDirectoryItem(_handle, url, liz, isFolder=False)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_handle, succeeded=True, updateListing=True, cacheToDisc=False)
    HOME.setProperty('GTO.provider', content['scraper'])


def scrape_page():
    HOME.setProperty('GTO.provider', LOC(30105))
    HOME.setProperty('GTO.busy', 'true')
    scraper = Scraper()
    scraper.err404 = os.path.join(ADDON_PATH, 'resources', 'lib', 'media', scraper.err404)

    notifyOSD(LOC(30010), LOC(30018) % scraper.shortname, icon=getScraperIcon(scraper.icon))
    writeLog('Start scraping from %s' % scraper.rssurl)
    content = get_feed(scraper.rssurl, container=scraper.selector)

    if content is None:
        writeLog('Scraper returns no data', xbmc.LOGERROR)
        notifyOSD(LOC(30010), LOC(30132), icon=getScraperIcon(Scraper().icon), enabled=True)
        HOME.setProperty('GTO.busy', 'false')
        return False

    if hasattr(scraper, 'subselector'):
        content = content[0].split(scraper.subselector)
        content.pop(0)

    item_nr = 0
    items = list()
    entry = {
        'timestamp': int(time.time()),
        'scraper': scraper.friendlyname
    }

    for item in content:
        scraper.scrapeRSS(item)
        if hasattr(scraper, 'scrapeDetailPage') and \
                callable(getattr(scraper, 'scrapeDetailPage')) and scraper.detailURL:

            writeLog('Scraping details from {}'.format(scraper.detailURL))
            details = get_feed(scraper.detailURL)
            scraper.scrapeDetailPage(details, scraper.detailselector)

        if not isinstance(scraper.enddate, datetime.datetime) or scraper.enddate < datetime.datetime.now():
            writeLog('Outdated or no endtime available, discard item')
            continue

        pvrid = channelName2pvrId(scraper.channel)
        if OPT_PVR_ONLY and not pvrid: continue
        logoURL = getStationLogo(pvrid, scraper.err404).replace('image://', '')
        channel = getPvrChannelName(pvrid, scraper.channel)

        record = {
            'item': item_nr,
            'title': entity2char(scraper.title),
            'thumb': scraper.thumb,
            'datetime': datetime.datetime.strftime(scraper.startdate, RSS_TIME_FORMAT),
            'runtime': scraper.runtime,
            'enddate': datetime.datetime.strftime(scraper.enddate, RSS_TIME_FORMAT),
            'channel': scraper.channel,
            'pvrchannel': channel,
            'pvrid': pvrid,
            'logo': logoURL,
            'genre': entity2char(scraper.genre),
            'plot': entity2char(scraper.plot),
            'cast': entity2char(scraper.cast),
            'rating': scraper.rating
        }
        if pvrid: record.update(getBroadcast(pvrid, datetime.datetime.strftime(scraper.startdate, RSS_TIME_FORMAT_WOS)))

        items.append(record)
        item_nr += 1

    entry.update({'items': items})
    with open(SCRAPER_CONTENT, 'w', encoding='utf-8') as f:
        json.dump(entry, f, indent=4, ensure_ascii=False)

    HOME.setProperty('GTO.busy', 'false')
    HOME.setProperty('GTO.timestamp', str(int(time.time())))
    HOME.setProperty('GTO.provider', scraper.friendlyname)
    return item_nr


def change_scraper():
    global Scraper
    _scrapers = list()
    for modules in os.listdir(SCRAPER_FOLDER):
        if modules in (['__init__.py']) or modules[-3:] != '.py':
            continue
        writeLog('Found scraper: {}'.format(modules))
        module = __import__('{}.{}'.format(SCRAPER_MODULPATH, modules[:-3]), locals(), globals(), fromlist=['Scraper'])
        Scrapers = getattr(module, 'Scraper')

        if not Scrapers().enabled:
            continue
        li = xbmcgui.ListItem(label=Scrapers().friendlyname, label2=Scrapers().baseurl)
        li.setArt({'icon': getScraperIcon(Scrapers().icon)})
        li.setProperty('module', '{}.{}'.format(SCRAPER_MODULPATH, modules[:-3]))
        li.setProperty('shortname', Scrapers().shortname)
        _scrapers.append(li)

    _selected = xbmcgui.Dialog().select(LOC(30111), _scrapers, useDetails=True)
    if _selected > -1:
        writeLog('Selected scraper: {}'.format(_scrapers[_selected].getProperty('module')))
        ADDON.setSetting('preferred', _scrapers[_selected].getProperty('module'))
        ADDON.setSetting('scraper', _scrapers[_selected].getProperty('shortname'))
        module = __import__(_scrapers[_selected].getProperty('module'), locals(), globals(), fromlist=['Scraper'])
        Scraper = getattr(module, 'Scraper')


def show_info(item):
    if not os.path.isfile(SCRAPER_CONTENT):
        return False

    with open(SCRAPER_CONTENT, 'r', encoding='utf-8') as f:
        content = json.load(f)

    for property in window_properties: HOME.clearProperty('GTO.Info.{}'.format(property))
    item = content['items'][int(item)]

    if item.get('broadcastid', None) is not None:

        is_timer = hasTimer(item['broadcastid'])
        HOME.setProperty('GTO.Info.BroadcastID', str(item['broadcastid']))
        HOME.setProperty('GTO.Info.hasTimer', str(is_timer))

    if parser.parse(item['datetime'], dayfirst=False) >= datetime.datetime.now():
        writeLog('Title \'{}\' starts @{}, enable switchtimer button'.format(item['title'], item['datetime']))
        is_inFuture = True
        HOME.setProperty("GTO.Info.isInFuture", str(is_inFuture))

    elif parser.parse(item['datetime'], dayfirst=False) < datetime.datetime.now() < parser.parse(item['enddate'], dayfirst=False):
        writeLog('Title \'{}\' is currently running, enable switch button'.format(item['title']))

        is_running = True
        HOME.setProperty("GTO.Info.isRunning", str(is_running))

    HOME.setProperty("GTO.Info.Item", str(item['item']))
    HOME.setProperty("GTO.Info.Title", item['title'])
    HOME.setProperty("GTO.Info.Picture", item['thumb'])
    HOME.setProperty("GTO.Info.Description", item['plot'] or LOC(30140))
    HOME.setProperty("GTO.Info.Channel", item['pvrchannel'])
    HOME.setProperty("GTO.Info.ChannelID", str(item['pvrid']))
    HOME.setProperty("GTO.Info.Logo", item['logo'])
    HOME.setProperty("GTO.Info.Date", convert_dateformat(item['datetime']))
    HOME.setProperty("GTO.Info.RunTime", str(item['runtime'] // 60))
    HOME.setProperty("GTO.Info.EndTime", convert_dateformat(item['enddate']))
    if item['rating'] is None or item['rating'] == '':
        HOME.setProperty("GTO.Info.Genre", item['genre'])
    else:
        HOME.setProperty('GTO.Info.Genre', item['genre'] + ' | IMDb: ' + str(item['rating']))
    HOME.setProperty("GTO.Info.Cast", item['cast'])
    HOME.setProperty("GTO.Info.Rating", str(item['rating']))

    try:
        popup = xbmcgui.WindowXMLDialog(INFO_XML, ADDON_PATH)
        popup.doModal()
        del popup
    except RuntimeError:
        writeLog('Missing PVR info window for this skin', xbmc.LOGERROR)
        notifyOSD(LOC(30010), LOC(30136), icon=xbmcgui.NOTIFICATION_WARNING, enabled=True)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """

    writeLog('Parameter call for handle #{}: {}'.format(_handle, paramstring))
    params = dict(parse_qsl(paramstring))
    if params:
        try:
            if params['action'] == 'scrape':
                if scrape_page():
                    list_offers()

            elif params['action'] == 'change_scraper':
                change_scraper()
                if params.get('source', None) is None:
                    if scrape_page():
                        list_offers()

            elif params['action'] == 'getcontent':
                list_offers()

            elif params['action'] == 'info':
                show_info(params['item'])

            elif params['action'] == 'record':
                if not setTimer(params['broadcastid'], params['item']):
                    notifyOSD(LOC(30010), LOC(30134), icon=xbmcgui.NOTIFICATION_ERROR, enabled=True)
                else:
                    HOME.setProperty('GTO.timestamp', str(int(time.time())))
                    list_offers()

            elif params['action'] == 'reminder':
                if not setTimer(params['broadcastid'], params['item'], reminder=True):
                    notifyOSD(LOC(30010), LOC(30134), icon=xbmcgui.NOTIFICATION_ERROR, enabled=True)
                else:
                    # Reminders doesn't trigger a notification
                    notifyOSD(LOC(30010), LOC(30135), enabled=True)
                    HOME.setProperty('GTO.timestamp', str(int(time.time())))
                    list_offers()

            elif params['action'] == 'switch_channel':
                switchToChannel(params['pvrid'], params['item'])

            else:
                raise UnknownParameterException('Invalid parameter string: \'{}\''.format(paramstring))

        except UnknownParameterException as e:
            writeLog(e)
            notifyOSD(LOC(30010), LOC(30133), icon=xbmcgui.NOTIFICATION_ERROR, enabled=True)

    else:

        # Bootstrap
        list_offers()


if __name__ == '__main__':

    try:
        module = __import__(OPT_PREFERRED_SCRAPER, locals(), globals(), fromlist=['Scraper'])
        writeLog('import scraper module %s' % OPT_PREFERRED_SCRAPER)
    except ImportError:
        module = __import__(SCRAPER_DEFAULT, locals(), globals(), fromlist=['Scraper'])
        writeLog('import scraper module %s' % SCRAPER_DEFAULT)

    Scraper = getattr(module, 'Scraper')

    router(sys.argv[2][1:])

