#!/usr/bin/env python

import os
import sys
import datetime
import iso8601
import json
import requests
import pymongo
from shapely.geometry import shape, Point
from urlparse import urlparse

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

            """
            # Clean up Queue
            if type(req['extended_attributes']['queue']) is str:
                queue = req['extended_attributes'].split('_')[0]
            else:
                queue = None
            """
            
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

            service_requests.update(
                { "service_request_id":adjusted_req['service_request_id'] }, 
                { "$set": adjusted_req },
                upsert=True 
            )

    except Exception as e:
        print 'Update Error', e

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
        if (os.environ.get('MONGOHQ_URL')):
            MONGO_URL = os.environ.get('MONGOHQ_URL')
            conn = pymongo.Connection(MONGO_URL)
            db = conn[urlparse(MONGO_URL).path[1:]]
        else:
            conn = pymongo.Connection(config['DATABASE']['host'], config['DATABASE']['port'])
            db = config['DATABASE']['db_name']

        collection_prefix = config['DATABASE']['collection_prefix']
        service_requests = db[collection_prefix + 'requests']

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
