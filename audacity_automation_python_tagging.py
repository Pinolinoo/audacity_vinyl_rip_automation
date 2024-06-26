import os
import sys
import time
import json
import discogs_client
import subprocess
import mutagen
from mutagen.easyid3 import EasyID3
from datetime import datetime

EasyID3.RegisterTextKey('comment', 'COMM')
start_time = time.time()

# ========================
# ====   Begin i18n   ====
# ========================
LOCALIZED_STRINGS = {
    'en': {
        'export_button': 'Export',
        'metadata_window': 'Edit Metadata Tags'
    },
    'de': {
        'export_button': 'Exportieren',
        'metadata_window': 'Tag-Metadaten bearbeiten'
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
metadata_window_text = None
metadata_window_text = metadata_window_text or get_localized_string('metadata_window')
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


print("Getting metadata from Discogs")
metadata = get_discogs_metadata(int(discogs_id))

# TODO: Can probably be removed now that we aren't interpolating metadata into
#   apple script
import re

def remove_parentheses(content):
    if isinstance(content, dict):
        return {key: remove_parentheses(value) for key, value in content.items()}
    elif isinstance(content, list):
        return [remove_parentheses(element) for element in content]
    elif isinstance(content, str):
        return re.sub(r'\s*\(\d+\)', '', content).strip()
    else:
        return content

metadata = remove_parentheses(metadata)

print(metadata)
# ---- END TODO ----

click_removal_and_eq()

outputfolder = os.path.join(PATH, f"{metadata['artist']}_{metadata['release_title']}")
no_tracks = len(metadata['tracks'])

# Function to escape " ' "
def escape_double_quotes(text):
    text =  text.replace("'", "")
    text =  text.replace('"', '')
    return text


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
    f'            keystroke "{escape_double_quotes(outputfolder)}"',
    '            delay 0.2 -- Ensure the text is entered properly',
    '            -- Press the "exportieren" button',
    f'            click button "{export_button_text}"',
    '            delay 0.2',
    '        end tell',
]

# Add the repeated sections for each track
for i, track in enumerate(metadata['tracks']):
    apple_script_lines.extend([
        f"""
            delay 1
            if exists window "{metadata_window_text}" then
                tell application "System Events" to tell process "Audacity" to tell button "OK" of window "{metadata_window_text}" to perform action "AXPress"
            end if
        """
    ])

apple_script_lines.extend([
    '    end tell',
    'end tell',
])

# Join the AppleScript lines into a single string
apple_script = "\n".join(apple_script_lines)


# Execute the AppleScript using os.system()
os.system(f"osascript -e '{apple_script}'")


# Wait until output directory has all files
print("Waiting for file export to finish", end='')
timeout_timer = 0
last_file_count = 0
while True:
    files = [
        f for f in os.listdir(outputfolder)
        if os.path.isfile(os.path.join(outputfolder, f)) and
        os.path.getctime(os.path.join(outputfolder, f)) >= start_time
    ]

    if len(files) > last_file_count:
        last_file_count = len(files)
        timeout_timer = 0
    else:
        timeout_timer += 1

    if timeout_timer >= 20:
        print()
        print(("ERROR: Exported file count does not match discogs track count. "
              "Please check the contents of your export folder and/or the number "
              "of text labels in the Audacity project and try again."))
        sys.exit(1)

    if len(files) == no_tracks:
        break
    else:
        print(".", end='')
        sys.stdout.flush()

    time.sleep(1)

print()
print("Writing tags and file names...")

def get_mp3_files(directory):
    """Retrieve all mp3 files in the directory and sort them by creation date."""
    files = []
    for file in os.listdir(directory):
        if file.endswith(".mp3") and os.path.getctime(os.path.join(outputfolder, file)) >= start_time:
            file_path = os.path.join(directory, file)
            creation_time = os.path.getctime(file_path)
            files.append((file_path, creation_time))
    files.sort(key=lambda x: x[1])  # Sort by creation time
    return [file[0] for file in files]

def update_metadata(file_path, track, i):
    audio = EasyID3(file_path)
    audio['artist'] = escape_double_quotes(track['artists'])
    audio['title'] = escape_double_quotes(track['title'])
    audio['album'] = escape_double_quotes(metadata['release_title'])
    audio['date'] = str(metadata['year'])
    audio['genre'] = escape_double_quotes(metadata['genre'])
    audio['comment'] = escape_double_quotes(metadata['label'])
    audio['tracknumber'] = str(i + 1)
    audio.save()

def build_filenames_from_discogs_data():
    filenames = []
    for i, track in enumerate(metadata['tracks']):
        formatted_index = f"{i + 1:02}"
        filename = f"{formatted_index} {track['artists']} - {track['title']}"
        filenames.append(filename)
    return filenames

new_names = build_filenames_from_discogs_data()
mp3_files = get_mp3_files(outputfolder)

if len(mp3_files) != len(metadata['tracks']):
    print("The number of MP3 files does not match the number of metadata entries.")
    sys.exit(1)

try:
    for i, (file_path, track, new_file_name) in enumerate(zip(mp3_files, metadata['tracks'], new_names)):
        update_metadata(file_path, track, i)
        _, file_extension = os.path.splitext(file_path)
        new_file = os.path.join(outputfolder, new_file_name + file_extension)
        os.rename(file_path, new_file)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print(f'Files successfully processed to {outputfolder}')
print('Done.')
