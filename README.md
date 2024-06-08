# audacity_vinyl_rip_automation
I wrote a simple python/ apple script to automate metadata entry for an export of multiple audio files. 

Requirements:
Runs only on Mac (Apple Script)
Python
Audacity
Internet Connection
Dope Records

Instruction: 

Record your record in audacity.
Set Text Marks at the beginning of each track. 
Find the Record on Discord and copy the release ID. 

Example: 
https://www.discogs.com/de/release/28985929-Various-W133004
ID: 28985929

Launch the python script in your terminal.
Enter the path where you want your output folders to be generated
Enter the Discogs ID 

Wait for the script to apply click removal, a Low Cut EQ at 20HZ and then for it to export all your tracks. 

Note: The default settings in your audacity export window will be used. I tested this with MP3 320. Maybe for wav there could be issues with the metadata. 

I am not a professional developer so might be very buggy. But feel free to use xx

