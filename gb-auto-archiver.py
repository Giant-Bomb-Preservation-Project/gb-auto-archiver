# GB Auto-Archiver v1.0 alpha
# part of the Giant Bomb Preservation Society efforts

import requests
import os
import re
import requests
import random
import string
import csv
import sys
import json
from tqdm import *
import subprocess
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import time
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import urllib.request


load_dotenv()

## Discord bot setup
TOKEN = os.getenv('TOKEN')
CHANNEL = os.getenv('CHANNEL')

headers_disc = {
    "Authorization": f"Bot {TOKEN}",
    "User-Agent": f"DiscordBot"
}

## Function to call Discord channel messages
def disc(message):
    msg = {
        'content': message 
    }
    response = requests.post(f"https://discord.com/api/v9/channels/{CHANNEL}/messages", headers=headers_disc, json=msg)
    response

def get_content_type(url_here):
    get_cl = urllib.request.urlopen(url_here)
    return get_cl.info()['Content-Length']

# Testing variables (BLOCK THESE)
yesterday = '2023-02-03'

## Set user-agent for GB so it doesn't tell you to fuck off for being basic af
get_header = {
    'User-Agent': 'gb-auto-archiver',
}

   
## Announce bot online
disc('```elm' + '\n' + '(  )~~*   [GB Auto Archiver Online]   *~~(  )' + '\n' + '```')
time.sleep(3)

## INPUT YOUR API KEY HERE
APIKEY = os.getenv('APIKEY')

## Generate API request link for yesterday's videos only using yesterday's date and the api key provided
#today = datetime.now()
#yesterday_unformatted = today - timedelta(days=1)
#yesterday = str(datetime.strftime(yesterday_unformatted, "%Y-%m-%d"))


api_url = f"https://www.giantbomb.com/api/videos/?api_key={APIKEY}&format=json&field_list=publish_date,video_show,name,hd_url,guid,deck,hosts,premium&filter=publish_date:{yesterday};00:00:00|{yesterday};23:59:59"

## Create some info holders 4 later baby!
data_pairs = []
upload = []
missing_urls = []
all_shows = []
jsonDump = {}
cl_pool = []
cl = 'x'
first = True

bombs = [
    "I'm a wizard, and that's fucked up",
    "China Don't Care",
    "VINNY!",
    "King of the Garbage Boys",
    "Please don't shake the baby",
    "Remember: • Don't stop for nothin' \n • Hit those motherfuckers \n • Blocking is boring \n • Go for broke \n • Face it straight \n • Triump or die",
    "Anime is for Jerks"
    "Oh look I found a dead bird, that's going straight in my pocket"
    "Do you wanna ride the rollercoaster?"
    "Remember that song we used to play?"
    "Bigger."
    "How's the running around?"
    "I'd rather be in Barkerville"
    "Matthew Rorie's Alpha Protocol"
    "Fuck 'em"
    "For the past 29 hours powerful and odious forces have attempted to silence me, to box me out of my rightful spot, and to steal my throne"
    "Dave Lang: The king of the garbage boys. This grotesque birdmonster. This monument to everything that is wrong and cruel and dark in this world. This late-game Bloodborne motherfucker. 7ft 3 inches of dog bones and all of them giving me the middle finger. ME! Matt KEssler! America's sweetheart."
    "What a season. What. A. Season."
    "Yeah that's right, man! We're gonna go craz nuts. We're gonna go balls-out ESPORTS! It's time for video games. It's time for bikini girls tellin' you what happened this week. And we're gonna fuck shit up on the real."
    "Headshot City"
    "Letting loose in Butt City®"
    "That's some dope shit"
    "She got a penitentiary body"
    "Enjoy your massage"
    "If I did *this* would that mean anything to you?"
    "Let me tell you somethin' about Bemini Run for the Genesis... That mission based boating game is better than any other mission based boating game, BAR NONE!"
    "I could talk about Peter Molyneux's balls for a long time, but what I'd rather talk about... No, there's nothing I'd rather talk about right now than Peter Molyneux's balls!"
    "Skylanders is probably aimed at kids, but whatever. I am a legal adult who can drink, buy pornography, rent a car, and vote... and I think it's still pretty cool."
    "This tastes like every other fucking thing we've had on this podcast."
    "He's like the J.R.R. Tolkien of being shitty!"
    "Nothing gets me excited like a couple of dead bodies."
    "Poo poo. Poo poo pocket."
    "That sounded to me like the Rock Band version of sucking your own dick."
    "Hey everyone it's tuuuuuesdaay!"
    "SPF fuck you!"
    "Did you see what Sheikh Zanzibar did?!"
]
## Set current working directory as variable
dir = os.getcwd()

