'''
Module that is imported by cli.py that deals with SoCo and Sonos interaction
'''

import os
from ipaddress import ip_address
from time import sleep
import json
import sys
import random
from operator import itemgetter 
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

import html
from urllib.parse import urlparse, quote, unquote

import soco
from soco.data_structures import DidlAlbum, to_didl_string
from soco.discovery import by_name
from soco.music_services import MusicService
from soco.exceptions import MusicServiceAuthException
from .config import music_service, master_speaker
from .sonos_config import STATIONS, META_FORMAT_PANDORA, META_FORMAT_RADIO, \
                         DIDL_LIBRARY_PLAYLIST, DIDL_AMAZON, DIDL_SERVICE, DIDL_ALBUM, DIDL_TRACK, \
                         SONOS_DIDL

import re
from unidecode import unidecode

ms = MusicService(music_service)
 
def extract(uri):
    #print(f"{uri=}")
    # I am storing Spotify uris with colons not %3a
    match = re.search(r"spotify.*[:/](album|track|playlist)[:/](\w+)", uri)
    spotify_uri = "spotify:" + match.group(1) + ":" + match.group(2)
    #print(f"{spotify_uri=}")
    share_type = spotify_uri.split(":")[1]
    encoded_uri = spotify_uri.replace(":", "%3a")
    return (share_type, encoded_uri)


def get_sonos_players():
    # master is assigned in sonos_cli2.py
    n = 0
    sp = None
    while n < 10:
        n+=1
        #print("attempt "+str(n)) 
        try:
            sp = soco.discover(timeout=2)
            #sp_names = {s.player_name:s for s in sp}
        except TypeError as e:    
            print(e) 
            sleep(1)       
        else:
            break 
    return sp    

def set_master(speaker):
     return by_name(speaker)
    
def my_add_to_queue(uri, metadata):
    # generally don't need the uri (can be passed as '') although passing it in
    try:
        response = master.avTransport.AddURIToQueue([
                ('InstanceID', 0),
                ('EnqueuedURI', uri), #x-sonos-http:library ...
                ('EnqueuedURIMetaData', metadata),
                ('DesiredFirstTrackNumberEnqueued', 0),
                ('EnqueueAsNext', 1)
                ])
    except soco.exceptions.SoCoUPnPException as e:
        print("my_add_to_queue exception:", e)
        print("uri:", uri)
        print("metadata:", metadata)
        return 0
    else:
        qnumber = response['FirstTrackNumberEnqueued']
        return int(qnumber)

# the 'action' functions
def current_track_info(text=True):
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'ERROR'

    # check if sonos is playing something
    if state == 'PLAYING':
        try:
            track = master.get_current_track_info()
        except Exception as e:
            print("Encountered error in track = master.get_current_track_info(): ", e)
            response = "I encountered an error trying to get current track info."
        else:
            title = track.get('title', '')
            artist = track.get('artist', '')
            album = track.get('album', '')
            if text:
                response = f"The track is {title}, the artist is {artist} and the album is {album}."
            else:
                response = {'title':title, 'artist':artist, 'album':album}
    else:
        response = None

    return response

def current():
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'error'

    # check if sonos is playing something
    if state == 'PLAYING':
        try:
            track = master.get_current_track_info()
        except Exception as e:
            print("Encountered error in track = master.get_current_track_info(): ", e)
            return

        return track

def turn_volume(volume):
    for s in master.group.members:
        s.volume = s.volume - 10 if volume=='quieter' else s.volume + 10

def set_volume(level):
    for s in master.group.members:
        s.volume = level

def mute(bool_):
    for s in master.group.members:
        s.mute = bool_

def unjoin():
    for s in master.group.members:
        s.unjoin()

# playq sonos playfromqueue
def play_from_queue(pos):
    try:
        master.play_from_queue(pos)
    except (soco.exceptions.SoCoUPnPException, soco.exceptions.SoCoSlaveException) as e:
        print("master.play_from_queue exception:", e)
    
def playback(type_):
    try:
        getattr(master, type_)()
    except soco.exceptions.SoCoUPnPException as e:
        print("master.{}:".format(type_), e)
        if type_ == 'play':
            try:
                master.play_from_queue(0)
            except (soco.exceptions.SoCoUPnPException, soco.exceptions.SoCoSlaveException) as e:
                print("master.play_from_queue exception:", e)

