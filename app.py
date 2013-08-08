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
    host = 'localhost'
    port = 27017
    client = MongoClient(host, port)

db = client.three11
###
# Utility functions
###
'''
def query_db(query, args=()):
    cur = g.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    #cur = g.db.cursor() # If using Postgres JSON functions
    
    try:
        cur.execute(query, args)
    except psycopg2.DataError,err:
        print 'Data Error: ', err
    
    try:
        res = cur.fetchall()
    except psycopg2.ProgrammingError, err:
        res = None
        print 'Programming Error: ', err

    cur.close()

    return res

###
# API Calls
###

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
'''
def get_sample_json():
    res = query_db("""
        SELECT row_to_json(row(status))
        FROM requests
    """)
    
    return res

@app.route("/sample_json")
def display_sample_json():
    sample = get_sample_json()
    
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
    app.run(debug=True)
