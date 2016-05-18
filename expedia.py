'''
Created on Apr 24, 2016

@author: marina
'''
from __future__ import unicode_literals, division
import hashlib
import time
import requests
import json
import logging
from datetime import datetime
from datetime import timedelta
from requests.exceptions import ConnectionError
from enums import SortBy, SortOrder

LOGGER = logging.getLogger(__name__)


CID = 'XXXXXXX'
API_KEY = 'XXXXXXXXXXXXXXXXXX'
SIGNATURE_SECRET = 'XXXXXXXXXXXX'

THUMBNAIL_PREFIX = 'http://images.travelnow.com//'
 
def run_expedia_request(ean_tags, ip_addr = '127.0.0.1', results_num=10):
    signature_input = API_KEY + SIGNATURE_SECRET + str(int(time.time()))

    md_res = hashlib.md5()
    md_res.update(signature_input)
    sig = md_res.hexdigest()
    req_url = "http://api.ean.com/ean-services/rs/hotel/v3/list?"
    preset_tags = "?minorRev=30&cid={}&apiKey={}&sig={}&customerUserAgent=Mozilla/4.0&customerIpAddress={}&locale=en_US&currencyCode=USD&numberOfResults={}&room1=2".format(CID, API_KEY, sig, 
                                                                                                                                                 ip_addr,
                                                                                                                                                 results_num)
    req_url += preset_tags 
    for tag_code, tag_value in ean_tags.iteritems():
        req_url += '&{}={}'.format(tag_code, tag_value)
    response = requests.get(req_url)
    LOGGER.debug("run_expedia_request: url %s", req_url)
    return json.loads(response.content)

def sort_by_ean_value(sortby, order):
    value = None
    if sortby in (SortBy.price, SortBy.price_per_person):
        if order in (SortOrder.descending, SortOrder.reverse):
            value = "PRICE_REVERSE"
        else:
            value = "PRICE"
    elif sortby in (SortBy.stars, SortBy.rating):
        if order in (SortOrder.descending, SortOrder.reverse):
            value = "QUALITY_REVERSE"
        else:
            value = "QUALITY"
    elif sortby in (SortBy.popularity, SortBy.guest_rating, SortBy.recommendations):
        # tripadvisor - no reverse
        value =  "TRIP_ADVISOR"
    elif sortby == SortBy.name:
        value = "ALPHA"
    elif sortby == SortBy.distance:
        value = "PROXIMITY"
    return value

def get_ean_tags_from_webhook_input(body):
    """ input: {location, arriveDate: '2016-05-04T00:00:00', duration: '1', travelers, attributes, 
                                        sortBy, sortOrder, messagingProvider}"""
    ean_tags = {}
    if body.get('arriveDate'):
        arrivalDatetime = datetime.strptime(body['arriveDate'], "%Y-%m-%dT%H:%M:%S")
        ean_tags['arrivalDate'] = arrivalDatetime.strftime("%m/%d/%Y")
        if body.get('duration'):
            departureDatetime = arrivalDatetime + timedelta(days=int(body['duration']))
            ean_tags['departureDate'] = departureDatetime.strftime("%m/%d/%Y")
    location = body.get('location', {})
    if location:
        if location.get('longitude'):
            ean_tags['longitude'] = location['longitude']
        if location.get('latitude'):
            ean_tags['latitude'] = location['latitude']
    sortby = body.get('sortBy')
    order = body.get('sortOrder')
    if sortby:
        value = sort_by_ean_value(sortby, order)
        if value:
            ean_tags['sort']=value
    return ean_tags
 
def expedia_search_request_to_facebook(ean_tags):
    """ expedia search into facebook format """
    try:
        ean_response = run_expedia_request(ean_tags, results_num=10)
    except ValueError, ConnectionError:
        pass # expedia returned not json or connection error
    else:
        expedia_hotels_list = ean_response.get('HotelListResponse',{}).get('HotelList', {}).get('HotelSummary', [])
        elements = []
        for hotel_item in expedia_hotels_list:
            element = dict(title=hotel_item['name'],
                            image_url='http://images.travelnow.com/{}'.format(hotel_item['thumbNailUrl'].replace('_t.', '_b.')),
                            item_url=hotel_item['deepLink'],
                            buttons=[{"type":"web_url",
                                     "url":hotel_item['deepLink'],
                                     "title":"View Hotel"}])
            subtitle = None
            room_rate = hotel_item.get('lowRate') or hotel_item.get('highRate')
            if hotel_item.get('lowRate') and hotel_item.get('highRate'):
                if hotel_item.get('lowRate') != hotel_item.get('highRate'):
                    subtitle = "Room Rate is between {} and {} {}".format(hotel_item['lowRate'], hotel_item['highRate'], hotel_item['rateCurrencyCode'])
            if subtitle is None and room_rate:
                subtitle = "Room Rate is {}{}".format(room_rate, hotel_item['rateCurrencyCode'])
            if subtitle is not None:
                element['subtitle']=subtitle
            elements.append(element)
        message = dict(attachment=dict(type="template", 
                                                  payload=dict(template_type="generic", 
                                                               elements=elements)))
        return message
                        