def play(add, uris):
    # must be a coordinator and possible that it stopped being a coordinator
    # after launching program
    global master
    if master is None:
        master = set_master(master_speaker)
    if not master.is_coordinator:
        master.unjoin()

    if not add:
    # with check on is_coordinator may not need the try/except
        try:
            master.stop()
            master.clear_queue()
        except (soco.exceptions.SoCoUPnPException,soco.exceptions.SoCoSlaveException) as e:
            print("master.stop or master.clear_queue exception:", e)

    for uri in uris:
        #print('uri: ' + uri)
        #print("---------------------------------------------------------------")
    
        # a few songs from Deborah album Like You've Never Seen Water are a playlist
        if 'library_playlist' in uri:
            i = uri.find(':')
            id_ = uri[i+1:]
            meta = DIDL_LIBRARY_PLAYLIST.format(id_=id_)
        elif 'library' in uri and not 'static' in uri:
            # this is a bought track and question also one that was uploaded one?
            i = uri.find('library')
            ii = uri.find('.')
            encoded_uri = uri[i:ii]
            meta = DIDL_AMAZON.format(id_=encoded_uri) #? if need parentID="" which isn't in DIDL_SERVICE
            #meta = DIDL_SERVICE.format(item_id="10030000"+encoded_uri, #interesting that id worked; from sharelink.py
            #        item_class = "object.item.audioItem.musicTrack",
            #        sn="51463")
            my_add_to_queue(encoded_uri, meta)
        elif 'static:library' in uri: # and 'static' in uri:
            # track moved from Prime into my account but not paid for - there is no reason to do this
            i = uri.find('library')
            ii = uri.find('?')
            encoded_uri = uri[i:ii]
            meta = DIDL_SERVICE.format(item_id="00032020"+encoded_uri, #that number is the sharelink "track" "key"
                    item_class = "object.item.audioItem.musicTrack",
                    sn="51463")
            my_add_to_queue(encoded_uri, meta)
        elif 'catalog' in uri: 
            # an Amazon music object (track or album)
            i = uri.find('catalog')
            ii = uri.find('?')
            encoded_uri = uri[i:ii]
            meta = DIDL_SERVICE.format(item_id="00032020"+encoded_uri, #that number is the sharelink "track" "key"
                    item_class = "object.item.audioItem.musicTrack",
                    sn="51463")
            my_add_to_queue(encoded_uri, meta)
        elif 'spotify' in uri:
            (share_type, encoded_uri) = extract(uri)
            meta = DIDL_SERVICE.format(item_id="00032020"+encoded_uri, #interesting that id worked; from sharelink.py
                    item_class = "object.item.audioItem.musicTrack",
                    sn="3079") #2311 is Spotify Europe
            my_add_to_queue(encoded_uri, meta)

        else:
            print(f'The uri:{uri} was not recognized')
            continue

        #print(f"{encoded_uri=}\n") 

    # need this because may have selected multiple tracks and want to start from the top (like shuffle)
    if not add:
        play_from_queue(0) 
   # else:
   #     queue = master.get_queue()
   #     play_from_queue(len(queue) - 1)

def play_station(station):
    station = STATIONS.get(station.lower())
    if station:
        uri = station[1]
        if uri.startswith('x-sonosapi-radio'):
            meta = META_FORMAT_PANDORA.format(title=station[0])
        elif uri.startswith('x-sonosapi-stream'):
            meta = META_FORMAT_RADIO.format(title=station[0])

        master.play_uri(uri, meta, station[0]) # station[0] is the title of the station

def list_queue():
    queue = master.get_queue()
    response = []
    for t in queue:
        if type(t) == soco.data_structures.DidlMusicTrack:
            response.append({"title": t.title, "artist": t.creator, "album": t.album})
        else:
            response.append({"title": t.metadata['title'], "artist": "", "album": "(MSTrack)"})
    return response

def clear_queue():
    try:
        master.clear_queue()
    except Exception as e:
        print("Encountered exception when trying to clear the queue:",e)
 
