Skintegration in Confluence:
----------------------------

If You want to use the plugin as widget you have to perfom following steps:

        cd $HOME/.kodi/addons/script.service.gto/integration/skin.confluence

1. Copy XML and graphics to the Confluence skin

        cp script-gto.xml $HOME/.kodi/addons/skin.confluence/720p/
        cp -R media $HOME/.kodi/addons/skin.confluence/720p/media
        
2. Announce the XML to the skin. Edit ```$HOME/.kodi/addons/skin.confluence/16x9/Includes.xml``` and include next line below the leading ```<includes>``` tag:

        <include file="gto-widget.xml" />

3. Open ```$HOME/.kodi/addons/skin.confluence/720p/IncludesHomeRecentlyAdded.xml``` and search for ```<control type="group" id="9003">```. Add below ```<include>HomeRecentlyAddedGTO</include>```.

Store all files. You are done!
