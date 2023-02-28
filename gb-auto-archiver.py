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
from tqdm import tqdm
import subprocess
import time
import time
from datetime import datetime, timedelta, date

## Discord bot setup
TOKEN = 'BOT_TOKEN_HERE'
channel = CHANNEL_ID_HERE

headers_disc = {
    "Authorization": f"Bot {TOKEN}",
    "User-Agent": f"DiscordBot"
}

## Function to call Discord channel messages
def disc(message):
    msg = {
        'content': message 
    }
    response = requests.post(f"https://discord.com/api/v9/channels/{channel}/messages", headers=headers_disc, json=msg)
    response

# Testing variables (BLOCK THESE)
yesterday = '2023-01-23'


## Set user-agent for GB so it doesn't tell you to fuck off for being basic af
get_header = {
    'User-Agent': 'gb-auto-archiver',
}

   
## Announce bot online
disc('```elm' + '\n' + '(  )~~*   [GB Auto Archiver Online]   *~~(  )' + '\n' + '```')
time.sleep(3)

## INPUT YOUR API KEY HERE
apikey = 'API_KEY_HERE' 

## Generate API request link for yesterday's videos only using yesterday's date and the api key provided
#today = datetime.now()
#yesterday_unformatted = today - timedelta(days=1)
#yesterday = str(datetime.strftime(yesterday_unformatted, "%Y-%m-%d"))


api_url = f"https://www.giantbomb.com/api/videos/?api_key={apikey}&format=json&field_list=publish_date,video_show,name,hd_url,guid,deck,hosts&filter=publish_date:{yesterday};00:00:00|{yesterday};23:59:59"

## Create some info holders 4 later baby!
data_pairs = []
upload = []
missing_urls = []
all_shows = []
jsonDump = {}

## Set current working directory as variable
dir = os.getcwd()

## Download yesterday's API dump
print('>> downloading API dump')
print(' ')
disc('```elm' + '\n' + f'>> Downloading API for {yesterday} (yesterday)' + '\n' + '```')
time.sleep(3)

try:
    api_request = (requests.get(api_url, headers=get_header))
except Exception as api_error:
    print(f'error: {api_error}')
    disc(f'```elm' + '\n' + f'error: {api_error}' + '\n' + '```')
    sys.exit(1)
print(f'>>  API for {yesterday} successfully downloaded')
print(' ')
disc('```diff' + '\n' + f'+ GB API successfully downloaded' '\n' + '```')
time.sleep(3)

## Load the API dump into a variable and report number of shows found.
jsonDump = api_request.json()
shows = len(jsonDump['results'])
print(f'>>  {shows} shows found   ]')
print(' ')

if shows == 0:
    disc('```diff' + '\n' + f'+ {shows} new videos found. I\'M OUTTA HERE SUCKERS!' + '\n' + '```')
    sys.exit()
else:
    disc('```diff' + '\n' + f'+ {shows} new videos found' + '\n' + '```')
    

## Append hd_url's + filepath to a 2D array (data_pairs) so they are paired and clean up filenames.
## (e.g. ['http://url.com/vid1.mp4', 'C:/vid1.mp4'], etc...)
## Wrapped in package 'tqdm' to display progress bar in CLI
pbar = tqdm(range(len(jsonDump['results'])))
for i in pbar:
    
    ## API Variables
    hd_url = jsonDump['results'][i]['hd_url']
    publish_date = jsonDump['results'][i]['publish_date'][:10]
    video_show = jsonDump['results'][i]['video_show']['title']
    name = jsonDump['results'][i]['name']
    guid = jsonDump['results'][i]['guid']
    hosts = jsonDump['results'][i]['hosts']
    deck = jsonDump['results'][i]['deck']
    
    pbar.set_description(f"Gathering Shows")
    time.sleep(0.2)
    data_pairs.append([])
    data_pairs[i].append(hd_url)
    data_pairs[i].append((f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/"))
    filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/")
    filename = re.sub(':', '', (publish_date + '-' + video_show + '-' + name + '.mp4')).replace(" ", "_").replace('/', "-").replace("\\", "/")
    print(f'{filename}')
    all_shows.append(filename)

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
for i in tqdm(range(len(jsonDump['results'])), desc=f"Downloading {shows} Shows"):
    url, fn = data_pairs[i][0], data_pairs[i][1]
    if ".mp4" in url:
        url = (url + f'?api_key={apikey}')
    fn_only = os.path.split(fn)
    if url == None:
        show_subtract = +1
        continue
    r = requests.get(url, headers=get_header)
    disc('```diff' + '\n' + f'+ {fn_only[1]}......  DOWNLOADED' + '\n' + '```')
    open(f'{fn}', "wb").write(r.content)

## Take the total amount of shows and subtract it from the shows with missing URLs to calculate the actual number of shows downloaded.
final_shows = shows - show_subtract        
time.sleep(3)

## Announce shows with missing URLs
disc('```elm' + '\n' + 'Shows missing download urls:' + '\n' '```')
time.sleep(1)
if not missing_urls:
    missing_string = '* No shows were missing *'
elif missing_urls:
    missing_string = "\n".join(missing_urls)
disc('```diff' + '\n' + f'- {missing_string}' + '\n' + '```')
time.sleep(2)

## Upload to Archive.org!
print(f'>>  Uploading {final_shows} shows to Archive.org')
print(' ')
disc('```elm' + '\n' + f'>> UPLOADING {final_shows} shows to Archive.org' + '\n' + '```')

proc = subprocess.Popen(["ia", "upload", f"--spreadsheet={dir}/upload.csv"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE, text=True)
logfile = open(f'{dir}\ia_upload_{yesterday}.log', 'w', errors='ignore')
for line in proc.stdout:
    sys.stdout.write(line)
    logfile.write(line)
logfile.close()

print(">> Uploading complete")
disc('```diff' + '\n' + f'+ UPLOAD COMPLETE' + '\n' + '```')
    # disc('```diff' + '\n' + f'Errors: {upload_ia.stderr}' + '\n' + '```')
time.sleep(3)

## Find contents of current directory and delete the files so we can start fresh next time baby!
dir_contents = os.listdir(dir)

print('>> cleaning up')
print(' ')

for item in dir_contents:
   extensions = (".mp4", ".csv")
   if item.endswith(extensions):
       os.remove(os.path.join(dir, item))

## Print shows missing urls for log
print('[   Missing URLs   ]')
print(missing_urls)