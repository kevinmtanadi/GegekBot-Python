class Reminder:
    def __init__(self, requester, message, datetime):
        self.requester = requester
        self.message = message
        self.datetime = datetime
    
    def toString(self):
        message = "REMINDER!!! -  " + self.datetime + " === " + self.message
        return self.requester, message