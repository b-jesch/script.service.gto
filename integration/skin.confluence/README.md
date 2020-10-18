Skintegration in Confluence:
----------------------------

If You want to use the plugin as widget you have to perfom following steps:

        cd $HOME/.kodi/addons/script.service.gto/integration/skin.confluence

1. Copy XML and graphics to the Confluence skin

        cp gto-widget.xml $HOME/.kodi/addons/skin.confluence/720p/
        cp -R media $HOME/.kodi/addons/skin.confluence/
        
2. Announce the XML to the skin.

        cd $HOME/.kodi/addons/skin.confluence/720p/
        nano Includes.xml
        
    Include next line below the leading ```<includes>``` tag:
        
        <include file="gto-widget.xml" />
        
    store changes (CTRL-O, CTRL-X)
        
        nano IncludesHomeRecentlyAdded.xml
    
    Search for ```<control type="group" id="9003">```. Add below:
        <include>HomeRecentlyAddedGTO</include>

4. Include buttons for "change Scraper" and "reload Scraper"

        nano IncludesHomeMenuItems.xml
        
    Search for ```<control type="image" id="90149">``` and add before this control (between control 90148 and 90149):

		<control type="button" id="90150">
			<include>ButtonHomeSubCommonValues</include>
			<label>$ADDON[script.service.gto 30115]</label>
			<onclick>RunPlugin(plugin://script.service.gto?action=change_scraper)</onclick>
			<visible>System.HasAddon(script.service.gto)</visible>
		</control>
		<control type="button" id="90151">
			<include>ButtonHomeSubCommonValues</include>
			<label>$ADDON[script.service.gto 30116]</label>
			<onclick>RunPlugin(plugin://script.service.gto?action=scrape)</onclick>
			<visible>System.HasAddon(script.service.gto)</visible>
		</control> 


Store and restart Kodi. You are done!