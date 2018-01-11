import base64
import json
import os
import re
import sys
import time
from collections import OrderedDict
from difflib import SequenceMatcher as sm

import pandas as pd
import requests
import simplejson
import six
import yaml

######SETUP#####

#FIXME: Need to also read cmd line args
config_path='/Users/Oakes/Desktop/config.yml'
if os.path.exists(config_path):
    with open(config_path, "r") as yml:
        cfg = yaml.load(yml)
else:
    print("No Configuration Supplied")
    sys.exit(1)
sections = [ section for section in cfg]

#######Authorization#################
#POST https://accounts.spotify.com/api/token
##TODO: Need to cache token and check expiration
##TODO: Need to check response code
def make_authorization_headers(client_id, client_secret):
    auth_header = base64.b64encode(six.text_type(client_id + ':' + client_secret).encode('ascii'))
    return {'Authorization': 'Basic %s' % auth_header.decode('ascii')}

if 'Spotify' in sections:
    sp_cid = cfg['Spotify']['CID']
    sp_secret = cfg['Spotify']['CSECRET']
else:
    #Probably should prompt here instead of exiting
    print('No Spotify Credentials Specified')
    sys.exit(1)

headers = make_authorization_headers(sp_cid, sp_secret)
payload = { 'grant_type': 'client_credentials'}

def oauth(auth_headers, payload):
    r = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=payload)
    if r.status_code == 200:
        authed = r.json()
        return (authed['access_token'], authed['token_type'], authed['expires_in'], time.time())

auth = oauth(headers, payload)
token = auth[0]
now = auth[3]
expire = auth[2]
access_api = {'Authorization': 'Bearer %s' % token.decode('ascii')}

#Get Track Data
df = pd.read_csv('data/my_tracks.csv')
#df = pd.read_csv('data/billboard_lyrics_1964-2015.csv')
#df = pd.read_csv('/Users/Oakes/Google Drive/Projects/data/MSD_SUBSET_ALL.csv')
#df = pd.read_csv('/Users/Oakes/Google Drive/Projects/data/MSD_SUBSET_ALL.csv', encoding='utf-8')
#song_list = [ "%20".join(song.split()) for song in df['Song'].ix[4900:5100] ] 
#only search with primary artist if 'featuring' in artist name. 
#TODO: Should probably format song/artists colummns
def apply(row):
    song = "%20".join(row['Song'].split())
    artist_list = map(lambda word: word.lower(), row['Artist'].split())
    if 'featuring' in artist_list:
        artist = row['Artist'].lower().split("featuring")
        primary_artist = artist[0].strip()
    else:
        primary_artist = "%20".join(row['Artist'].split())
    return (song, primary_artist)
query_list = df.apply(apply, axis=1)

#Might need to modify search pattern to get better coverage track title and artist may not yield best results
def search_url(q):

    return 'https://api.spotify.com/v1/search?q=' + 'track:' + q[0] + '%20artist:' + q[1] + '&type=track&limit=1'

    #return 'https://api.spotify.com/v1/search?q=' + 'track:' + q[0] + '&type=track&limit=1'
print("Grabbing Track Objects")
start = time.time()

#Should probably have some sort of progress bar here. maybe some debugging logic
#for i in query_list:
#    r = requests.get(search_url(i), headers=access_api).json()
#    print(r)

#track_objs = [ requests.get(search_url(i), headers=access_api).json() for i in query_list ]
#TODO: Check cache before performing search
track_objs=[]
err=[]
for i in query_list:
    delta = int(round(time.time() - now))
    if delta >= 3450:
        print('Grab New Token')
        auth = oauth(headers, payload)
        token = auth[0]
        access_api = {'Authorization': 'Bearer %s' % token.decode('ascii')}
        now = time.time()
    r = requests.get(search_url(i), headers=access_api)
    if r.status_code == 200:
        track_objs.append(r.json())
    elif r.status_code == 429:
        timeout = r.headers['Retry-After']
        print(timeout)
        sys.exit(1)
        #time.sleep(timeout)
    else:
        #Take Exception
        #400 -- client has made a http request to port listening for https requests
        #502 -- The server recieved an invalid response upstream
        #Just return empty list if recieve bad error code
        print(r.status_code)
        err.append((i, r.text))
        track_objs.append([])

