import os
import csv
import pymongo
from urlparse import urlparse

MONGO_URL = os.environ.get('MONGOHQ_URL')

conn = pymongo.Connection(MONGO_URL)

db = conn[urlparse(MONGO_URL).path[1:]]

res = db.boston_requests.aggregate([
    {"$group":
        {"_id": "$service_type", 
         "count": { "$sum": 1 }
        }
    },
    {"$sort": {"count": -1}}
])

with open('taxonomy.csv', 'wt') as f:
    writer = csv.writer(f)
    
    headers = ('service_name', 'count')
    writer.writerow(headers)
    
    for type in res['result']:
        writer.writerow( (type['_id'], type['count']) )
    