def shuffle(artists):
    master.stop() # not necessary but let's you know a new cmd is underway
    master.clear_queue()
    tracks = []
    results = ms.search("tracks", artists)
    random.shuffle(results)
    # get something playing right away
    master.add_to_queue(results[0])
    master.play_from_queue(0)
    tracks.append(results[0].title)
    for track in list(results)[1:]:
        # remove dups - not sure how common
        if track.title in tracks:
            continue
        track_metadata = track.metadata.get('track_metadata', None)
        #print(f"{track_metadata.metadata.get('artist')=}: {arg=}")
        if not track_metadata:
            continue
        # Occasionally the artist is in some field search looks at but it's not the artist for the song
        # may not be worth checking
        #if unidecode(track_metadata.metadata.get('artist').lower()) in artists.lower(): #added 07092023 
        #if artists.lower() in unidecode(track_metadata.metadata.get('artist').lower()): #added 07092023 
        track_artist = track_metadata.metadata.get('artist').lower()
        if not track_artist.isascii():
            track_artist = unidecode(track_artist)

        if any(word in track_artist for word in artists.lower().split()): #added 07092023 
        #if unidecode(track_metadata.metadata.get('artist').lower()) == artists.lower(): #added 07092023 
            try:
                master.add_to_queue(track)
            except Exception as e:
                print("Encountered exception when trying to clear the queue:",e)
            else:
                tracks.append(track.title)
    #master.play_from_queue(0)
    #return "\n".join(tracks)
    #if len(tracks) < 3:
    #    for track in list(results)[1:]:
    #        # remove dups - not sure how common
    #        if track.title in tracks:
    #            continue
    #        track_metadata = track.metadata.get('track_metadata', None)
    #        #print(f"{track_metadata.metadata.get('artist')=}: {arg=}")
    #        if not track_metadata:
    #            continue
    #        # Occasionally the artist is in some field search looks at but it's not the artist for the song
    #        # may not be worth checking
    #        try:
    #            master.add_to_queue(track)
    #        except Exception as e:
    #            print("Encountered exception when trying to clear the queue:",e)
    #        else:
    #            tracks.append(track.title)
    msg = ""
    for n, t in enumerate(tracks):
        msg += f"{n}. {t}\n"
    return msg

def old_shuffle(artists):
    tracklist = []
    msg = ""
    for artist in artists:
        s = 'artist:' + ' AND artist:'.join(artist.split())
        result = solr.search(s, fl='artist,title,uri', rows=500) 
        count = len(result)
        num_tracks = int(10/len(artists))
        if count:
            msg += f"Total track count for {artist} was {count}\n"
            tracks = result.docs
            k = num_tracks if count >= num_tracks else count
            random_tracks = random.sample(tracks, k)
            tracklist.extend(random_tracks)
        else:
            msg += f"I couldn't find any tracks for {artist.title()}\n"
            return msg

    random.shuffle(tracklist)
    uris = [t.get('uri') for t in tracklist]
    play(False, uris)

    titles = [t.get('title', '')+'-'+t.get('artist', '') for t in tracklist]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    msg += f"The mix for {' and '.join(artists)}:\n{title_list}"

    return msg
    
def list_(artist):
    s = 'artist:' + ' AND artist:'.join(artist.split())
    result = solr.search(s, fl='artist,title,uri', rows=500) 
    return result
    #count = len(result)
    #msg = ""
    #if count:
    #    msg += f"Track count for {artist.title()} was {count}:\n"
    #    tracks = result.docs
    #else:
    #    msg += f"I couldn't find any tracks for {artist.title()}\n"
    #    return msg

    #title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    ##msg += f"The list for {artist}:\n{title_list}"
    #msg += title_list

    #return msg

def play_pause():
    try:
        state = master.get_current_transport_info()['current_transport_state']
    except Exception as e:
        print("Encountered error in state = master.get_current_transport_info(): ", e)
        state = 'ERROR'

    # check if sonos is playing music
    if state == 'PLAYING':
       # master.pause()
        playback('pause')
    else:
        playback('play')
    #elif state!='ERROR':
    #    master.play()

def play_track(track):
    results = ms.search("tracks", track)
    master.add_to_queue(results[0])
    queue = master.get_queue()
    master.play_from_queue(len(queue) - 1)
    return results[0].title

