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

import html
from urllib.parse import quote

import soco
from soco.data_structures import DidlAlbum, to_didl_string
from soco.discovery import by_name
from soco.music_services import MusicService
from soco.exceptions import MusicServiceAuthException
from .config import music_service
from .sonos_config import STATIONS, META_FORMAT_PANDORA, META_FORMAT_RADIO, \
                         DIDL_LIBRARY_PLAYLIST, DIDL_AMAZON, DIDL_SERVICE, DIDL_ALBUM, DIDL_TRACK, \
                         SONOS_DIDL

import re
from unidecode import unidecode
#soco_config.CACHE_ENABLED = False

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
#    try:
#        ip_address(speaker)
#    except ValueError:
#        pass
#    else:
#        return soco.SoCo(speaker)
#
#    sps = get_sonos_players()
#    if not sps:
#        return None
#
#    sp_names = {s.player_name:s for s in sps}
#    return sp_names.get(speaker)

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
        master = set_master("Office2")
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

def play_track_from_search_list(position):
    filename = "sonos_track_uris.json"
    with open(filename, 'r') as f:
        track_uris = json.load(f)

    play(True, [track_uris[position-1]]) # add

def select_from_list(position):
    filename = "sonos_data.json"
    with open(filename, 'r') as f:
        sonos_data = json.load(f)
    item_id, uri = sonos_data[position-1]
    #uri = html.escape(uri) # the uri typically has & which needs to be html entity escaped but now done in search_track
    #Note: the id appears to be necessary for track ddl but not for album ddl

    #metadata = DIDL_TRACK.format(item_id=item_id, uri=uri)
    metadata = SONOS_DIDL.format(item_id=item_id, uri=uri)

    my_add_to_queue(uri, metadata)

def search_track2(track):
    results = search_track_with_retry(track)
    return results

def search_album(album):
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

    album_list = "\n".join([f"{a[0]}. {a[1]}" for a in enumerate(albums, start=1)])
    return album_list

    #print(f"Found {len(album_list)} albums matching '{album}' with the following results {album_list}")

    #print(to_didl_string(results[0]))
    #item_id = quote(results[0].metadata.get('id'))
    # not that id appears to be unnecessary for album ddl but necessary for track ddl

    #metadata = DIDL_ALBUM.format(item_id=item_id, uri=results[0].uri)
    #metadata = SONOS_DIDL.format(item_id=item_id, uri=results[0].uri)

    #print(metadata)
    #my_add_to_queue(results[0].uri, metadata)

def play_album(album):
    master.stop() # not necessary but let's you know a new cmd is underway
    master.clear_queue()
    results = ms.search("albums", album)

    albums = []
    album_data = []
    for album in results:
        album_meta = album.metadata
        artist = album_meta.get('artist', 'Unknown Artist')
        title = album_meta.get('title', 'Unknown Title')
        albums.append(f"{title} - {artist}")
        # Note: for the purpose of creating the DIDL string it appears that the item_id is unnecessary
        item_id = quote(album_meta.get('id')) # the album ids have a # although doesn't seem to need escaping   
        album_data.append([item_id, album.uri])

    album_list = "\n".join([f"{a[0]}. {a[1]}" for a in enumerate(albums, start=1)])
    print(f"Found {len(album_list)} albums matching '{album}' with the following results {album_list}")

    filename = "sonos_album_data.json"
    with open(filename, 'w') as f:
        json.dump(album_data, f, indent=2)

    print(to_didl_string(results[0]))
    item_id = quote(results[0].metadata.get('id'))
    # not that id appears to be unnecessary for album ddl but necessary for track ddl

    #metadata = DIDL_ALBUM.format(item_id=item_id, uri=results[0].uri)
    metadata = SONOS_DIDL.format(item_id=item_id, uri=results[0].uri)

    print(metadata)
    my_add_to_queue(results[0].uri, metadata)
    return
    master.add_to_queue(results[0]) #this works but our problem is we are saving to disk
    master.play_from_queue(0)
    print(dir(results[0]))
    print(results[0].metadata)
    print(results[0].uri)
    print(results[0].item_id)
    print(to_didl_string(results[0]))
    return

    ##play(True, [results[0].uri])
    ##play(True, [results[0].metadata.get('id')[:-11]+'?sid=201&sn=0'])
    #master.play_from_queue(0)
    #return list_queue()
    #results[0].metadata["item_id"] = results[0].metadata.get('id')
    #results[0].metadata["parent_id"] = ""
    #del results[0].metadata["id"]
    #del results[0].metadata["item_type"]
    #didl_object = DidlAlbum.from_dict(results[0].metadata)
    #didl_lite_xml = didl_object.to_xml()
    #print(f"{didl_lite_xml=}")

    #uri = results[0].uri[:-13]
    uri = results[0].uri

    i = uri.find('catalog')
    #ii = uri.find('?'))
    print(f"{uri=}")
    encoded_uri = uri[i:]
    master.add_uri_to_queue(uri)
    return
    #meta = DIDL_SERVICE_ALBUM.format(item_id="00032020"+encoded_uri, #that number is the sharelink "track" "key"
    meta = DIDL_SERVICE_ALBUM.format(id_ = encoded_uri, #that number is the sharelink "track" "key"
            #item_class = "object.item.audioItem.musicTrack",
            item_class = "object.container.album.musicAlbum",
            sn="51463")
    my_add_to_queue(encoded_uri, meta)

