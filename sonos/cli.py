#!bin/python

'''Click-based command line script to control sonos.
There are a bunch of aliases in .bashrc'''

import click
from . import sonos_actions
from .get_lyrics import get_lyrics #uses genius.com
import random
from .config import master_speaker

def bold(text):
    return "\033[1m" + text + "\033[0m"

def colorize(text, color):
    if color == 'red':
        return "\033[31m" + text + "\033[0m"
    elif color == 'green':
        return "\033[32m" + text + "\033[0m"
    elif color == 'magenta':
        return "\033[35m" + text + "\033[0m"
    else:
        return text

class Config():
    def __init__(self):
        pass

pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option("-m", "--master", help="The name of the master speaker")
@click.option("-v", "--verbose", is_flag=True, help="Display additional information")
@pass_config
def cli(config, master, verbose):
    '''Sonos command line app; master defaults to "Office2"; verbose defaults to False '''
    config.verbose = verbose
    if not master:
        sonos_actions.master = sonos_actions.set_master(master_speaker)
        #master = "Office2"
    else:
        sonos_actions.master = sonos_actions.set_master(master)

    if verbose:
        click.echo(f"Master speaker is {master}: {sonos_actions.master.ip_address}")

@cli.command()
@click.argument('station', default="wnyc", required=False)
def playstation(station):
    """Play a station (currently a pandora station (eg 'Neil Young') or 'wnyc'
    The default is 'wnyc'"""
    sonos_actions.play_station(station)

@cli.command()
@click.argument('track', type=click.STRING, required=True, nargs=-1)
def playtrack(track):
    '''[play] Play a track -> sonos playtrack harvest by neil young"'''
    msg = sonos_actions.play_track(" ".join(track))
    click.echo(msg)

# used by claude_music 
@cli.command()
@click.argument('track', type=click.STRING, required=True, nargs=-1)
def searchtrack(track):
    '''[search] Play a track -> sonos playtrack harvest by neil young"'''
    msg = sonos_actions.search_track(" ".join(track))
    click.echo(msg)

@cli.command()
@click.argument('album', type=click.STRING, required=True, nargs=-1)
def searchalbum(album):
    '''Search for an album'''
    msg = sonos_actions.search_album(" ".join(album))
    click.echo(msg)

# used by claude_music 
@cli.command()
@click.argument('position', type=int, required=True, nargs=1)
def select(position):
    '''select a track or album from an onscreen list'''
    msg = sonos_actions.select_from_list(position)
    click.echo(msg)

@cli.command()
@click.argument('positions', type=int, required=True, nargs=-1)
def selectm(positions):
    '''select a track or album from an onscreen list'''
    print(positions)
    for p in positions:
        msg = sonos_actions.select_from_list(p)
    click.echo(msg)

@cli.command()
@click.argument('track', type=click.STRING, required=True, nargs=-1)
def searchtrack2(track):
    '''[search] Play a track -> sonos playtrack harvest by neil young"'''
    msg = sonos_actions.search_track2(" ".join(track))
    click.echo(msg)

@cli.command()
def louder():
    '''[[l]ouder] Turn the volume higher'''
    sonos_actions.turn_volume("louder")

@cli.command()
def quieter():
    '''[[q]ieter] Turn the volume lower'''
    sonos_actions.turn_volume("quieter")

@cli.command()
def pause():
    '''Pause playback'''
    sonos_actions.playback('pause')

@cli.command()
def resume():
    '''Resume playback'''
    sonos_actions.playback('play')

@cli.command()
def play_pause():
    '''Play Pause'''
    sonos_actions.play_pause()

@cli.command()
def next():
    '''Next track'''
    sonos_actions.playback('next')

@cli.command()
def trackinfo():
    '''Detailed info for the currently playing track'''
    track_info = sonos_actions.current()
    if track_info:
        msg = "\n"+"\n".join([f"{bold(colorize(x, 'magenta'))}: {colorize(y, 'bold')}" for x,y in track_info.items()])+"\n"
    else:
        msg = "Nothing appears to be playing"

    click.echo(msg)

@cli.command()
def what():
    '''Image, title, artist and album for the currently playing track'''
    track = sonos_actions.current_track_info(False) #False = don't return text; return a dictionary

    if track:
        click.secho("\nartist: ", nl=False, fg='cyan', bold=True)
        click.echo(f"{track['artist']}")
        click.secho("title: ", nl=False, fg='cyan', bold=True)
        click.echo(f"{track['title']}")
        click.secho("album: ", nl=False, fg='cyan', bold=True)
        click.echo(f"{track['album']}\n")
    else:
        click.secho("Nothing appears to be playing! ", nl=False, fg='red', bold=True)

