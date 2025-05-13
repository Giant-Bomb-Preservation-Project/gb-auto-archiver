# GB Auto-Archiver v1.0 alpha
# part of the Giant Bomb Preservation Society efforts

import requests
import os
import re
import random
import string
import csv
import sys
import json
from tqdm import tqdm
import subprocess
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import time
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import urllib.request

load_dotenv()

def disc(message):
    msg = {'content': message}
    requests.post(f"https://discord.com/api/v9/channels/{CHANNEL}/messages",
                  headers=headers_disc, json=msg)

def mod(message):
    msg = {'content': message}
    requests.post(f"https://discord.com/api/v9/channels/{MODCHANNEL}/messages",
                  headers=headers_disc, json=msg)

def get_content_type(url_here):
    get_cl = urllib.request.urlopen(url_here)
    return get_cl.info()['Content-Length']

def cl_check(hd_url):
    cl = get_content_type(hd_url)
    if cl in cl_pool:
        return True
    cl_pool.append(cl)
    return False

def recursive_lookup(key, dic):
    if key in dic: return dic[key]
    for val in dic.values():
        if isinstance(val, dict):
            found = recursive_lookup(key, val)
            if found is not None:
                return found
    return 'UNCATEGORIZED'

def get_vars(hd_url):
    data = api[i]
    publish_date = recursive_lookup('publish_date', data)[:10]
    video_show = recursive_lookup('title', data)
    guid = recursive_lookup('guid', data)
    name = recursive_lookup('name', data)
    site = recursive_lookup('api_detail_url', data)
    deck = recursive_lookup('deck', data)
    hosts = recursive_lookup('hosts', data)
    premium = recursive_lookup('premium', data)

    base = f"{publish_date}-{video_show}-{name}"
    suffix = '_Premium.mp4' if premium else '.mp4'
    filename = re.sub(':', '', base + suffix).replace(" ", "_").replace('/', "-")
    filepath = os.path.join(dir, filename)
    urls.append(hd_url)
    fns.append(filepath)

    return [{
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

def get_vars_miss():
    data = api[i]
    publish_date = recursive_lookup('publish_date', data)[:10]
    video_show = recursive_lookup('title', data)
    name = recursive_lookup('name', data)
    premium = recursive_lookup('premium', data)

    base = f"{publish_date}-{video_show}-{name}"
    suffix = '_Premium.mp4' if premium else '.mp4'
    filename = re.sub(':', '', base + suffix).replace(" ", "_").replace('/', "-")
    missing_urls.append(filename + '\n')

def create_csv(hd_url):
    vars = get_vars(hd_url)[0]
    for key, val in vars.items():
        if val == 'UNCATEGORIZED' and vars['site'] != 'UNCATEGORIZED':
            mod(f"```diff\n- !! MISSING [{key}] for {vars['guid']} - {vars['filename']}\n```\n{vars['site']}")
    upload.append({
        'identifier': 'gb-' + vars['guid'] + '-ID' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)),
        'file': vars['filepath'],
        'title': vars['name'],
        'description': vars['deck'],
        'subject[0]': 'Giant Bomb',
        'subject[1]': vars['video_show'],
        'hosts': vars['hosts'],
        'creator': 'Giant Bomb',
        'date': vars['publish_date'],
        'collection': 'giant-bomb-archive',
        'mediatype': 'movies',
        'external-identifier': 'gb-guid:' + vars['guid'],
    })
    disc(f"```diff\n>>      [{i}] {vars['filename']}\n```")
    with open(f'{dir}/upload.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=upload[0].keys())
        writer.writeheader()
        writer.writerows(upload)

def download_url(args):
    url, fn = args
    if not url:
        return
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        fn_only = os.path.basename(fn)
        with open(fn, 'wb') as f:
            pbar = tqdm(total=int(r.headers['Content-Length']),
                        desc=f"Downloading {fn_only}",
                        unit='MiB', unit_divisor=1024,
                        unit_scale=True, dynamic_ncols=True,
                        colour='#ea0018', mininterval=1)
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        disc(f"```diff\n+ {fn_only} . . .  DOWNLOADED\n```")

def download_parallel(inputs):
    cpus = max(cpu_count(), 2)
    ThreadPool(cpus - 1).map(download_url, inputs)

def get_hd_url():
    for key in ('hd_url', 'high_url', 'low_url'):
        if key in api[i] and api[i][key]:
            return api[i][key] + ('' if '?exp=' in api[i][key] else f'?api_key={APIKEY}')
    return None

# Discord bot setup
TOKEN = os.getenv('TOKEN')
MODCHANNEL = os.getenv('MODCHANNEL')
CHANNEL = os.getenv('CHANNEL')
headers_disc = {
    "Authorization": f"Bot {TOKEN}",
    "User-Agent": "DiscordBot"
}

disc('```elm\n(  )~~*   [GB Auto Archiver Online]   *~~(  )\n```')
time.sleep(1)

APIKEY = os.getenv('APIKEY')
dir = os.path.dirname(os.path.abspath(__file__))

end_date = date(2024, 10, 11)
current_date = datetime.now() - timedelta(days=95)

while current_date.date() >= end_date:
    # reset state for this date
    upload = []
    missing_urls = []
    cl_pool = []
    urls = []
    fns = []
    show_subtract = 0

    yesterday = current_date.strftime("%Y-%m-%d")
    api_url = (
        f"https://www.giantbomb.com/api/videos/"
        f"?api_key={APIKEY}&format=json"
        f"&field_list=publish_date,video_show,name,hd_url,high_url,low_url,"
        f"guid,deck,hosts,premium,site_detail_url"
        f"&filter=publish_date:{yesterday};00:00:00|{yesterday};23:59:59"
    )

    print(f'>> downloading API dump for {yesterday}')
    disc(f'```elm\n>> Downloading API for {yesterday}\n```')
    time.sleep(0.5)

    try:
        api_request = requests.get(api_url, headers={'User-Agent': 'gb-auto-archiver'})
        api = api_request.json().get('results', [])
    except Exception as e:
        print(f'error: {e}')
        disc(f'```elm\nerror: {e}\n```')
        break

    shows = len(api)
    print(f'>>  {shows} shows found for {yesterday}')
    if shows == 0:
        disc(f'```diff\n+ {shows} new videos found for {yesterday}. Skipping.\n```')
    else:
        disc(f'```diff\n+ {shows} new videos found for {yesterday}\n```')

        for i in range(shows):
            hd_url = get_hd_url()
            if hd_url and not cl_check(hd_url):
                create_csv(hd_url)
            elif not hd_url:
                get_vars_miss()

        disc('```elm\nShows missing download urls:\n```')
        time.sleep(1)
        missing_string = '* No shows were missing URLs *' if not missing_urls else "".join(missing_urls)
        disc(f'```diff\n {missing_string}\n```')

        inputs = list(zip(urls, fns))
        disc('```elm\n[   Downloading shows   ]\n```')
        download_parallel(inputs)

        final_shows = shows - show_subtract
        time.sleep(1)
        disc(f'```elm\n>> UPLOADING {final_shows} shows to Archive.org\n```')
        proc = subprocess.Popen(
            ["ia", "upload", f"--spreadsheet={dir}/upload.csv"],
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
            encoding='utf-8', text=True
        )
        log = open(f'{dir}/ia_upload_{yesterday}.log', 'w', errors='ignore')
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        log.close()

        disc('```diff\n+ UPLOAD COMPLETE\n```')
        time.sleep(1)
        # clean up
        for item in os.listdir(dir):
            if item.endswith((".mp4", ".csv")):
                os.remove(os.path.join(dir, item))

    current_date -= timedelta(days=1)
