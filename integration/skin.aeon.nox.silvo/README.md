Skintegration in Aeon Nox: Silvo:
----------------------------

If You want to use the plugin as widget you have to perfom following steps:

        cd $HOME/.kodi/addons/script.service.gto/integration/skin.aeon.nox.silvo

1. Copy the widget XML and graphics to Aeon Nox Silvo folder:

        cp gto-widget.xml $HOME/.kodi/addons/skin.aeon.nox.silvo/16x9/
        cp media/* $HOME/.kodi/addons/skin.aeon.nox.silvo/media/

2. Announce the XML to the skin. Edit ```$HOME/.kodi/addons/skin.aeon.nox.silvo/16x9/Includes.xml``` and include next line below the leading ```<includes>``` tag:

        <include file="gto-widget.xml" />

3. Modify the navigation to the widget in ```$HOME/.kodi/addons/skin.aeon.nox.silvo/16x9/Includes_Home.xml```:

      - Import the widget. Search for: ```<!-- NextRecording -->```. Place following above this line: 
         ```
         <!-- GTO Widget -->
         <include condition="System.HasAddon(script.service.gto)">HomeRecentlyAddedGTO</include>    
         ```
    
      - Search for ```<control type="button" id="9027">```
      - insert next line below ```<onup condition="Control.IsVisible(5777)">5777</onup>```
  
      - Search for ```<!-- Layouts -->```
      - around 17 lines below search for ```<onup condition="!Control.IsVisible(90010) + Control.IsVisible(90020) + !Control.IsVisible(9027) + !Skin.HasSetting(centermainmenu)">90020</onup>```
      - insert below this line ```<onup condition="Control.IsVisible(5777)">5777</onup>```
  
Note, the option "Show Recording widget" must be activated in skin settings!
Store all files. You are ready!