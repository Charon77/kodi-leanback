# Kodi modules
import xbmc
import xbmcaddon
import xbmcgui

# Python modules
# import platform
# import os.path
# import subprocess
import json
import requests
import threading
from threading import Thread
from requests import ConnectionError
import sys

# Getting constants
__addon__ = xbmcaddon.Addon('script.youtube.leanback')
__addonId__ = __addon__.getAddonInfo('id')
__addonName__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__localizedMessages__ = __addon__.getLocalizedString

yt_url_screen_id = 'https://www.youtube.com/api/lounge/pairing/generate_screen_id'
yt_url_lounge_id = 'https://www.youtube.com/api/lounge/pairing/get_lounge_token_batch'
yt_url_bind = 'https://www.youtube.com/api/lounge/bc/bind'
yt_url_pairing_code = 'https://www.youtube.com/api/lounge/pairing/get_pairing_code'


class LeanbackPlayer(xbmc.Player):
    global dialog

    # def __init__(self, *args):
    #     log("ZZZZZZZZZ")
    #     pass

    def onPlayBackPaused(self):
        postBind("onStateChange", {
            'currentTime': self.getTime(),
            'state': '2',
            })
    def onPlayBackResumed(self):
        postBind("onStateChange", {
            'currentTime': self.getTime(),
            'state': '1',
            })
    # def onAVChange(self):
    #     dialog.textviewer("Callback", "AVCh")
    # def onAVStarted(self):
    #     dialog.textviewer("Callback", "AVStarted")
    def onPlayBackSeek(self, time, seekOffset):
        postBind("onStateChange", {
            'currentTime': self.getTime(),
            'state': '1',
            })
    def onAVStarted(self):
        self.seekTime(float(now_playing_state['currentTime']))

        postBind("onStateChange", {
            'currentTime': self.getTime(),
            'state': '1',
            })




# Method to print logs on a standard way
def log(message, level=xbmc.LOGNOTICE):
    xbmc.log('[%s:v%s] %s' % (__addonId__, __version__, message.encode('utf-8')), level)
# end of log

def postBind(key,val):
    global ofs
    ofs += 1
    post_params = {}
    post_params['ofs'] = ofs
    post_params['count'] = 1
    post_params['req0__sc']=key
    bind_params['RID'] = '1337'


    for (k,v) in val.items():
        post_params['req0_'+k] = v
    #dialog.textviewer("Post Bind A", json.dumps(post_params))

    requests.post(yt_url_bind, params=bind_params, data=post_params)


def parseBind(obj):
    log("Received " + json.dumps(obj))
    cmd = obj[0]

    if cmd == "noop":
        pass
    elif cmd == "loungeStatus":
        pass
    elif cmd == "c":
        bind_params["SID"] = obj[1]
    elif cmd == "S":
        bind_params["gsessionid"] = obj[1]
    elif cmd == "getNowPlaying":
        #dialog.textviewer("Get Now Playing", "A")
        if 'videoId' in now_playing_state:
            postBind("nowPlaying", {})
        else:
            postBind("nowPlaying", now_playing_state)
    elif cmd == "setPlaylist":
        params = obj[1]
        eventDetails = json.loads(params["eventDetails"])
        videoId = eventDetails["videoId"]
        player.play('plugin://plugin.video.youtube/play/?video_id={0}'.format(videoId))
        log(json.dumps(obj))

        now_playing_state['videoId'] = eventDetails["videoId"]
        now_playing_state['listId'] = params["listId"]
        now_playing_state['ctt'] = params['ctt']
        now_playing_state['currentTime'] = params['currentTime']
        now_playing_state['currentIndex'] = '0'
        now_playing_state['state'] = '3'

        postBind("nowPlaying", now_playing_state)


        # now_playing_state['state'] = '1'
        # postBind("onStateChange", {
        #     'currentTime': '15',
        #     'state': '1',
        #     'duration': '50',
        #     'cpn': 'foo',
        #     })
        #dialog.textviewer("Set Playlist", videoId)
    #elif cmd == "updatePlaylist":
        #dialog.textviewer("Update Playlist", json.dumps(obj))
    elif cmd == "pause":
        player.pause()
        now_playing_state['state'] = '2'
        postBind("onStateChange", {
            'currentTime': player.getTime(),
            'state': now_playing_state['state'],
            #'duration': '50',
            #'cpn': 'foo',
            })
    elif cmd == "play":
        player.pause()
        now_playing_state['state'] = '1'
        postBind("onStateChange", {
            'currentTime': player.getTime(),
            'state': now_playing_state['state'],
            #'duration': '50',
            #'cpn': 'foo',
            })
    elif cmd == "seekTo":
        newTime = obj[1]['newTime']
        player.seekTime(float(newTime))
        postBind("onStateChange", {
            'currentTime': newTime,
            'state': now_playing_state['state'],
            })

    elif cmd == "setVolume":
        newVolume = obj[1]['volume']
        log(newVolume)
        xbmc.executebuiltin('SetVolume({0}, true)'.format(newVolume))
        postBind("onVolumeChanged", {
            "volume": newVolume,
            "muted": "false"}
        )

    else:
        log("Unknown command")
        log(json.dumps(obj))

        #dialog.textviewer("Unknown command", json.dumps(obj))

