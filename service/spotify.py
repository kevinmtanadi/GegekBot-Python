import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

class Spotify:
    def __init__(self):
        client_credentials_manager = SpotifyClientCredentials(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
    def getSpotifyTitle(self, url):
        track_id = track_id = url.split('/')[-1].split('?')[0]
        res = 'spotify:track:' + track_id
        track = self.sp.track(res)
        title = track['name']
        artist = track['artists'][0]['name']

        return title + " - " + artist