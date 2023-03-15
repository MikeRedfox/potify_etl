import datetime
import os
import requests
import spotipy
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine, Session, select
from spotipy.oauth2 import SpotifyOAuth
import json


sqlite_file_name = "spotify.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    artist: str
    album: str
    date: str
    n: int

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

def create_table(engine):
    SQLModel.metadata.create_all(engine)
    
def populate_table(engine):
    session = Session(engine)
    with open('db.json') as f:
        data = json.load(f)['_default']

    entries = [ Song(id=idx,
                name=d['name'],
                artist=d['artist'],
                album=d['album'],
                date=d['date'],
                n=d['n']) for idx,d in data.items()]

    for entry in entries:
        session.add(entry)

    session.commit()
    session.close()

def see_table(engine):

    with Session(engine) as session:
        statement = select(Song)
        results = session.exec(statement)
        for song in results:
            print(song)



def main(engine):

    access_token = get_token()
    session = Session(engine)

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


        statement = select(Song).where(Song.name == name)

        try:
            result = session.exec(statement).one()
            result.n += 1
            session.add(result)
            session.commit()
            session.refresh(result)

        except sqlalchemy.exc.NoResultFound:
            new_song = Song(id=idx,
                name=name,
                artist=artist,
                album=album,
                date=date,
                n=1)
            session.add(new_song)
            session.commit()

    session.close()

if __name__ == '__main__':
    main(engine)
