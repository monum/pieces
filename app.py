from flask import Flask, json, g, render_template, request, Response

import os
import pymongo
#from pymongo import MongoClient
from urlparse import urlparse

from bson.son import SON

# Default Config
DEBUG = True

app = Flask(__name__)

###
# Handle database connection
###
MONGO_URL = os.environ.get('MONGOHQ_URL')

if MONGO_URL:
    conn = pymongo.Connection(MONGO_URL)
    db = conn[urlparse(MONGO_URL).path[1:]]
else:
    HOST = 'localhost'
    PORT = 27017
    conn = pymongo.Connection(HOST, PORT)
    db = conn['boston311']

collection = 'boston_requests'
service_requests = db[collection]

###
# Utility functions
###


###
# API Calls
###

@app.route("/daily_count")
def daily_count():
    days = request.args.get("days", 60)
    
    res = service_requests.aggregate([
        {
            "$group": {
                "_id": {
                    "year": { "$year" : "$requested_datetime" },
                    "month": { "$month" : "$requested_datetime" },
                    "day": { "$dayOfMonth" : "$requested_datetime" }
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "_id": -1
            }
        },
        {
            "$limit": days
        }
    ])
    
    return Response(json.dumps(res), mimetype='application/json')
    
###
# Page Rendering
###

@app.route("/")
def dashboard():
    """
        Render the main dashboard view.
    """
    
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.config.from_object(__name__)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
