# GB Auto-Archiver v1.0 alpha
# part of the Giant Bomb Preservation Society efforts

# It's import city over here
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

# Load environment
load_dotenv()

## Function to call Discord channel messages
def disc(message):
    msg = {
        'content': message 
    }
    response = requests.post(f"https://discord.com/api/v9/channels/{CHANNEL}/messages", headers=headers_disc, json=msg)
    response

## Function to call Discord mod messages
def mod(message):
    msg = {
        'content': message 
    }
    response = requests.post(f"https://discord.com/api/v9/channels/{MODCHANNEL}/messages", headers=headers_disc, json=msg)
    response

# Function to get filesize of an url
def get_content_type(url_here):
    get_cl = urllib.request.urlopen(url_here)
    return get_cl.info()['Content-Length']

# Function to check for duplicate filesizes
def cl_check(hd_url):

    # Runs function of current URL to find 'content-length' aka filesize
    cl = get_content_type(hd_url)

    # Checks if filesize is in the pool (first run will be 'no' always), if it is present, delete the show
    if cl in cl_pool:
        api.pop([i])
        return True
    else:
        cl_pool.append(cl)
        return False

# Creates the different variables needed for the show being processed
def get_vars(hd_url):
    
    video_show = recursive_lookup('title', api[i])
    publish_date = recursive_lookup('publish_date', api[i])
    guid = recursive_lookup('guid', api[i])
    name = recursive_lookup('name', api[i])
    site = recursive_lookup('api_detail_url', api[i])
    deck = recursive_lookup('deck', api[i])
    hosts = recursive_lookup('hosts', api[i])
    premium = recursive_lookup('premium', api[i])

    # Trim publish date to 10char limit
    publish_date = publish_date[:10]

    # If the show is premium add '_premium.mp4' to filename and add the Filename, Download url, and Filesize info to the 'data_pairs'
    if premium == True:
        filename = re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '_Premium.mp4')).replace(" ", "_").replace('/', "-").replace("\\", "/")
        filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '_Premium.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/")
        urls.append(hd_url)
        fns.append(filepath)

    else:
        filename = re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-").replace("\\", "/")
        filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/") 
        urls.append(hd_url)
        fns.append(filepath)
    
    # Create show variables to send back up into CSV creation, announcements, etc...
    show_vars = [{
        'video_show': video_show,
        'publish_date': publish_date,
        'guid': guid,
        'site': site,
        'deck': deck,
        'hosts': hosts,
        'premium': premium,
        'name': name,
        'filename': filename,
        'filepath': filepath
    }]

    
    return show_vars

# If a show is missing, run through this function to create the info needed to generate info about missing shows
def get_vars_miss():
    
    
    video_show = recursive_lookup('title', api[i])
    publish_date = recursive_lookup('publish_date', api[i])
    guid = recursive_lookup('guid', api[i])
    name = recursive_lookup('name', api[i])
    site = recursive_lookup('api_detail_url', api[i])
    deck = recursive_lookup('deck', api[i])
    hosts = recursive_lookup('hosts', api[i])
    premium = recursive_lookup('premium', api[i])

    # Trim publish date to 10 chars
    publish_date = publish_date[:10]

    # If the show is premium add '_premium.mp4' to filename and add the Filename, Download url, and Filesize info to the 'data_pairs'
    if premium == True:
        filename = re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '_Premium.mp4')).replace(" ", "_").replace('/', "-").replace("\\", "/")
        filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '_Premium.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/")
        missing_urls.append(f'{filename}' + '\n')

    else:
        filename = re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-").replace("\\", "/")
        filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/") 
        missing_urls.append(f'{filename}' + '\n')
    
    # Return these variables as a list to pull from
    show_vars_miss = [{
        'video_show': video_show,
        'publish_date': publish_date,
        'guid': guid,
        'site': site,
        'deck': deck,
        'hosts': hosts,
        'premium': premium,
        'name': name,
        'filename': filename,
        'filepath': filepath
    }]

    
    # Increase show_subtract to calculate missing shows later
    show_subtract = show_subtract + 1

    return show_vars_miss