'''
200	OK - The request has succeeded. The client can read the result of the request in the body and the headers of the response.
201	Created - The request has been fulfilled and resulted in a new resource being created.
202	Accepted - The request has been accepted for processing, but the processing has not been completed.
204	No Content - The request has succeeded but returns no message body.
304	Not Modified. See Conditional requests.
400	Bad Request - The request could not be understood by the server due to malformed syntax. The message body will contain more information; see Error Details.
401	Unauthorized - The request requires user authentication or, if the request included authorization credentials, authorization has been refused for those credentials.
403	Forbidden - The server understood the request, but is refusing to fulfill it.
404	Not Found - The requested resource could not be found. This error can be due to a temporary or permanent condition.
429	Too Many Requests - Rate limiting has been applied.
500	Internal Server Error. You should never receive this error because our clever coders catch them all ... but if you are unlucky enough to get one, please report it to us through a comment at the bottom of this page.
502	Bad Gateway - The server was acting as a gateway or proxy and received an invalid response from the upstream server.
503	Service Unavailable - The server is currently unable to handle the request due to a temporary condition which will be alleviated after some delay. You can choose to resend the request again.        print(i)
'''
#cache the search 
track_objs_file = open('data/track_objects_mytracks.tmp', 'w')
simplejson.dump(track_objs, track_objs_file)
track_objs_file.close

#print("Fetch Time: " + str(start - time.time()))

#[u'items', u'next', u'href', u'limit', u'offset', u'total', u'previous']
#href is the filter used 
#total is the results returned 

#[u'album', u'name', u'uri', u'external_urls', u'popularity', u'explicit', u'preview_url', u'track_number', u'd
#isc_number', u'href', u'artists', u'duration_ms', u'external_ids', u'type', u'id', u'available_markets']

##with open('data/track_objects_MSD.tmp') as f:
#   track_objs = simplejson.load(f)
track_list =[]
q=[]
n=0
qlength=99
null_idex=[]
counter=0

#Need to fetch in batches of max size 100
#FIXME: There is a more efficient way to do this
#TODO: Cache this list for speed
for i,j in enumerate(track_objs):
    time.sleep(.1)
    try:
        if len(j['tracks']['items']) >= 1:
            match_list=OrderedDict()
            artist_list = map(lambda word: word.lower(), df['Artist'].iloc[i].split())
            if 'featuring' in artist_list:
                artist = df['Artist'].iloc[i].lower().split("featuring")
                primary_artist = artist[0].strip()
            else:
                primary_artist = df['Artist'].iloc[i]
            
            if "&" in primary_artist.split():
                primary_artist = primary_artist.split('&')[0].strip()
            #elif "x" in primary_artist.split():
            #    primary_artist = primary_artist.split("x")[0].strip()
            else:
                pass
            match = sm(None, j['tracks']['items'][0]['artists'][0]['name'].lower(), primary_artist.lower()).ratio()
            if match > float(0.60):
                match_list.update({match : j['tracks']['items'][0]})
            
            if len(match_list) == 1:
                mykey = list(match_list.values())[0]
                track_id = mykey['id']
                popularity = mykey['popularity']
                fartist = mykey['artists'][0]['name']
            else:
                #No confident matches
                null_idex.append(i)
                track_id = "NaN"
                popularity = "NaN"
                fartist = "NaN"
        else:
            #The query did not return any results
            null_idex.append(i)
            track_id = "NaN"
            popularity = "NaN"
            fartist = "NaN"
    except:
            #Lazy
            e = sys.exc_info()
            print(e)
            null_idex.append(i)
            track_id = "NaN"
            popularity = "NaN"
            fartist = "NaN"

    if ( n == qlength ) or ( counter == len(track_objs) - 1 ):
        q.append((track_id, popularity, fartist))
        track_list.append(q)
        q=[]
        n=0
        counter+=1
    else:
        q.append((track_id, popularity, fartist))
        n+=1
        counter+=1
    match_list=OrderedDict()