def generate_search_fallbacks(query):
    """Generate simplified search terms for fallback when parsing fails."""
    words = query.strip().split()
    if len(words) <= 2:
        return []
    
    fallbacks = []
    
    # Try removing one word at a time, starting from the beginning
    for i in range(len(words)):
        if i == 0:
            # Skip first word
            fallback = " ".join(words[1:])
        else:
            # Remove word at position i
            fallback = " ".join(words[:i] + words[i+1:])
        
        if fallback not in fallbacks:
            fallbacks.append(fallback)
    
    # Try keeping only the last 2-3 words (often artist name)
    if len(words) >= 3:
        fallback = " ".join(words[-2:])
        if fallback not in fallbacks:
            fallbacks.append(fallback)
    
    return fallbacks

def search_track_with_retry(track, max_retries=5):
    """Search for tracks with retry logic for AuthTokenExpired and parsing errors."""
    # First try the original search with AuthToken retry logic
    for attempt in range(max_retries):
        try:
            return ms.search("tracks", track)
        except MusicServiceAuthException as e:
            if "AuthTokenExpired" in str(e) and attempt < max_retries - 1:
                print(f"API call failed (attempt {attempt + 1}/{max_retries}), retrying in 1 second...")
                sleep(1)
                continue
            else:
                # Re-raise if it's not AuthTokenExpired or we've exhausted retries
                raise
        except TypeError as e:
            # This is likely the SoCo parsing bug, try fallback searches
            if "string indices must be integers" in str(e):
                print(f"Search parsing failed with '{track}', trying simplified searches...")
                
                fallbacks = generate_search_fallbacks(track)
                for fallback in fallbacks:
                    try:
                        print(f"Trying: '{fallback}'")
                        results = ms.search("tracks", fallback)
                        print(f"Success with '{fallback}'")
                        return results
                    except (TypeError, MusicServiceAuthException):
                        continue
                
                # If all fallbacks failed, re-raise original error
                print(f"All fallback searches failed for '{track}'")
                raise
            else:
                # Different TypeError, re-raise
                raise

def search_track(track):
    results = search_track_with_retry(track)

    tracks = []
    sonos_data = []
    for track in results:
        track_meta = track.metadata.get('track_metadata')
        if track_meta and track_meta.metadata:
            artist = track_meta.metadata.get('artist', 'Unknown Artist')
            album = track_meta.metadata.get('album', 'Unknown Album')
            tracks.append(f"{track.title}-{artist}-{album}")
        else:
            tracks.append(f"{track.title}-Unknown Artist-Unknown Album")
    
        item_id = track.metadata.get('id') 
        uri = html.escape(track.uri) # the uri typically has & which needs to be html entity escaped
        sonos_data.append([item_id, uri])

    filename = "sonos_data.json"
    with open(filename, 'w') as f:
        json.dump(sonos_data, f, indent=2)

    track_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(tracks, start=1)])
    return track_list

def search_for_track(track):
    results = search_track_with_retry(track)

    tracks = []
    for track in results:
        track_meta = track.metadata.get('track_metadata')
        if track_meta and track_meta.metadata:
            artist = track_meta.metadata.get('artist', 'Unknown Artist')
            album = track_meta.metadata.get('album', 'Unknown Album')
            item_id = track.metadata.get('id') 
            uri = html.escape(track.uri) # the uri typically has & which needs to be html entity escaped
            tracks.append({"title":track.title, "artist":artist, "album":album, "item_id":item_id, "uri":uri})
        else:
            uri = html.escape(track.uri) # the uri typically has & which needs to be html entity escaped
            tracks.append({"title":track.title, "artist":"Unknown Artist", "album":"Unknown Album", "item_id":"Unknown item_id", "uri":uri})
    
    filename = "sonos_data2.json"
    with open(filename, 'w') as f:
        json.dump(tracks, f, indent=2)

    track_list = "\n".join([f"{t[0]}. {"-".join(list(t[1].values())[:3])}" for t in enumerate(tracks, start=1)])
    return track_list

def play_track_from_search_list(position):
    filename = "sonos_track_uris.json"
    with open(filename, 'r') as f:
        track_uris = json.load(f)

    play(True, [track_uris[position-1]]) # add