## Announce API downloading
print('>> downloading API dump')
print(' ')
disc('```elm' + '\n' + f'>> Downloading API for {yesterday}' + '\n' + '```')
time.sleep(1)

# Attempt to download API
try:
    api_request = (requests.get(api_url, headers=get_header))
except Exception as api_error:
    print(f'error: {api_error}')
    disc(f'```elm' + '\n' + f'error: {api_error}' + '\n' + '```')
    sys.exit(1)

# Announce the date of the API downloaded
print(f'>>  API for {yesterday} successfully downloaded')
print(' ')
disc('```diff' + '\n' + f'+ GB API successfully downloaded' '\n' + '```')
time.sleep(1)

## Load the API dump into a variable and report number of shows found.
jsonDump = api_request.json()
shows = len(jsonDump['results'])
print(f'>>  {shows} shows found   ]')
print(' ')

## If there are no new shows, exit. Otherwise announce number of shows found
if shows == 0:
    disc('```diff' + '\n' + f'+ {shows} new videos found. I\'M OUTTA HERE SUCKERS!' + '\n' + '```')
    sys.exit()
else:
    disc('```diff' + '\n' + f'+ {shows} new videos found' + '\n' + '```')
    

## Check for duplicate 'content-length' in HTTP headers and delete if dupe (e.g. duplicate files where Free and Premium are the same videos)
for i in range(len(jsonDump['results'])):
    hd_url = jsonDump['results'][i]['hd_url']
    if hd_url == None:
        continue
    else:
        if "?exp=" in hd_url:
            pass
        else:
            hd_url = (hd_url + f'?api_key={APIKEY}')

    # Runs function of current URL to find 'content-length' aka filesize
    content_length = get_content_type(hd_url)

    # Add the filesize to the current show as a value
    jsonDump['results'][i]['content-length'] = content_length

    # Define the current show's filesize as 'cl'
    cl = jsonDump['results'][i]['content-length']

    # Checks if filesize is in the pool (first run will be 'no' always), if it is present, delete the show
    if cl in cl_pool:
        jsonDump['results'].pop([i])
    else:
        cl_pool.append(cl)


