# audacity_vinyl_rip_automation
I wrote a simple python/ apple script to automate metadata entry for an export of multiple audio files. 

## Requirements:
 - Runs only on Mac (Apple Script)
 - Python
 - Audacity (with mod-script-pipe module enabled)
 - Internet Connection
 - Dope Records

### Configuration
 - Enable `mod-script-pipe` module in Audacity.  (Audacity => Preferences => Modules)
 - Enable accessibility permissions for your command line application in macOS system preferences.  (Apple Logo => System Preferences => Security & Privacy => Privacy tab => Accessibility)
 - Install `discogs_client` python library.
    ```
        pip install discogs_client
    ```

**IMPORTANT:** while the script is running do not change your cursor (click anywhere) otherwise the apple script will fill out stuff in the wrong areas.

**IMPORTANT2:** The folder you export will be filled with a folder for the album you're exporting. If you repeat this step delete the folder that was created otherwise the apple script will skip the first track because the warning "folder does not exist" will not pop up.

Instructions:

Record your record in audacity.
Set Text Marks at the beginning of each track. 
Find the Record on Discord and copy the release ID. 

Example: 
https://www.discogs.com/de/release/28985929-Various-W133004
ID: 28985929

1. Launch the python script in your terminal
    ```
        python3 audacity_automation.py
    ```
2. Enter the absolute path (/...) where you want your output folders to be generated.
3. Enter the Discogs ID.

Wait for the script to apply click removal, a Low Cut EQ at 20HZ and then for it to export all your tracks. 

DO NOT click anywhere else during the export, because the applescript will relies on being in the right location and it will start filling in different windows if you click somewhere else.

Note: The default settings in your audacity export window will be used. I tested this with MP3 320. Maybe for wav there could be issues with the metadata. 
Note2: Some releases give errors, I haven't figured out why yet. Try with a different one, maybe you find the bug and can help me. 


I am not a professional developer so might be very buggy. But feel free to use xx
