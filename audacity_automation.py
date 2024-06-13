import os
import sys
import time
import json
import discogs_client
import os
import subprocess

#import requests
#from bs4 import BeautifulSoup

# Platform specific file name and file path.
# PATH is the location of files to be imported / exported.

# ========================
# ====   Begin i18n   ====
# ========================
LOCALIZED_STRINGS = {
    'en': {
        'export_button': "Export"
    },
    'de': {
        'export_button': "Exportieren"
    }
}

def get_audacity_language():
    config_file = os.path.expanduser('~/Library/Application Support/audacity/audacity.cfg')
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"The configuration file {config_file} does not exist.")

    language = None
    with open(config_file, 'r') as file:
        lines = file.readlines()
        in_locale_section = False
        for line in lines:
            if line.strip() == '[Locale]':
                in_locale_section = True
            elif in_locale_section:
                if line.startswith('Language='):
                    language = line.split('=')[1].strip()
                    break
    return language

language_code = None
language_code = language_code or get_audacity_language()

def get_localized_string(key,):
    return LOCALIZED_STRINGS.get(language_code, {}).get(key, key)

export_button_text = None
export_button_text = export_button_text or get_localized_string('export_button')
# ======================
# ====   End i18n   ====
# ======================


#PATH = './'
PATH = ""
while not os.path.isdir(PATH):
    PATH = os.path.realpath(input('Path to output folder: '))
    if not os.path.isdir(PATH):
        print('Invalid path. Try again.')
print('Test folder: ' + PATH)

discogs_id = input("Pls provide the discogs ID: ")

# Platform specific constants
if sys.platform == 'win32':
    print("recording-test.py, running on windows")
    PIPE_TO_AUDACITY = '\\\\.\\pipe\\ToSrvPipe'
    PIPE_FROM_AUDACITY = '\\\\.\\pipe\\FromSrvPipe'
    EOL = '\r\n\0'
else:
    print("running on linux or mac")
    PIPE_TO_AUDACITY = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
    PIPE_FROM_AUDACITY = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
    EOL = '\n'


print("Write to  \"" + PIPE_TO_AUDACITY +"\"")
if not os.path.exists(PIPE_TO_AUDACITY):
    print(""" ..does not exist.
    Ensure Audacity is running with mod-script-pipe.""")
    sys.exit()

print("Read from \"" + PIPE_FROM_AUDACITY +"\"")
if not os.path.exists(PIPE_FROM_AUDACITY):
    print(""" ..does not exist.
    Ensure Audacity is running with mod-script-pipe.""")
    sys.exit()

print("-- Both pipes exist.  Good.")

TOPIPE = open(PIPE_TO_AUDACITY, 'w')
print("-- File to write to has been opened")
FROMPIPE = open(PIPE_FROM_AUDACITY, 'r')
print("-- File to read from has now been opened too\r\n")


def send_command(command):
    """Send a command to Audacity."""
    print("Send: >>> "+command)
    TOPIPE.write(command + EOL)
    TOPIPE.flush()


def get_response():
    """Get response from Audacity."""
    line = FROMPIPE.readline()
    result = ""
    while True:
        result += line
        line = FROMPIPE.readline()
        # print(f"Line read: [{line}]")
        if line == '\n':
            return result


def do_command(command):
    """Do the command. Return the response."""
    send_command(command)
    # time.sleep(0.1) # may be required on slow machines
    response = get_response()
    print("Rcvd: <<< " + response)
    return response


def play_record(filename):
    """Import track and record to new track.
    Note that a stop command is not required as playback will stop at end of selection.
    """
    do_command(f"Import2: Filename={os.path.join(PATH, filename + '.wav')}")
    do_command("Select: Track=0")
    do_command("SelTrackStartToEnd")
    # Our imported file has one clip. Find the length of it.
    clipsinfo = do_command("GetInfo: Type=Clips")
    clipsinfo = clipsinfo[:clipsinfo.rfind('BatchCommand finished: OK')]
    clips = json.loads(clipsinfo)
    duration = clips[0]['end'] - clips[0]['start']
    # Now we can start recording.
    do_command("Record2ndChoice")
    print('Sleeping until recording is complete...')
    time.sleep(duration + 0.1)


