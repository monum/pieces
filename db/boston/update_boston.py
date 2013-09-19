#!/usr/bin/env python

import os
import sys
import datetime
import iso8601
import json
import requests
from shapely.geometry import shape, Point
import psycopg2
import urlparse

def load_json(filename):
    with open(filename, 'rt') as f:
        json_data = json.load(f)
        
    return json_data

def append_log(file_name, message):
    with open(file_name, 'a') as log_file:
        log_file.write('\n') 
    log_file.write(message)
    
def compute_time_range(end_date=None, num_of_days=1):
    """Computing the the start and end date for our Open311 query"""

    days_delta = datetime.timedelta(days=num_of_days)

    if end_date is None:
        end_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    
    end = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    start = end - days_delta

    return (start,end)

def parse_date(date_string):
    try:
        return iso8601.parse_date(date_string)
    except (iso8601.ParseError, Exception) as e:
        print 'Date Parsing Error: ', e
        return None

def get_requests(city, start, end, page):
    """
        Retrieving service request data from a 311 endpoint, in this case
        Boston's Open311 API
    """
    
    base_url = config['endpoint']

    query_args = {
                  'start_date':  start.isoformat() +'Z', 
                  'end_date':    end.isoformat() + 'Z',
                  'page':        page,
                  'page_size':   200,
                  'extensions':  'v1'
                 }
    
    print query_args
        
    try:
        return requests.get(base_url, params=query_args).json()
    except (requests.exceptions.RequestException, Exception) as e:
        print 'Requests Error: ', e
        return []
        #sys.exit(1)

