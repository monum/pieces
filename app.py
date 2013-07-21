from flask import Flask, g, render_template

#***#
from flask import json

import os
import psycopg2, psycopg2.extras
import urlparse

app = Flask(__name__)

###
# Handle database connection
###

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

###
# Utility functions
###

def query_db(query, args=()):
    cur = g.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        cur.execute(query, args)
    except psycopg2.DataError,err:
        print 'Error', err
    
    try:
        res = cur.fetchall()
    except psycopg2.ProgrammingError, err:
        res = None
            
        print 'Error', err

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
    
    return json.dumps(sample)

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
    app.run()