print(len(null_idex))
#Audio Features
#https://api.spotify.com/v1/audio-features/{id}
id_str=""
contents=[]
#Need to add popularity to dataframe
#FIXME: Need generate api token again. Should probably do this with an oauth object
#TODO: Need to add retry logic based upon status_code
auth = oauth(headers, payload)
atoken = auth[0]
aaccess_api = {'Authorization': 'Bearer %s' % atoken.decode('ascii')}
for qitem in track_list:
    for id in qitem:
        if id[0] != 'NaN': 
            id_str = id_str + id[0] + ","
    features = requests.get("https://api.spotify.com/v1/audio-features/?ids=" + id_str, headers=aaccess_api)
    print(features.status_code)
    contents.append(features.json()['audio_features'])
    
    #Need to reset otherwise get a 414 URI too long
    id_str=""

null_row={u'track_href': u'NaN', u'analysis_url': u'NaN', u'energy': u'NaN', u'liveness': u'NaN', u'tempo': u'NaN',
u'speechiness': u'NaN', u'uri': u'NaN', u'acousticness': u'NaN', u'instrumentalness': u'NaN', u'time_signature': u'NaN',
u'danceability': u'NaN', u'key': u'NaN', u'duration_ms': u'NaN', u'loudness': u'NaN', u'valence': u'NaN', u'type': u'NaN', 
u'id': u'NaN', u'mode': u'NaN'}
def indexer(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]
frames=[]
results=[]
z=0


for x in indexer(range(0, len(df.index)), 100):
    results.append(x)
print("Length of Contents")
print(len(contents))
print(contents)
for frame in contents:
    for null_val in null_idex:
        if null_val in results[z]:
            print("Insert null value row into list at " + str(null_val-(z*100)))
            frame.insert(null_val-(z*100), null_row)
    print("Compare")
    print(len(frame))
    print(len(results[z]))
    if len(frame) == len(results[z]):
        try:
                frames.append(pd.DataFrame(frame, index=results[z]))
        except:
                #
                print(results[z])
                for i in frame:
                    print(type(i))

    else:
        print("Frame size error")
    z+=1

audio_df = pd.concat(frames)

#pop_list = [ pop[1] for pop in qitem for qitem in track_list ]
#art_list = [ art[2] for art in qitem for qitem in track_list ]
pop_list=[]
art_list=[]
for i in track_list:
    for pop in i:
        pop_list.append(pop[1])
        art_list.append(pop[2])

dataset = pd.concat([df, audio_df], axis=1)
print(len(track_list))
print(len(pop_list))

dataset['Popularity'] = pop_list
#dataset['Fetched_Artist'] = art_list
#Need to set encoding to utf-8 for fetched artist. Get an unicode encoding error otherwise.
try:
    dataset['Artist'] = df['Artist'].map(lambda x: x.encode('unicode-escape').decode('utf-8'))
except UnicodeDecodeError:
    pass
try:
    dataset['Song'] = df['Song'].map(lambda x: x.encode('unicode-escape').decode('utf-8'))
except UnicodeDecodeError:
    pass
#if 'Lyrics' in dataset.columns:
#    dataset = dataset.drop(['Lyrics'], axis=1)
#dataset['Lyrics'] = df['Lyrics'].map(lambda x: x.encode('unicode-escape').decode('utf-8'))
#df['analysis_url'] = df['analysis_url'].map(lambda x: x.encode('unicode-escape').decode('utf-8'))
#df['uri'] = df['uri'].map(lambda x: x.encode('unicode-escape').decode('utf-8'))
#df['type'] = df['type'].map(lambda x: x.encode('unicode-escape').decode('utf-8'))
#df['track_href'] = df['track_href'].map(lambda x: x.encode('unicode-escape').decode('utf-8'))

print(dataset.columns)
try:
    dataset.to_csv('data/MYTRACKS_processed_Final20170811.csv', encoding='utf-8')
except:
    dataset.to_csv('data/MYTRACKS_processed_Final20170811.csv')
#dataset.to_csv('data/Top100_196412015_processed_Final.csv', encoding='utf-8')
#process_df = pd.read_csv('data/Top100_196412015_processed_Final.csv')
'''
def check(row):
    artist_list = map(lambda word: word.lower(), row['Artist'].split())
    if 'featuring' in artist_list:
        artist = row['Artist'].lower().split("featuring")
        primary_artist = artist[0].strip()
    else:
        primary_artist = row['Artist']
    
    print(primary_artist)

process_df.apply(check, axis=1)
'''