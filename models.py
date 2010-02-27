from google.appengine.ext import db

class Batter(db.Model) :
    pid = db.StringProperty()
    first = db.StringProperty()
    last = db.StringProperty()