@cli.command()
def showqueue():
    '''[showq] Show the queue and the currently playing track'''
    lst = sonos_actions.list_queue()
    if not lst:
        click.echo("The queue is empty")
        return
    else:
        q = list(enumerate(lst, 1))

        # below marks the currently playing track with a red music note.
        track_info = sonos_actions.current()
        if track_info:
            cur_pos = int(track_info['playlist_position'])
            q[cur_pos-1][1]['title'] =f"{colorize("🎵", 'red')}" + q[cur_pos-1][1]['title']

        for num,track in q:
            title, artist, album = track.values()
            s  = f"{title} - {colorize(artist, 'green')} - {colorize(album, 'red')}"
            click.echo(f"{num}. {s}")

@cli.command()
def clearqueue():
    '''[clearq] Clear the queue'''
    sonos_actions.clear_queue()

@cli.command()
def lyrics():
    '''Retrieve lyrics for the current track'''
    title = sonos_actions.current()['title']
    artist = sonos_actions.current()['artist']
    lyrics = get_lyrics(artist, title)
    click.secho(f"\n{title} by {artist}", fg='cyan', bold=True, nl=False)
  
    if not lyrics:
        click.echo("Couldn't retrieve lyrics")
    else:
        click.echo(lyrics)

@cli.command()
@click.argument('artists', type=click.STRING, required=True, nargs=-1)
def shuffle(artists):
    '''Shuffle the songs from one or more artists: sonos shuffle "patty griffin" "neil young" "aimee mann"'''
    artists = " ".join(artists)
    artists.replace('\\', '') # added 07092023 but also have to add unidecode to sonos_actions2.py shuffle 
    msg = sonos_actions.shuffle(artists)
    click.echo(msg)

@cli.command()
@click.argument('artist', type=click.STRING, required=True, nargs=-1)
def tracks(artist):
    '''List the tracks from an artist'''
    artist = " ".join(artist)
    result = sonos_actions.list_(artist)
    count = len(result)
    msg = ""
    if count:
        msg += f"Track count for {artist.title()} was {count}:\n"
        track_list = result.docs
    else:
        msg += f"I couldn't find any tracks for {artist.title()}\n"
        return
    titles = [t.get('title', '')+'-'+t.get('artist', '') for t in track_list]
    title_list = "\n".join([f"{t[0]}. {t[1]}" for t in enumerate(titles, start=1)])
    msg += title_list
    click.echo(msg)
    z = input("Which tracks? ")
    if not z:
        return
    zz = z.split(',')
    uris = [track_list[int(x)-1]['uri'] for x in zz]
    titles = [track_list[int(x)-1]['title'] for x in zz]
    click.echo("\n".join(titles))
    sonos_actions.play(False, uris)

@cli.command()
@click.argument('album', type=click.STRING, required=True, nargs=-1)
#@click.option('-a', '--artist', help="Artist to help find album to be played")
#def playalbum(album, artist=None):
def playalbum(album):
    '''Play an album -> sonos playalbum "A man needs a maid" -a "neil young"'''
    msg = sonos_actions.play_album(" ".join(album))
    click.echo(msg)

@cli.command()
@click.argument('pos', type=click.INT, required=True)
@pass_config
def playfromqueue(config, pos):
    '''[playq] Play track from queue position - top of list is position #1'''
    lst = sonos_actions.list_queue()
    if 0 < pos <= len(lst):
        sonos_actions.play_from_queue(pos-1)
        if config.verbose:
            click.echo(f"Playing track {pos}: {lst[pos-1]}")
    else:
        click.echo(f"{s} is out of the range of the queue")

@cli.command()
@click.argument('user_request', type=str, required=True, nargs=-1)
def smartplay(user_request):
    '''"smartplay burgundy shoes by patty griffin" '''
    # note the title and artist are not "cleaned" - that happens later
    title, artist, preferences = sonos_actions.parse_play_request(" ".join(user_request)).values()
    d = sonos_actions.generate_query_and_do_search(title, artist, preferences)
    parsed_results = sonos_actions.parse_search_results(d["results"])
    position = sonos_actions.intelligent_match_selection(parsed_results, d["title"], d["artist"], d["preferences"])
    sonos_actions.play_track_from_search_list(position)
    click.echo(parsed_results[position-1])
    click.echo(title+artist)
