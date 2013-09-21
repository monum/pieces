from flask import Flask, json, g, render_template, request, Response

import os
import psycopg2, psycopg2.extras
import urlparse

app = Flask(__name__)

###
# Handle database connection
###

def connect_db():    
    if "HEROKU_POSTGRESQL_OLIVE_URL" in os.environ:
        HEROKU_POSTGRES_URL = os.environ["HEROKU_POSTGRESQL_OLIVE_URL"]
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(HEROKU_POSTGRES_URL)
    
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    else:
        pass
        """
        return psycopg2.connect(
            host=config['DATABASE']['host'],
            password=config['DATABASE']['password'],
            dbname=config['DATABASE']['db_name'],
            user=config['DATABASE']['user']
        )
        """
"""
@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()
"""

###
# Utility functions
###

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
        FROM boston_requests
    """)
    
    return res

@app.route("/sample")
def display_sample():
    sample = get_sample()
    
    return Response(json.dumps(sample), mimetype='application/json')

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
    app.run(host='0.0.0.0', port=port, debug=True)
