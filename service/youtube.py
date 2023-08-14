import sys
sys.path.append('./pytube')
import pytube
from pytube import YouTube

from youtube_search import YoutubeSearch 
from model.song import Song

class Youtube:
    def __init__(self):
        pass

    def search(self, query):
        result = YoutubeSearch(query, max_results=1).to_dict()
        for v in result:
            youtube_url = "https://www.youtube.com" + v['url_suffix']
            yt = YouTube(youtube_url)
            song = Song()
            song.setData(title=yt.title, url=youtube_url, id=id, length=yt.length)
            return song
        