## Append hd_url's + filepath to a 2D array (data_pairs) so they are paired and clean up filenames.
## (e.g. ['http://url.com/vid1.mp4', 'C:/vid1.mp4'], etc...)
## Wrapped in package 'tqdm' to display progress bar in CLI
for i in tqdm(range(len(jsonDump['results'])), desc="Gathering Shows"):

    ## API Variables
    hd_url = jsonDump['results'][i]['hd_url']
    publish_date = jsonDump['results'][i]['publish_date'][:10]
    video_show = jsonDump['results'][i]['video_show']['title']
    name = jsonDump['results'][i]['name']
    guid = jsonDump['results'][i]['guid']
    hosts = jsonDump['results'][i]['hosts']
    deck = jsonDump['results'][i]['deck']
    premium = jsonDump['results'][i]['premium']

    if "content-length" in jsonDump['results'][i]:
        size = jsonDump['results'][i]['content-length']
    else:
        continue

    # Conditions for dealing with URLS
    ## If url = none, empty url
    ## If url contains '?exp=' its a newer url and doesn't need the API key
    ## Otherwise, assume its an old link and add the apikey at the end
    if hd_url == None:
        jsonDump['results'].pop([i])
        continue
    else:
        if "?exp=" in hd_url:
            pass
        else:
            hd_url = (hd_url + f'?api_key={APIKEY}')

    time.sleep(0.1)  
    
    # Since we potentially will skip writing to the data_pairs list if a show 
    last_pos = len(data_pairs)

    # If the show is premium add '_premium.mp4' to filename and add the Filename, Download url, and Filesize info to the 'data_pairs'
    if premium == True:
        filename = re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '_Premium.mp4')).replace(" ", "_").replace('/', "-").replace("\\", "/")
        filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '_Premium.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/")
        data_pairs.append([hd_url])
        data_pairs[last_pos].append((f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '_Premium.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/"))
        data_pairs[last_pos].append(size)

    else:
        filename = re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-").replace("\\", "/")
        filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/") 
        data_pairs.append([hd_url])
        data_pairs[last_pos].append((f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/"))
        data_pairs[last_pos].append(size)

    ## Announce show to Discord in the form of the filename
    disc(f'```diff' + '\n' + f'>>      [{i}] {filename}' + '\n' + '```')
    
    ## If the show does not have 'hd_url' defined, skip the process of appending it to the CSV
    if hd_url == None:
         missing_urls.append(filename + '\n')
         continue
         
    ## Write metadata for Archive.org CSV
    upload.append({
        'identifier': 'gb-' + guid + '-ID' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)),
        'file': filepath,
        'title': name,
        'description': deck,
        'subject[0]': 'Giant Bomb',
        'subject[1]': video_show,
        'hosts': hosts,
        'creator': 'Giant Bomb',
        'date': publish_date.split(' ')[0],
        'collection': 'giant-bomb-archive',
        'mediatype': 'movies',
        'external-identifier': 'gb-guid:' + guid,
        })

print(' ')    
print('>> show gathered successfully')
print(' ')


## Write CSV for upload to Archive.org
with open('upload.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=upload[0].keys())
        writer.writeheader()
        writer.writerows(upload)
        print('>> Saved output to', dir, 'upload.csv')

## Download function
## For each set of [url, filepath] download and save locally.
disc('```elm' + '\n' + '[   Downloading shows   ]' + '\n' + '```')

show_subtract = 0

# Create lists for urls and filenames
urls = []
fns = []

# Append urls and links 
for i in range(len(data_pairs)):
    urls.append(data_pairs[i][0])
    fns.append(data_pairs[i][1])

inputs = zip(urls, fns)

def download_url(inputs):
    url, fn = inputs[0], inputs[1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(f'{fn}', 'wb') as f:
            pbar = tqdm(total=int(r.headers['Content-Length']),
                        desc=f"Downloading {fn}",
                        unit='MB',
                        unit_divisor=1000000,
                        unit_scale=True
                        )
            
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

def download_parallel(args):
    cpus = cpu_count()
    ThreadPool(cpus - 1).imap_unordered(download_url, args)

download_parallel(inputs)

## Single DL Code ## (phased out because GB links expire too quickly now)
# for i in range(len(jsonDump['results'])):

#     # Define url and filename (fn) as the pairs of data from each array.
#     # Kind of garbage way to do it but it's in place from when I was trying to get multiple downloads at once working.  
#     url, fn, clength = data_pairs[i][0], data_pairs[i][1], data_pairs[i][2]

#     # If there's no url, add it to the number of missing show urls
#     if url == None:
#         show_subtract = +1
#         continue

#     # Define "filename only" as 'fn' for cleaner announcements
#     fn_only = os.path.split(fn)

#     # Request the url for download and then write to file
#     with requests.get(url, stream=True) as r:
#         r.raise_for_status()
#         with open(f'{fn}', 'wb') as f:
#             pbar = tqdm(total=int(r.headers['Content-Length']),
#                         desc=f"Downloading {fn}",
#                         unit='MB',
#                         unit_divisor=1000000,
#                         unit_scale=True
#                         )
            
#             for chunk in r.iter_content(chunk_size=1024):
#                 if chunk:
#                     f.write(chunk)
#                     pbar.update(len(chunk))

#     # Announce download completion
#     disc('```diff' + '\n' + f'+ {fn_only[1]}...  DOWNLOADED' + '\n' + '```')
#     print(f'{fn_only[1]} downloaded')

## Take the total amount of shows and subtract it from the shows with missing URLs to calculate the actual number of shows downloaded.
final_shows = shows - show_subtract        
time.sleep(1)

# Set the next announcement based on whether or not urls were missing
disc('```elm' + '\n' + 'Shows missing download urls:' + '\n' '```')
time.sleep(1)
if not missing_urls:
    missing_string = '* No shows were missing *'
elif missing_urls:
    missing_string = "\n".join(missing_urls)

# Announce if there were missing URLs to Discord and console
disc('```diff' + '\n' + f' {missing_string}' + '\n' + '```')
print('[   Missing URLs   ]')
print(missing_urls)

time.sleep(1)

# Announce upload process
print(f'>>  Uploading {final_shows} shows to Archive.org')
print(' ')
disc('```elm' + '\n' + f'>> UPLOADING {final_shows} shows to Archive.org' + '\n' + '```')

## Upload to Archive.org! ##
# Run IA python script and print the output to the current console as well as logging it to a file
proc = subprocess.Popen(["ia", "upload", f"--spreadsheet={dir}/upload.csv"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, encoding='utf-8', text=True)
logfile = open(f'{dir}\ia_upload_{yesterday}.log', 'w', errors='ignore')
for line in proc.stdout:
    sys.stdout.write(line)
    logfile.write(line)
logfile.close()

## Announce upload complete
print(">> Uploading complete")
disc('```diff' + '\n' + f'+ UPLOAD COMPLETE' + '\n' + '```')
time.sleep(1)

bombin = random.choice(bombs)
disc(f'```{bombin}```')

## Find contents of current directory and delete the files so we can start fresh next time baby!
dir_contents = os.listdir(dir)

print('>> cleaning up')
print(' ')

for item in dir_contents:
   extensions = (".mp4", ".csv")
   if item.endswith(extensions):
       os.remove(os.path.join(dir, item))