def export_tracks(filename):
    """Export the new track, and deleted both tracks."""
    do_command("Select: Track=1 mode=Set")
    do_command("SelTrackStartToEnd")
    do_command(f"Export2: Filename={os.path.join(PATH, filename)} NumChannels=1.0")

def import_track(filename):
    """Import track and record to new track.
    Note that a stop command is not required as playback will stop at end of selection.
    """
    do_command(f"Import2: Filename={os.path.join(PATH, filename + '.wav')}")
    do_command("Select: Track=0")
    do_command("SelTrackStartToEnd")

def set_track_marks():
    """ setting the marks where the tracks shall be cut"""
    print("please manually select the marks where the tracks start. (got to the region and press cmd-b)")
    input("When finished: Press any key to continue")


def click_removal_and_eq():
    print("performing Click-Removal and EQ")
    do_command("Select: Track=0")
    do_command("SelTrackStartToEnd")
    do_command('FilterCurve:f0="22,933945" f1="24,657648" FilterLength="8191" InterpolateLin="0" InterpolationMethod="B-spline" v0="-29,866962" v1="-0,066518784"')
    do_command('ClickRemoval:Threshold="200" Width="20"')


def get_discogs_metadata(release_id):
    try:
        # Replace 'YOUR_DISCOGS_USER_TOKEN' with your actual Discogs user token
        client = discogs_client.Client('ExampleApplication/0.1', user_token='iZxvHXuswSUINSmuLqAAMOAgCkCznoKcmjZVqfsU')
        release = client.release(release_id)
        
        metadata = {
            'release_title': release.title,
            'artist': ', '.join(artist.name for artist in release.artists),
            'year': release.year,
            'genre': ', '.join(release.genres),
            'label': ', '.join(label.name for label in release.labels),
            'tracks': []
        }
        
        for track in release.tracklist:
            track_info = {
                'title': track.title,
                'duration': track.duration,
                'artists': ', '.join(artist.name for artist in track.artists) if track.artists else metadata['artist']
            }
            metadata['tracks'].append(track_info)
        
        return metadata
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        sys.exit(1)

click_removal_and_eq()

print("Getting metadata from Discogs")
metadata = get_discogs_metadata(int(discogs_id))

outputfolder = os.path.join(PATH, f"{metadata['artist']}_{metadata['release_title']}")
no_tracks = len(metadata['tracks'])


# Generate the AppleScript dynamically
apple_script_lines = [
    'tell application "Audacity"',
    '    activate',
    '    delay 0.5 -- Ensure Audacity is in focus',
    'end tell',
    '',
    'tell application "System Events"',
    '    tell process "Audacity"',
    '        keystroke "L" using {command down, shift down}',
    '        delay 0.5 -- Adjust delay as needed',
    '        -- Ensure the dialog is focused',
    '        tell window 1',
    f'            keystroke "{outputfolder}"',
    '            delay 0.2 -- Ensure the text is entered properly',
    '            -- Press the "exportieren" button',
    f'            click button "{export_button_text}"',
    '            delay 0.2',
    '        end tell',
    '        keystroke return',
]

# Add the repeated sections for each track
for i, track in enumerate(metadata['tracks']):
    artist = track['artists']
    title = track['title']
    apple_script_lines.extend([
        '        tell window 2',
        '            keystroke tab',
        '            delay 0.2',
        f'            keystroke "{artist}"',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        f'            keystroke "{title}"',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        f'            keystroke "{metadata["release_title"]}"',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        f'            keystroke "{metadata["year"]}"',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        f'            keystroke "{metadata["genre"]}"',
        '            delay 0.2',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        '            keystroke tab',
        '            delay 0.2',
        f'            keystroke "{metadata["label"]}"',
        '            delay 0.5',
        '            keystroke return',
        '            delay 0.2',
        '            keystroke return',
        '            delay 0.2',
        '            keystroke return',
        '        end tell',
        '        delay 1',  # Ensure there's a delay between each export
    ])

apple_script_lines.extend([
    '    end tell',
    'end tell',
])

# Join the AppleScript lines into a single string
apple_script = "\n".join(apple_script_lines)

#print(apple_script)

# Execute the AppleScript using os.system()
os.system(f"osascript -e '{apple_script}'")

print("Wait until Export is over.")