def parse_play_request(user_request: str) -> Dict[str, Any]:

    """
    Algorithmic parsing vs having LLM do the parsing including looking for 'preferences'
    like "live version" or "acoustic version".
    
    This handles basic patterns like "song by artist" and "artist's song".
    """
    request_lower = user_request.lower().strip()
    
    # Remove common prefixes
    request_lower = re.sub(r'^(play\s+|i\s+want\s+to\s+hear\s+|put\s+on\s+)', '', request_lower)
    request_lower = re.sub(r'\s+', ' ', request_lower).strip()
    
    # Simple preferences detection
    preferences = {}
    if re.search(r'\blive\s+(?:version|recording)', request_lower):
        preferences['prefer_live'] = True
    elif re.search(r'\bacoustic\s+(?:version|recording)', request_lower):
        preferences['prefer_acoustic'] = True
    
    # Remove preference phrases from text before parsing title/artist
    # Remove live-related phrases
    request_lower = re.sub(r'\b(?:a|the|some|an)?\s*live\s+(?:version|recording)(?:\s+of)?\b', '', request_lower)
    # Remove acoustic-related phrases  
    request_lower = re.sub(r'\b(?:a|the|some|an)?\s*acoustic\s+(?:version|recording)(?:\s+of)?\b', '', request_lower)
    
    # Clean up extra whitespace that may result from removals
    request_lower = re.sub(r'\s+', ' ', request_lower).strip()
    
    # Simple "by" pattern
    by_match = re.search(r'^(.+?)\s+by\s+(.+)$', request_lower)
    if by_match:
        return {
            'title': by_match.group(1).strip(),
            'artist': by_match.group(2).strip(),
            'preferences': preferences
        }
    
    # Simple possessive pattern
    poss_match = re.search(r"^(.+?)'s\s+(.+)$", request_lower)
    if poss_match:
        return {
            'title': poss_match.group(2).strip(),
            'artist': poss_match.group(1).strip(),
            'preferences': preferences
        }
    
    # Fallback: treat as title only
    return {
        'title': request_lower,
        'artist': None,
        'preferences': preferences
    }

