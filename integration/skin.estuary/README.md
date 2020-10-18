Skintegration in Estuary:
----------------------------

Because Estuary is the default skin of Kodi Jarvis and up and possibly resides in a read-only area of the system (LibreElec, Corelec, ...), you have to place a copy of the system skin folder to the addons folder:
        
        cp -R /usr/share/kodi/addons/skin.estuary $HOME/.kodi/addons/
        
         
If You want to use the plugin as widget you have to perfom following steps:

1. Copy skin icon and widget to Estuary folder:

        cd $HOME/.kodi/addons/script.service.gto/integration/skin.estuary
        cp -R icons $HOME/.kodi/addons/skin.estuary/extras/icons
        cp gto-widget.xml $HOME/.kodi/addons/skin.estuary/xml/

2. Register the include:

        nano $HOME/.kodi/addons/skin.estuary/xml/Includes_Home.xml
        
   Insert in line 3 (after `<includes>`):
   
        <include file="gto-widget.xml"/>

   Save changes and exit
    
3. Insert the widget into the PVR section of the skin. Open the Home.xml and search for the PVR includes.
   
        nano $HOME/.kodi/addons/skin.estuary/xml/Home.xml
        
    Search for the PVR includes. Use following text as search item: 
   
        <include content="WidgetListCategories" condition="System.HasPVRAddon">
            
    Every widget has the same structure, a widget list is closed with a `</control>` tag.
    Insert before `</control>` tag:
     
        <include content="WidgetListGTO" condition="System.HasPVRAddon + System.HasAddon(script.service.gto)">
            <param name="content_path" value="plugin://script.service.gto?action=getcontent&amp;ts=$INFO[Window(Home).Property(GTO.timestamp)]"/>
            <param name="widget_header" value="$ADDON[script.service.gto 30104]: $INFO[Window(Home).Property(GTO.Provider)]"/>
            <param name="widget_target" value="pvr"/>
            <param name="list_id" value="12500"/>
            <param name="label" value="$INFO[ListItem.label2]$INFO[ListItem.Property(StartTime), (,)]"/>
            <param name="label2" value="$INFO[ListItem.label]"/>
        </include>
        
    Save changes (CTRL-o) and exit (CTRL-x)

    Example:
    
            <include content="WidgetListCategories" condition="System.HasPVRAddon">
                <param name="widget_header" value="$LOCALIZE[31148]"/>
                <param name="list_id" value="12900"/>
                <param name="pvr_submenu" value="true"/>
                <param name="pvr_type" value="TV"/>
            </include>
            <include content="WidgetListChannels" condition="System.HasPVRAddon">
                <param name="content_path" value="pvr://channels/tv/*?view=lastplayed"/>
                <param name="sortby" value="lastplayed"/>
                <param name="sortorder" value="descending"/>
                <param name="widget_header" value="$LOCALIZE[31016]"/>
                <param name="widget_target" value="pvr"/>
                <param name="list_id" value="12200"/>
            </include>
            ...
            <include content="WidgetListGTO" condition="System.HasPVRAddon + System.HasAddon(script.service.gto)">
                <param name="content_path" value="plugin://script.service.gto?action=getcontent&amp;ts=$INFO[Window(Home).Property(GTO.timestamp)]"/>
                <param name="widget_header" value="$ADDON[script.service.gto 30104]: $INFO[Window(Home).Property(GTO.Provider)]"/>
                <param name="widget_target" value="pvr"/>
                <param name="list_id" value="12500"/>
                <param name="label" value="$INFO[ListItem.label2]$INFO[ListItem.Property(StartTime), (,)]"/>
                <param name="label2" value="$INFO[ListItem.label]"/>
            </include>
        </control>
    
			
4. Extend DefaultDialogButton with 2nd click

        nano $HOME/.kodi/addons/skin.estuary/xml/Includes_Buttons.xml
    
    search for `<include name="DefaultDialogButton">` and extend within the control group the 2nd `<onclick>$PARAM[onclick]</onclick>`:
      
            ```<onclick>$PARAM[onclick_2]</onclick>```
        
    Example:
     
             <control type="button" id="$PARAM[id]">
                <width>$PARAM[width]</width>
                <height>$PARAM[height]</height>
                <label>$PARAM[label]</label>
                <font>$PARAM[font]</font>
                <textoffsetx>20</textoffsetx>
                <onclick>$PARAM[onclick]</onclick>
                <onclick>$PARAM[onclick_2]</onclick>
                <wrapmultiline>$PARAM[wrapmultiline]</wrapmultiline>
                <align>center</align>
                <texturefocus border="40" colordiffuse="button_focus">buttons/dialogbutton-fo.png</texturefocus>
                <texturenofocus border="40">buttons/dialogbutton-nofo.png</texturenofocus>
                <visible>$PARAM[visible]</visible>
             </control>

			
Save and exit nano. Restart Kodi.