class BindThread(Thread):
    def __init__(self):
        super(BindThread, self).__init__()
        self.session = requests.Session()
        self.is_stopping = False


    def run(self):
        while not self.is_stopping:
            log(json.dumps(bind_params))

            bind_params["RID"] = "rpc"
            bind_params["CI"] = "0"

            self.bind_stream = self.session.get(yt_url_bind, params=bind_params, stream=True)
            json_buffer = ""

            if not self.bind_stream.ok:
                log("Bind Thread not okay")

            for line in self.bind_stream.iter_lines():
                log("line read")
                log(line)

                try:
                    int(line)
                except ValueError:
                    json_buffer += line
                    json_buffer += "\n"
                else:
                    json_buffer = ""

                try:
                    list_of_items = json.loads(json_buffer)
                except (ValueError, TypeError):
                    pass
                else:
                    for item in list_of_items:
                        obj = item[1]
                        parseBind(obj)

    def kill(self):
        self.is_stopping = True
        if (self.bind_stream):
            log("Killing")
            self.bind_stream.close()


if __name__ == '__main__':
    ofs = 0
    # Starting the Addon
    log("Starting " + __addonName__)

    dialog = xbmcgui.Dialog()



    now_playing_state = {
            'videoId': None,
            'currentTime': None,
            'ctt': None,
            'listId': None,
            'currentIndex': None,
            'state': '3',
            }

    # Screen ID
    screen_id = __addon__.getSetting('screen_id')
    if not screen_id:
        screen_id = requests.get(yt_url_screen_id).text
        __addon__.setSetting('screen_id', screen_id)


    screen_name = __addon__.getSetting('screen_name')
    if not screen_name:
        screen_name = 'Kodi Leanback'
        __addon__.setSetting('screen_name', screen_name)

    app_name = __addon__.getSetting('app_name')
    if not app_name:
        screen_name = 'Kodi Leanback App'
        __addon__.setSetting('app_name', screen_name)

    # Lounge Token
    lounge_token = json.loads(requests.get(yt_url_lounge_id, {'screen_ids': screen_id}).text)['screens'][0]['loungeToken']
    #dialog.ok("Lounge Token", lounge_token)

    # Pairing Code

    pairing_codeparams = {
            "ctx":          "pairing",
            "access_type":  "permanent",
            "app":          app_name,
            "lounge_token": lounge_token,
            "screen_id":    screen_id,
            "screen_name":  screen_name,
            }


    pairing_code = requests.get(yt_url_pairing_code, pairing_codeparams).text
    __addon__.setSetting('pairingCode', pairing_code)


    # Bind
    bind_params = {
                    "device":        "LOUNGE_SCREEN",
                    "id":            screen_id,
                    "name":          screen_name,
                    "app":           app_name,
                    "theme":         "cl",
                    "capabilities":  {},
                    "mdx-version":   "2",
                    "loungeIdToken": lounge_token,
                    "VER":           "8",
                    "v":             "2",
                    "RID":           "1337",
                    "AID":           "42",
                    "zx":            "xxxxxxxxxxxx",
                    "t":             "1",
            }


    # Initial Bind
    bind_resp = requests.post(yt_url_bind, bind_params).text
    bind_resp = ''.join(bind_resp.split('\n')[1:])
    bind_resp_obj = json.loads(bind_resp)

    for obj in bind_resp_obj:
        parseBind(obj[1])

    player = LeanbackPlayer()
    x = BindThread()
    x.start()

    monitor = xbmc.Monitor()
    # Repeat while not exiting
    while not monitor.abortRequested():
        # Sleep/wait for abort for 3 seconds
        if monitor.waitForAbort(0.25):
            # Abort was requested while waiting. We should exit
            x.kill()
            break
        xbmc.sleep(250)




