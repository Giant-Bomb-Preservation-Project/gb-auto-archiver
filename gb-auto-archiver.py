# GB Auto-Archiver v.0.1 alpha

import requests
from datetime import date
# import json
import os
import re
import requests
import random
import string
import csv

# Testing variables (BLOCK THESE)
# today = '2023-02-13' 
# f = open('gb.json')


# Set user-agent for GB so it doesn't tell you to fuck off for being basic af
get_header = {
    'User-Agent': 'gb-auto-archiver',
}

# INPUT YOUR API KEY HERE
apikey = 'PASTE_API_KEY_HERE' 

# Generate API request link for today's videos only
today = date.today()
api_url = f"https://www.giantbomb.com/api/videos/?api_key={apikey}&format=json&field_list=publish_date,video_show,name,hd_url,guid,deck,hosts&filter=publish_date:{today};00:00:00|{today};23:59:59"

jsonDump = {}

# Download today's API dump
api_request = requests.get(api_url, headers=get_header)
print(f'downloading {today} API dump' )

# Load the API dump into a variable 
jsonDump = api_request.json()

# Create arrays 4 later baby!
data_pairs = []
upload = []

# Set current working directory as variable
dir = os.getcwd()


# Append hd_url's + filepath to a 2D array (data_pairs) so they are paired and clean up filenames.
# (e.g. ['http://url.com/vid1.mp4', 'C:/vid1.mp4'], etc...)
for i in range(len(jsonDump['results'])):
    data_pairs.append([])
    data_pairs[i].append(jsonDump['results'][i]['hd_url'])
    data_pairs[i].append((f'{os.getcwd()}' + '\\' + re.sub(':', '', (jsonDump['results'][i]['publish_date'][:10] + '-' + jsonDump['results'][i]['video_show']['title'] + '-' + jsonDump['results'][i]['name'] + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/"))
    filepath = (f'{os.getcwd()}' + '\\' + re.sub(':', '', (jsonDump['results'][i]['publish_date'][:10] + '-' + jsonDump['results'][i]['video_show']['title'] + '-' + jsonDump['results'][i]['name'] + '.mp4')).replace(" ", "_").replace('/', "-")).replace("\\", "/")

# Write metadata for Archive.org CSV
    upload.append({
                  'identifier': 'gb-' + jsonDump['results'][i]['guid'] + '-ID' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)),
                  'file': filepath,
                  'title': jsonDump['results'][i]['name'],
                  'description': jsonDump['results'][i]['deck'],
                  'subject[0]': 'Giant Bomb',
                  'subject[1]': jsonDump['results'][i]['video_show']['title'],
                  'hosts': jsonDump['results'][i]['hosts'],
                  'creator': 'Giant Bomb',
                  'date': jsonDump['results'][i]['publish_date'].split(' ')[0],
                  'collection': 'giant-bomb-archive',
                  'mediatype': 'movies',
                  'external-identifier': 'gb-guid:' + jsonDump['results'][i]['guid'],
                })
    
# Write CSV for upload to Archive.org
with open('upload.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=upload[0].keys())
        writer.writeheader()
        writer.writerows(upload)
        print('  Saved output to', dir)


# Download function
# For each set of [url, filepath] download and save locally.
def download_url(args):
    for i in range(len(jsonDump['results'])):
        url, fn = args[i][0], args[i][1]
        if url == None:
            continue
        r = requests.get(url, headers=get_header)
        open(f'{fn}', "wb").write(r.content)

download_url(data_pairs)

# Upload to Archive.org!
os.system(f'cmd /k "ia upload --spreadsheet={dir}/upload.csv"')

# Find contents of current directory and delete the files so we can start fresh next time baby!
dir_contents = os.listdir(dir)

for item in dir_contents:
    if item.endswith(".csv", ".mp4"):
        os.remove(os.path.join(dir, item))