def update_database(reqs):
    """Inserting and updating 311 data into our mongo database."""
    
    HEROKU_POSTGRES_URL = os.environ["HEROKU_POSTGRESQL_SILVER_URL"]
        
    if HEROKU_POSTGRES_URL:
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(HEROKU_POSTGRES_URL)
    
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
    else:
        conn = psycopg2.connect(
            host=config['DATABASE']['host'],
            password=config['DATABASE']['password'],
            dbname=config['DATABASE']['db_name'],
            user=config['DATABASE']['user']
        )
    cur = conn.cursor()
    
    table_prefix = config['DATABASE']['table_prefix']
    
    print table_prefix
    
    try:
        for req in reqs:
            attributes = [
                'service_request_id',
                'service_name',
                'service_code',
                'description',
                'status',
                'status_notes',
                'lat',
                'long',
                'requested_datetime',
                'updated_datetime',
                'address',
                'media_url'
            ]
                
            for attribute in attributes:
                if attribute not in req:
                    req[attribute] = None
            
            extended_attributes = [
                'channel',
                'classification',
                'queue'
            ]
            
            for extended_attribute in extended_attributes:
                if extended_attribute not in req['extended_attributes']:
                    req['extended_attributes'][extended_attribute] = None

            # Parse DateTimes
            requested_datetime = parse_date(req['requested_datetime'])
            updated_datetime = parse_date(req['updated_datetime'])

            # Set specific service type
            if type(req['extended_attributes']['classification']) is list and len(req['extended_attributes']['classification']) == 3:
                department = req['extended_attributes']['classification'][0]
                division = req['extended_attributes']['classification'][1]
                service_type = req['extended_attributes']['classification'][2]
            else:
                department = None
                division = None
                service_type = None
            
            # Find out the neighborhood of the request.
            
            if req['long'] and req['lat']:
                req_point = Point(req['long'], req['lat'])
            
                for feature in neighborhood_data['features']:
                    neighborhood_polygon = shape(feature['geometry'])
                    
                    if neighborhood_polygon.contains(req_point):
                        neighborhood = feature['properties']['neighborhood']
                        break
            else:
                neighborhood = None
                
            # Add category
            if service_type in config['taxonomy']:
                category = config['taxonomy'][service_type]['category']
            elif service_type:
                category = service_type
            else:
                category = None
            
            print category

            adjusted_req = {
                'service_request_id':       req['service_request_id'],
                'service_name':             req['service_name'],
                'service_code':             req['service_code'],
                'description':              req['description'],
                'status':                   req['status'],
                'lat':                      req['lat'],
                'lng':                      req['long'],
                'neighborhood':             neighborhood,
                'requested_datetime':       requested_datetime,
                'updated_datetime':         updated_datetime,
                'address':                  req['address'],
                'media_url':                req['media_url'],
                'channel':                  req['extended_attributes']['channel'],
                'department':               department,
                'division':                 division,
                'service_type':             service_type,
                'queue':                    req['extended_attributes']['queue'],
                'category':                 category
            }
            
            cur.execute("""
                SELECT service_request_id 
                FROM""" + table_prefix + """requests 
                WHERE service_request_id = %s
            """, (adjusted_req['service_request_id'],))
            
            res = cur.fetchone()
            
            if res:
                print 'Updating'
                
                cur.execute("""
                    UPDATE """ + table_prefix + """requests 
                    SET service_request_id=%(service_request_id)s,
                        service_name=%(service_name)s,
                        service_code=%(service_code)s,
                        description=%(description)s,
                        status=%(status)s,
                        lat=%(lat)s,
                        lng=%(lng)s,
                        neighborhood=%(neighborhood)s,
                        requested_datetime=%(requested_datetime)s,
                        updated_datetime=%(updated_datetime)s,
                        address=%(address)s,
                        media_url=%(media_url)s,
                        channel=%(channel)s,
                        department=%(department)s,
                        division=%(division)s,
                        service_type=%(service_type)s,
                        queue=%(queue)s,
                        category=%(category)s
                    WHERE service_request_id=%(service_request_id)s
                """, adjusted_req)
            else:
                print 'Inserting'
                
                cur.execute("""
                    INSERT 
                    INTO """ + table_prefix + """requests (service_request_id, 
                        service_name, service_code, description, status, 
                        lat, lng, neighborhood, requested_datetime, updated_datetime, 
                        address, media_url, channel, department, division, 
                        service_type, queue, category) 
                    VALUES (%(service_request_id)s, %(service_name)s, %(service_code)s,
                        %(description)s, %(status)s, %(lat)s, %(lng)s, %(neighborhood)s,
                        %(requested_datetime)s, %(updated_datetime)s, %(address)s, 
                        %(media_url)s, %(channel)s, %(department)s, %(division)s, 
                        %(service_type)s, %(queue)s, %(category)s);
                """, adjusted_req)

    except psycopg2.IntegrityError:
        conn.rollback()
    except Exception as e:
        print e
        
    conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    """
        Edit update_boston_config_sample.json to include the specifics about your postgres instance.
        Rename the file to update_boston_config.json.

        Example usage of this script: python update_boston.py -e 2013-07-25 -n 3
    """

    from optparse import OptionParser
    
    ONE_DAY = datetime.timedelta(1)
    
    parser = OptionParser()

    default_end_date = (datetime.datetime.utcnow()
                        .replace(hour=0, minute=0, second=0, microsecond=0) - ONE_DAY)
        
    defaults = {
        'config': 'update_boston_config.json', 
        'end_date': datetime.datetime.strftime(default_end_date,'%Y-%m-%d'), 
        'num_of_days': 1
    }

    parser.set_defaults(**defaults)
    
    parser.add_option('-c', '--config', dest='config', 
                      help='Provide your configuration file.')
    parser.add_option('-e', '--end_date', dest='end_date', 
                      help='Provide the end date in the form YYYY-MM-DD')
    parser.add_option('-n', '--num_of_days', dest='num_of_days', type='int', 
                      help='Provide the number of days.')
    options, args = parser.parse_args()

    if (options.config and options.end_date and options.num_of_days):
        config = load_json(options.config)
        # Connect to the database

        end_date = datetime.datetime.strptime(options.end_date, '%Y-%m-%d')        
        num_of_days = options.num_of_days
        
        neighborhood_data = load_json('data/boston_neighborhoods.geojson')

        start, end = compute_time_range(end_date, 1) # Just handling one day at a time

        latest_response_length = None 
    
        for day in xrange(num_of_days):
            page = 1
            more_pages = True  
            while more_pages:
                response = get_requests(config['city'], start, end, page)

                latest_response_length = len(response)

                if latest_response_length > 0:
                    update_database(response)
                    page += 1
                else:
                    more_pages = False

            start -= ONE_DAY
            end -= ONE_DAY
