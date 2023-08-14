class Song:
    def __init__(self):
        self.id = None
        self.title = None
        self.url = None
        self.length = None
        self.requester = None
    
    def setData(self, title=None, url=None, id=None, length=None, requester=None):
        if title != None:
            self.title = title
        
        if url != None:
            self.url = url
        
        if id != None:
            self.id = id
        
        if length != None:
            self.length = length
        
        if requester != None:
            self.requester = requester

class FavoriteSong:
    def __init__(self, requester, songs):
        self.requester = requester
        self.songs = songs