def generate_query_and_do_search(title: str, artist: str = None, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate intelligent search queries with fallback strategies for API issues.
    
    Specifically handles the "fixing her hair" API parsing issue by using
    alternative query formats that avoid the problematic pattern.
    
    Args:
        title: Song title
        artist: Artist name (optional)
        preferences: Search preferences
        
    Returns:
        Ordered list of search query strings to try
    """
    preferences = preferences or {}
    query = ""
    search_result = ""
    clean_title = clean_for_matching(title) #########
    clean_artist = clean_for_matching(artist) ########
    
    if clean_artist:
        if preferences.get('prefer_live'):
            query = f"{clean_title} {clean_artist} live"
        elif preferences.get('prefer_acoustic'):
            query = f"{clean_title} {clean_artist} acoustic"
        else:
            query = f"{clean_title} {clean_artist}"

    else:
        # No artist specified
        if preferences.get('prefer_live'):
            query = f"{clean_title} live"
        elif preferences.get('prefer_acoustic'):
            query = f"{clean_title} acoustic"
        else:
            query = clean_title

    try:
        search_result = search_track(query)
    except:
        pass
    
    return {
        'title': clean_title,
        'artist': clean_artist,
        'preferences': preferences or {},
        'query': query,
        'results': search_result,  # Top 10 results
        'total_results': len(search_result)
    }
    #return search_result


def parse_search_results(search_output: str) -> List[Dict[str, Any]]:
    """
    Parse sonos searchtrack output into structured data.
    
    Args:
        search_output: Raw output from sonos searchtrack command
        
    Returns:
        List of track dictionaries with position, title, artist, album
    """
    results = []
    lines = search_output.strip().split('\n')
    
    for line in lines:
        # Match pattern: "number. Title-Artist-Album"
        match = re.match(r'^(\d+)\.\s+(.+?)-(.+?)-(.+)$', line.strip())
        if match:
            results.append({
                'position': int(match.group(1)),
                'title': match.group(2).strip(),
                'artist': match.group(3).strip(),
                'album': match.group(4).strip(),
                'raw_line': line.strip()
            })
        else:
            # Fallback for old format without album
            old_match = re.match(r'^(\d+)\.\s+(.+?)-(.+)$', line.strip())
            if old_match:
                results.append({
                    'position': int(old_match.group(1)),
                    'title': old_match.group(2).strip(),
                    'artist': old_match.group(3).strip(),
                    'album': 'Unknown Album',
                    'raw_line': line.strip()
                })
    
    return results

def intelligent_match_selection(results: List[Dict[str, Any]], 
                               target_title: str, target_artist: str = None,
                               preferences: Dict[str, Any] = None) -> Optional[int]:
    """
    Use programmatic scoring to select the best track match from search results.
    
    This base implementation uses algorithmic scoring only. Subclasses can override
    to add LLM intelligence when available.
    
    Args:
        results: Parsed search results  
        target_title: Target song title
        target_artist: Target artist name
        preferences: Search preferences
        
    Returns:
        Position of best match or None
    """
    if not results:
        return None
        
    preferences = preferences or {}
    
    # Get programmatic scores for all results
    programmatic_matches = get_programmatic_scores(results, target_title, target_artist, preferences)
    
    if not programmatic_matches:
        return None
    
    # Use programmatic selection (base implementation)
    best_match = max(programmatic_matches, key=lambda x: x[1])
    max_score = best_match[1]
    winners = [m for m in programmatic_matches if m[1] == max_score]
    return random.choice(winners)[0] if len(winners) > 1 else best_match[0]
#return best_match[0]  # Return position

def get_programmatic_scores(results: List[Dict[str, Any]], target_title_clean: str, 
                           target_artist_clean: str, preferences: Dict[str, Any]) -> List[Tuple[int, float, Dict]]:
    """Get programmatic scores for all results."""
    prefer_live = preferences.get('prefer_live', False)
    prefer_acoustic = preferences.get('prefer_acoustic', False)
    prefer_studio = preferences.get('prefer_studio', False)
    
    scored_matches = []
    #target_title_clean = clean_for_matching(target_title)
    #target_artist_clean = clean_for_matching(target_artist) if target_artist else None
    
    for result in results:
        score = calculate_match_score(
            result, target_title_clean, target_artist_clean, prefer_live, prefer_acoustic, prefer_studio
        )
        
        if score > 0.3:  # Minimum viable match threshold
            scored_matches.append((result['position'], score, result)) # pulling position out just simplifies bein able to do [0] to get position
    
    with open("scored_matches.json", 'w') as f:
        json.dump(scored_matches, f, indent=2)

    return scored_matches
    

def calculate_match_score(result: Dict[str, Any], target_title: str, 
                         target_artist: str, prefer_live: bool, prefer_acoustic: bool, prefer_studio: bool) -> float:
    """
    Calculate a comprehensive match score for a search result.
    
    Considers multiple factors:
    - Title similarity (exact vs fuzzy matching)
    - Artist similarity (if provided)  
    - Live/acoustic/studio preference matching
    - Album context for version detection
    - Quality indicators (explicit, remaster, etc.)
    """
    title_clean = clean_for_matching(result['title'])
    artist_clean = clean_for_matching(result['artist'])
    album_clean = clean_for_matching(result['album'])
    
    # Base title similarity score
    if title_clean == target_title:
        title_score = 1.0  # Exact match ##############
    else:
        title_score = calculate_similarity(title_clean, target_title)
        
        # Special handling for exact matches with different spacing/punctuation
        if normalize_for_exact_match(title_clean) == normalize_for_exact_match(target_title):
            title_score = 1.0
    
    # Artist matching score
    artist_score = 0.0
    if target_artist:
        if artist_clean == target_artist:
            artist_score = 1.0
        else:
            artist_score = calculate_similarity(artist_clean, target_artist)
            # Bonus for partial name matches
            if target_artist in artist_clean or artist_clean in target_artist:
                artist_score = max(artist_score, 0.8)
    
    # Version type detection and scoring
    is_live_track = detect_live_version(result['title'], result['album'])
    is_acoustic_track = detect_acoustic_version(result['title'], result['album'])
    is_studio_track = not is_live_track and not is_acoustic_track  # Studio is default
    
    version_score = 0.0
    
    if prefer_live:
        if is_live_track:
            version_score = 0.3  # Significant bonus for live versions when requested 0.3
        else:
            version_score = -0.1  # Small penalty when live requested but not found
    elif prefer_acoustic:
        if is_acoustic_track:
            version_score = 0.3  # Significant bonus for acoustic versions when requested
        else:
            version_score = -0.1  # Small penalty when acoustic requested but not found
    elif prefer_studio:
        if is_studio_track:
            version_score = 0.2  # Bonus for studio when specifically requested
        else:
            version_score = -0.1  # Penalty when studio requested but not found
    else:
        # Default preference: slightly prefer studio versions
        if is_studio_track:
            version_score = 0.1  # Small bonus for studio
        elif is_live_track:
            version_score = -0.05  # Very small penalty for live when not requested
        else:  # acoustic
            version_score = 0.05  # Neutral for acoustic
    
    # Combine scores
    if target_artist:
        combined_score = (title_score * 0.6) + (artist_score * 0.3) + version_score + 0.1
    else:
        combined_score = (title_score * 0.8) + version_score + 0.2
    
    return max(0.0, combined_score)

def clean_for_matching(text: str) -> str:
    """Clean text for better matching by removing noise and normalizing."""
    if not text:
        return ""
        
    # Remove common annotations
    text = re.sub(r'\s*\(\d{4}\s*remaster(ed)?\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*\(live.*?\)', '', text, flags=re.IGNORECASE) 
    text = re.sub(r'\s*\[explicit\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*-\s*live\s*$', '', text, flags=re.IGNORECASE)
    
    # Normalize whitespace and case
    text = re.sub(r'\s+', ' ', text.lower().strip())
    return text

def detect_live_version(title: str, album: str) -> bool:
    """Detect if a track is a live version based on title and album context."""
    live_patterns = [
        r'\blive\b', r'\bconcert\b', r'live\s+from', r'live\s+at', r'artists\s+den',
        r'live\s+recording', r'concert\s+version'
    ]
    
    text_to_check = f"{title} {album}".lower()
    return any(re.search(pattern, text_to_check) for pattern in live_patterns)

def detect_acoustic_version(title: str, album: str) -> bool:
    """Detect if a track is an acoustic version based on title and album context."""
    acoustic_patterns = [
        r'\bacoustic\b', r'\bunplugged\b', r'acoustic\s+version',
        r'stripped', r'solo\s+acoustic'
    ]
    
    text_to_check = f"{title} {album}".lower()
    return any(re.search(pattern, text_to_check) for pattern in acoustic_patterns)
    
def normalize_for_exact_match(text: str) -> str:
    """Normalize text for exact matching by removing all punctuation and extra spaces."""
    if not text:
        return ""
    
    # Remove all punctuation and normalize spacing
    normalized = re.sub(r'[^\w\s]', '', text.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate simple similarity between two strings."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1, str2).ratio()
    
