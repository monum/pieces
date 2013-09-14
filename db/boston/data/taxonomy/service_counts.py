import os
import json
import csv
import pymongo
from urlparse import urlparse

MONGO_URL = os.environ.get('MONGOHQ_URL')

conn = pymongo.Connection(MONGO_URL)

db = conn[urlparse(MONGO_URL).path[1:]]

res = db.boston_requests.aggregate([
    {"$group":
        {"_id": "$service_name", 
         "count": { "$sum": 1 }
        }
    },
    {"$sort": {"count": -1}}
])

res_json = json.dumps(res)

with open('taxonomy.csv', 'wt') as f:
    writer = csv.writer(f)
    
    headers = ('service_name', 'count')
    writer.writerow(headers)
    
    for type in res_json['result']:
        writer.writerow( (type['_id'], type['count']) )
    