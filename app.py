from flask import Flask, json, g, render_template, request, Response

import os
import psycopg2, psycopg2.extras
import urlparse

from datetime import date, datetime, timedelta

app = Flask(__name__)
app.debug = True

#config: table prefix

###
# Handle database connection
###

def connect_db():    
    if "HEROKU_POSTGRESQL_OLIVE_URL" in os.environ:
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(os.environ["HEROKU_POSTGRESQL_OLIVE_URL"])
    
        return psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    else:
        url_base = ''
        
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(url_base)
        
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
    #cur = g.db.cursor() # If using Postgres JSON functions
    
    #a = cur.mogrify(query, args)
    #print a
    
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

def get_formatted_date(start_date, end_date, fmt='%Y-%m-%d'):
    start_day = start_date.strftime(fmt);
    end_day = end_date.strftime(fmt)
    
    return (start_day, end_day)

def get_max_date():
    res = query_db("""
        SELECT MAX(requested_datetime) AS max_date
        FROM boston_requests
    """)
    
    return res[0]['max_date']

def combine_open_closed_counts(open_count_res, closed_count_res, start_date, end_date):
    """
        Combine counts of open requests and closed counts into one structure.
        You will end up with something that looks like this:
            
        [{"date": "2012-06-30", "Open": 27, "Closed": 133}, 
         {"date": "2012-07-01", "Open": 31, "Closed": 44},...]
    """
    
    daily_count_res = open_count_res + closed_count_res
    
    sorted_daily_count = sorted(daily_count_res, key=lambda k: k['date'])
        
    input_exhausted = False
    
    date = start_date
    
    count = 0
    
    input = sorted_daily_count[count]
    
    next_date = start_date
    
    combined_result = []
    
    while date <= end_date:
        info = {}
        
        info['date'] = datetime.strftime(date, '%Y-%m-%d')
        info['open'] = 0
        info['closed'] = 0
        
        while not input_exhausted and info['date'] == input['date']:
            if input['status'] == 'closed':
                info['closed'] += input['count']
            elif input['status'] == 'open':
                info['open'] += input['count']
                
            count = count + 1
            
            if count >= len(sorted_daily_count):
                input_exhausted = True
            else:
                input = sorted_daily_count[count]
        
        date = date + timedelta(1)
        
        combined_result.append(info)
    
    print combined_result
    
    return combined_result

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

@app.route("/daily_count")
def daily_count():
    """
        Get a daily count of service requests that were opened and closed during a
        range of dates.
        
        The default range is 56 days.
    """
    days = request.args.get("days", 56)
    
    end_date = get_max_date()
    
    start_date = end_date - timedelta(days=int(days)-1)
        
    start_day, end_day = get_formatted_date(start_date, end_date)
        
    open_count_res = query_db("""
        SELECT 
            CAST(DATE(requested_datetime) as text) as date, COUNT(*), status
        FROM boston_requests 
        WHERE DATE(requested_datetime) BETWEEN (%s) AND (%s) AND status='open'
        GROUP BY date, status
        ORDER BY date ASC
    """, (start_day, end_day))
    
    closed_count_res = query_db("""
        SELECT 
            CAST(DATE(updated_datetime) as text) as date, COUNT(*), status
        FROM boston_requests 
        WHERE DATE(updated_datetime) BETWEEN (%s) AND (%s) AND status='closed'
        GROUP BY date, status
        ORDER BY date ASC
    """, (start_day, end_day))
            
    return Response(
        json.dumps(
            combine_open_closed_counts(
                open_count_res,
                closed_count_res,
                start_date,
                end_date
            )
        ),
        mimetype='application/json')

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