# Function that creates all of our info vars like filename, path, show names, etc... and then writes them to a CSV
def create_csv(hd_url):
    
    vars = {}
    vars = get_vars(hd_url)
    
    video_show = vars[0]['video_show']
    publish_date = vars[0]['publish_date']
    guid = vars[0]['guid']
    site = vars[0]['site']
    deck = vars[0]['deck']
    hosts = vars[0]['hosts']
    premium = vars[0]['premium']
    name = vars[0]['name']
    filename = vars[0]['filename']
    filepath = vars[0]['filepath']

    for m in vars[0]:
        if vars[0][m] == 'MISSING':
            if not site == 'MISSING':
                mod('```diff' + '\n' + f'- !! MISSING {[m]} for {guid} - {filename}' + '\n' +'```' + '\n' + f'{site}')
            else:
                mod('```diff' + '\n' + f'- !! MISSING {[m]} for {guid} - {filename}' + '\n' +'```')

   

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
    
    print('>> show gathered successfully')
   
    ## Announce show to Discord in the form of the filename
    disc(f'```diff' + '\n' + f'>>      [{i}] {filename}' + '\n' + '```')

    
    ## Write CSV for upload to Archive.org
    with open('upload.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=upload[0].keys())
            writer.writeheader()
            writer.writerows(upload)
            print('>> Saved output to', dir, 'upload.csv')

# Function that opens the multiple download_url functions
def download_parallel(args):
    cpus = cpu_count()
    ThreadPool(cpus - 1).map(download_url, args)
    

# Download function that extracts the tuple to create variables
def download_url(inputs):
    
    url, fn = inputs[0], inputs[1]
    
    # If there's no url, add it to the number of missing show urls
    if url:
   
        # Request the url for download and then write to file
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            
            # Define "filename only" as 'fn' for cleaner announcements
            fn_only = os.path.split(fn)
            
            with open(f'{fn}', 'wb') as f:
                pbar = tqdm(total=int(r.headers['Content-Length']),
                            desc=f"Downloading {fn_only}",
                            unit='MiB',
                            unit_divisor=1024,
                            unit_scale=True,
                            dynamic_ncols=True,
                            colour='#ea0018',
                            mininterval=1
                            )
                
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            # Announce download completion
            disc('```diff' + '\n' + f'+ {fn_only[1]} . . .  DOWNLOADED' + '\n' + '```')
    

def get_hd_url():
    if 'hd_url' not in api[i]:
        hd_url = None

    if 'hd_url' in api[i]:
        hd_url = api[i]['hd_url']

    return hd_url

# Recursive dictionary search for a value
def recursive_lookup(key, dic):
    if key in dic: return dic[key]
    for val in dic.values():
        if isinstance(val, dict):
            a = recursive_lookup(key, val)
            if a is not None: return a
    return 'MISSING'


## Discord bot setup
TOKEN = os.getenv('TOKEN')
MODCHANNEL = os.getenv('MODCHANNEL')
CHANNEL = os.getenv('CHANNEL')

# Set Discord headers for HTTP 
headers_disc = {
    "Authorization": f"Bot {TOKEN}",
    "User-Agent": f"DiscordBot"
}

# GB Quotes
bombs = [
    "I'm a wizard, and that's fucked up",
    "China Don't Care",
    "VINNY!",
    "King of the Garbage Boys",
    "Please don't shake the baby",
    "Remember: • Don't stop for nothin' \n • Hit those motherfuckers \n • Blocking is boring \n • Go for broke \n • Face it straight \n • Triump or die",
    "Anime is for Jerks",
    "Oh look I found a dead bird, that's going straight in my pocket",
    "Do you wanna ride the rollercoaster?",
    "Remember that song we used to play?",
    "Bigger.",
    "How's the running around?",
    "I'd rather be in Barkerville",
    "Matthew Rorie's Alpha Protocol",
    "Fuck 'em",
    "For the past 29 hours powerful and odious forces have attempted to silence me, to box me out of my rightful spot, and to steal my throne",
    "Dave Lang: The king of the garbage boys. This grotesque birdmonster. This monument to everything that is wrong and cruel and dark in this world. This late-game Bloodborne motherfucker. 7ft 3 inches of dog bones and all of them giving me the middle finger. ME! Matt KEssler! America's sweetheart.",
    "What a season. What. A. Season.",
    "Yeah that's right, man! We're gonna go craz nuts. We're gonna go balls-out ESPORTS! It's time for video games. It's time for bikini girls tellin' you what happened this week. And we're gonna fuck shit up on the real.",
    "Headshot City",
    "Letting loose in Butt City®",
    "That's some dope shit",
    "She got a penitentiary body",
    "Enjoy your massage",
    "If I did *this* would that mean anything to you?",
    "Let me tell you somethin' about Bemini Run for the Genesis... That mission based boating game is better than any other mission based boating game, BAR NONE!",
    "I could talk about Peter Molyneux's balls for a long time, but what I'd rather talk about... No, there's nothing I'd rather talk about right now than Peter Molyneux's balls!",
    "Skylanders is probably aimed at kids, but whatever. I am a legal adult who can drink, buy pornography, rent a car, and vote... and I think it's still pretty cool.",
    "This tastes like every other fucking thing we've had on this podcast.",
    "He's like the J.R.R. Tolkien of being shitty!",
    "Nothing gets me excited like a couple of dead bodies.",
    "Poo poo. Poo poo pocket.",
    "That sounded to me like the Rock Band version of sucking your own dick.",
    "Hey everyone it's tuuuuuesdaay!",
    "SPF fuck you!",
    "Did you see what Sheikh Zanzibar did?!",
]
## Create some info holders 4 later baby!
upload = []
missing_urls = []
jsonDump = {}
cl_pool = []
cl = 'x'

# Start at zero missing URLs and add one for each during 'download_url' function
show_subtract = 0

# Create lists for urls and filenames
urls = []
fns = []  

## Set user-agent for GB so it doesn't tell you to fuck off for being basic af
get_header = {
    'User-Agent': 'gb-auto-archiver',
}

## Announce bot online
disc('```elm' + '\n' + '(  )~~*   [GB Auto Archiver Online]   *~~(  )' + '\n' + '```')
time.sleep(1)

## INPUT YOUR API KEY HERE
APIKEY = os.getenv('APIKEY')

## Generate API request link for yesterday's videos only using yesterday's date and the api key provided
today = datetime.now()
yesterday_unformatted = today - timedelta(days=2)
yesterday = str(datetime.strftime(yesterday_unformatted, "%Y-%m-%d"))

# API url template for Giant Bomb API
api_url = f"https://www.giantbomb.com/api/videos/?api_key={APIKEY}&format=json&field_list=publish_date,video_show,name,hd_url,guid,deck,hosts,premium,site_detail_url&filter=publish_date:{yesterday};00:00:00|{yesterday};23:59:59"

## Set current working directory as variable
dir = os.getcwd()

## Announce API downloading
print('>> downloading API dump')
print(' ')
disc('```elm' + '\n' + f'>> Downloading API for {yesterday}' + '\n' + '```')
time.sleep(0.5)

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
time.sleep(0.5)


## Load the API dump into a variable and report number of shows found.
api = api_request.json()

# Trim extra JSON keys
for value in dict(api):
    if value != 'results':
       api.pop(value)

# Move nested 'results' into root of api
for m in api:
    api = api[m]

# Identify how many shows there are total
shows = len(api)

# Announce show number
print(f'>>  {shows} shows found   ')
print(' ')

## If there are no new shows, exit. Otherwise announce number of shows found
if shows == 0:
    disc('```diff' + '\n' + f'+ {shows} new videos found. I\'M OUTTA HERE SUCKERS!' + '\n' + '```')
    sys.exit()
else:
    disc('```diff' + '\n' + f'+ {shows} new videos found' + '\n' + '```')
    

# # Check for duplicate 'content-length' in HTTP headers and delete if dupe (e.g. duplicate files where Free and Premium are the same videos)
# for i in range(len(api)):

#     get_hd_url()

#     if hd_url:

#         if "?exp=" in hd_url:
#             cl_check(hd_url)

#         else:
#             hd_url = (hd_url + f'?api_key={APIKEY}')
#             cl_check(hd_url)

# Gather list of download URLs and show names
for i in tqdm(range(len(api)), desc="Gathering Shows"):

    # Get HD url for current show
    hd_url = get_hd_url()

    if hd_url:

        # If url exists and contains '?exp=' send to be checked and added to the filesize pool, followed by the CSV creation process
        if "?exp=" in hd_url:
            dupe = cl_check(hd_url)
            if not dupe:            
                create_csv(hd_url)
        
        # If url doesnn't contain '?exp=' treat as old school link and just append the api key. Then be sent to have filesize checked and added to the pool as well as CSV creation
        else:
            hd_url = (hd_url + f'?api_key={APIKEY}')
            dupe = cl_check(hd_url)
            if not dupe:            
                create_csv(hd_url)

    ## If the show does not have 'hd_url' defined, skip the process of appending it to the CSV and get the info needed to announce
    if not hd_url:
        get_vars_miss()

# Set the next announcement based on whether or not urls were missing
disc('```elm' + '\n' + 'Shows missing download urls:' + '\n' '```')
time.sleep(1)

# If there were no missing urls, set the report message to be sent out
if not missing_urls:
    missing_string = '* No shows were missing URLs *'

# If there were missing urls, set the report message to be sent out
elif missing_urls:
    missing_string = "\n".join(missing_urls)

# Announce if there were missing URLs to Discord and console
disc('```diff' + '\n' + f' {missing_string}' + '\n' + '```')
print('[   Missing URLs   ]')
print(missing_urls)

# Combine urls and filenames into a tuple
inputs = zip(urls, fns)        

# Sends the 'inputs' tuple to cascade down into the download_parallel function which spawns the multitude of downloaders
disc('```elm' + '\n' + '[   Downloading shows   ]' + '\n' + '```')
download_parallel(inputs)

## Take the total amount of shows and subtract it from the shows with missing URLs to calculate the actual number of shows downloaded.
final_shows = shows - show_subtract        
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
disc(f'```[  ~  {bombin}  ~  ]```')

## Find contents of current directory and delete the files so we can start fresh next time baby!
dir_contents = os.listdir(dir)

print('>> cleaning up')
print(' ')

for item in dir_contents:
   extensions = (".mp4", ".csv")
   if item.endswith(extensions):
       os.remove(os.path.join(dir, item))
