import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
import models

class BatterLoader(bulkloader.Loader) :
    def __init__(self) :
        bulkloader.Loader.__init__(self, 'Batter',
                                   [('pid', str),
                                    ('first', str),
                                    ('last', str)])

loaders = [BatterLoader]
