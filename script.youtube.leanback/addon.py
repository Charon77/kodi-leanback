# Kodi modules
import xbmc
import xbmcaddon
import xbmcgui

__addon__ = xbmcaddon.Addon('script.youtube.leanback')


dialog = xbmcgui.Dialog()


pairing_code = __addon__.getSetting('pairingCode')

dialog.ok("Pairing Code", "{0}-{1}-{2}-{3}".format(pairing_code[0:3], pairing_code[3:6], pairing_code[6:9], pairing_code[9:12]))
