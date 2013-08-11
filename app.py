from flask import Flask, json, g, render_template, request, Response

import os
import pymongo
from pymongo import MongoClient

app = Flask(__name__)

###
# Handle database connection
###
"""
def connect_db():
    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()
"""

if (os.environ.get('MONGOHQ_URL')):
    MONGO_URL = os.environ.get('MONGOHQ_URL')
    client = MongoClient(MONGO_URL)
else:
    HOST = 'localhost'
    PORT = 27017
    client = MongoClient(HOST, PORT)

db = client.three11
###
# Utility functions
###


###
# API Calls
###
'''
def get_sample():
    res = query_db("""
        SELECT *
        FROM requests
    """)
    
    return res

@app.route("/sample")
def display_sample():
    sample = get_sample()
    
    return Response(json.dumps(sample), mimetype='application/json')

'''
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