def add_album_to_queue(position):
    filename = "sonos_data.json"
    with open(filename, 'r') as f:
        sonos_data = json.load(f)

    item_id, uri = sonos_data[position-1]

    #Note: the id appears to be necessary for track ddl but not for album ddl
    metadata = SONOS_DIDL.format(item_id=item_id, uri=uri)
    my_add_to_queue(uri, metadata)

def add_track_to_queue(position):
    filename = "sonos_data2.json"
    with open(filename, 'r') as f:
        sonos_data = json.load(f)

    t = sonos_data[position-1]
    #Note: the id appears to be necessary for track ddl but not for album ddl
    metadata = SONOS_DIDL.format(item_id=t['item_id'], uri=t['uri'])
    my_add_to_queue(t['uri'], metadata)

def search_for_album(album):
    results = ms.search("albums", album)

    albums = []
    sonos_data = []
    for album in results:
        album_meta = album.metadata
        artist = album_meta.get('artist', 'Unknown Artist')
        title = album_meta.get('title', 'Unknown Title')
        albums.append(f"{title} - {artist}")

        # Note: for the purpose of creating the DIDL string it appears that the item_id is unnecessary
        item_id = quote(album_meta.get('id')) # the album ids have a # although doesn't seem to need escaping   
        sonos_data.append([item_id, album.uri])

    filename = "sonos_data.json"
    with open(filename, 'w') as f:
        json.dump(sonos_data, f, indent=2)

    # Use the returned list to select an album to play and use its position in list to select from the sonos_data.json file
    album_list = "\n".join([f"{a[0]}. {a[1]}" for a in enumerate(albums, start=1)])
    return album_list

def add_to_playlist_from_queue(playlist, position):
    #queue = list_queue()
    queue = master.get_queue()
    if 0 < position <= len(queue):
        track = queue[position-1]
        #title, artist, album = track.values()
    else:
        return f"{position} is out of the range of the queue"

    uri = track.get_uri()
    unquoted_uri = unquote(uri)
    parsed_uri = urlparse(unquoted_uri)
    path = parsed_uri.path
    directory_path = os.path.dirname(path) + "/"
    uri = f"soco://0fffffff{directory_path}?sid=201&amp;sn=0"

    filename = playlist
    file_path = Path.home() / "sonos_cli" / "playlists" / filename

    if file_path.is_file():
        with file_path.open('r') as file:
            data = json.load(file)

        data.append({"title": track.title, "artist": track.creator, "album": track.album, "item_id": directory_path, "uri": uri})
        with file_path.open('w') as file:
            json.dump(data, file, indent=2)
    else:
      file_path.parent.mkdir(parents=True, exist_ok=True)
      data = [{"title": track.title, "artist": track.creator, "album": track.album, "item_id": directory_path, "uri": uri}]
      with file_path.open('w') as file:
        json.dump(data, file, indent=2)

    return f"Selected track {position}: {track.title} by {track.creator} from the queue and added to playlist {playlist}"

def add_to_playlist_from_search(playlist, position):
    filename = "sonos_data2.json"
    with open(filename, 'r') as f:
        sonos_data = json.load(f)

    d = sonos_data[position-1]

    filename = playlist
    file_path = Path.home() / "sonos_cli" / "playlists" / filename

    if file_path.is_file():
        with file_path.open('r') as file:
            data = json.load(file)

        data.append(d)
        with file_path.open('w') as file:
            json.dump(data, file, indent=2)
    else:
      file_path.parent.mkdir(parents=True, exist_ok=True)
      data = [d]
      with file_path.open('w') as file:
        json.dump(data, file, indent=2)

    return f"Selected track {position}: {d["title"]} by {d["artist"]} from the search and added to playlist {playlist}"

def add_playlist_to_queue(playlist):
    filename = playlist
    file_path = Path.home() / "sonos_cli" / "playlists" / filename

    if not file_path.is_file():
        return f"Playlist {playlist} does not exist"

    with file_path.open('r') as file:
        tracks = json.load(file)

    for t in tracks:
        #Note: the id appears to be necessary for track ddl but not for album ddl
        metadata = SONOS_DIDL.format(item_id=t['item_id'], uri=t['uri'])
        my_add_to_queue(t['uri'], metadata)


    return f"Added {len(tracks)} tracks from playlist {playlist} to the queue"
