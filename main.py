import datetime
import os
import requests
import spotipy
from tinydb import TinyDB, Query
from spotipy.oauth2 import SpotifyOAuth

db = TinyDB('./db.json')
Song = Query()

client_id = os.environ['client_id']
client_secret = os.environ['client_secret']
refresh_token = os.environ['refresh_token']
redirect_uri = 'http://localhost:8888/callback'

scope = 'user-read-recently-played'
token = os.environ['auth']

with open('./last_unix.txt', 'r') as f:
    last_time_executed = int(f.read())


def normal():

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=scope,
        redirect_uri=redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
    ))

    results = sp.current_user_recently_played()
    for idx, item in enumerate(results['items']):
        track = item['track']
        print(idx, track['artists'][0]['name'], " – ", track['name'])


def get_token():

    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic {token}'.format(token=token)

    }

    data = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',

    }

    r = requests.post(url, headers=headers, data=data)
    return (access_token := r.json()['access_token'])


def main():

    access_token = get_token()

    with open('./last_unix.txt', 'w') as f:
        currentDateTime = datetime.datetime.now()
        timestamp = datetime.datetime.timestamp(currentDateTime)
        timestamp = int(timestamp * 1000)
        f.write(str(timestamp))

    sp = spotipy.Spotify(auth=access_token)

    results = sp.current_user_recently_played(
        limit=50, after=last_time_executed)
    # Extracting only the relevant bits of data from the json object
    for song in results["items"]:
        name = song["track"]["name"]
        artist = song["track"]["album"]["artists"][0]["name"]
        date = song["played_at"][0:10]
        album = song['track']['album']['name']

        if len(db.search(Song.name == name)) == 0:
            db.insert({
                'name': name,
                'artist': artist,
                'album': album,
                'date': date,
                'n': 1})
        else:
            song_id = db.get(Song.name == name).doc_id
            current_n = db.get(doc_id=song_id)['n']
            db.update({'n': current_n + 1}, doc_ids=[song_id])


if __name__ == '__main__':
    pass
