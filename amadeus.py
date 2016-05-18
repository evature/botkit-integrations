# encoding=utf-8
'''
Created on May 8, 2016

@author: tal

The Amadeus Sandbox APIs at https://sandbox.amadeus.com
'''
from __future__ import unicode_literals, division, print_function
from pprint import pprint
import requests
import logging
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import dateparse
from tools.imgix_url_helper import ImagixUrlHelper
from tools.airports import AIRPORTS

LOGGER = logging.getLogger(__name__)

RESOURCE_URL = "https://api.sandbox.amadeus.com/v1.2"
APIKEY = "XXXXXXXXXXXXXXXXXXXXXXXX" # API Key provided for your account, to identify you for API access
IMAGIX_SIGN_KEY = 'xxxxxxxxxxxxxxxxxxx'

MAX_RESULTS = 5  # maximum number of results to show in chat


def flights_low_fare_search(origin, destination, departure_date,
                            return_date=None, adults=None, children=None, infants=None, max_price=None, currency=None,
                            number_of_results=None, non_stop=None, arrive_by=None, return_by=None, include_airlines=None,
                            exclude_airlines=None, travel_class=None,
                            ):
    """Low fare flight search - https://sandbox.amadeus.com/travel-innovation-sandbox/apis/get/flights/low-fare-search"""
    url = RESOURCE_URL + "/flights/low-fare-search"
    params = dict(apikey=APIKEY,
                  # Mandatory Fields:
                  origin=origin, # City code from which the traveler will depart. See the location and airport interfaces for more information.
                  destination=destination, # IATA city code to which the traveler is going
                  departure_date=departure_date, # The date on which the traveler will depart from the origin to go to the destination. The maximum scope for a date range is 2 days, for a larger scope, use the Extensive Search!
                  )
    if return_date is not None: # The date on which the traveler will depart from the destination to return to the origin.
        params['return_date'] = return_date # If this parameter is not specified, the search will find only one-way trips.
        # If this, or the return_by parameter are specified, only return trips are found
    if arrive_by is not None: # The datetime by which the outbound flight should arrive, based on local time at the
        params['arrive_by'] = arrive_by # destination airport
    if return_by is not None: # The time by which the inbound flight should arrive, based on local time at the airport specified as
        params['return_by'] = return_by # the origin parameter
    if adults is not None: # The number of adult (age 12 and over) passengers traveling on this flight.
        params['adults'] = adults
    if children is not None: # The number of child (younger than age 12 on date of departure) passengers traveling on this flight
        params['children'] = children # who will each have their own separate seat
    if infants is not None: # The number of infant (younger than age 2 on date of departure) passengers traveling on this flight.
        params['infants'] = infants # Infants travel in the lap of an adult passenger, and thus the number of infants must not
        # exceed the number of adults.
    if include_airlines is not None: # If specified, all results will include at least one flight where one or more of these
        params['include_airlines'] = include_airlines # airlines is the marketing carrier. This behaves as an OR function.
    if exclude_airlines is not None: # If specified, no results will include any flights where any of these airlines is the
        params['exclude_airlines'] = exclude_airlines # marketing carrier
    if non_stop is not None: # Setting this to true will find only flights that do not
        params["non-stop"] = non_stop # require the passenger to change from one flight to another. Warning - Non Pythonic name!
    if max_price is not None: # Maximum price of trips to find in the result set, in USD (US dollars) unless some other
        params['max_price'] = max_price # currency code is specified. By default, no limit is applied
    if currency is not None: # The preferred currency for the results
        params['currency'] = currency
    if travel_class is not None: # Searches for results where the majority of the itinerary flight time should be in a the specified
        params['travel_class'] = travel_class # cabin class or higher
    if number_of_results is not None: # The number of results to display. This will not be strictly interpreted but used as a
        params['number_of_results'] = number_of_results # guideline to display a useful number of results. By default, the number of
        # results is dynamically determined. A maximum of 250 results will be displayed.
    LOGGER.debug('amadeus flights_low_fare_search(params="%s")', str(params))
    res = requests.get(url, params=params)
    if res.status_code == requests.codes.OK: # @UndefinedVariable pylint:disable=no-member
        return res.json()
    else:
        LOGGER.warning("Amadeus flights_low_fare_search status code: %s  content=%s", res.status_code, res.text)


def format_date(date_str, date_fmt='l, jS F '):
    if not date_str:
        return ''
    dt = dateparse.parse_datetime(date_str)
    time_str = dt.strftime("%I:%M%p").rstrip(":00").lstrip("0")
    return naturalday(dt, date_fmt) + time_str

def get_flight_element(flight, title, idx, bg_color):
    '''facebook flight element'''            
    arrives_at = format_date(flight.get('arrives_at', ''), 'jS F ')
    departs_at = format_date(flight.get('departs_at', ''), 'jS F ')
    airline = flight.get('marketing_airline') or flight.get('operating_airline', '')
    origin_airport = flight.get('origin', {}).get('airport', '')
    destination_airport = flight.get('destination', {}).get('airport', '')
    flight_number = flight.get('flight_number', '')
    
    element = dict(title= "{}  {}{}".format(title, airline, flight_number),
                   subtitle = " 🛫: {} {} →  🛬: {} {}".format(AIRPORTS.get(origin_airport, {}).get('name', ''), 
                                                               departs_at,
                                                               AIRPORTS.get(destination_airport, {}).get('name', ''),
                                                               arrives_at),
                    buttons=[{"type":"web_url",
                             "url":'https://www.google.com/search?q=flight%20{}%20{}'.format(airline, flight_number),
                             "title":"View Flight"}])
    
    img_text = "{} → {}".format(origin_airport, destination_airport)
    img_url = "https://placeholdit.imgix.net/~text?txtsize=66&txt={}&w=382&h=200&bg={}&txtclr=000000".format(img_text, bg_color)
    element['image_url'] = img_url
    return element


def amadeus_results_to_facebook(amadeus_json, eva_origin, eva_destination):
    """ amadeus search result into facebook format """
    results = amadeus_json and amadeus_json.get('results', [])
    if not results:
        return "Sorry, no matching results found."
    messages = ["Here are the top {} results:".format(min(MAX_RESULTS, len(results)))]
    
    for idx, result in enumerate(results[:MAX_RESULTS]):
        price = result.get('fare', {}).get('total_price', '')
        itineraries = result.get('itineraries', [])
        # find outbound flights
        for itinerary in itineraries:
            outbound_flights = itinerary.get('outbound', {}).get('flights', [])
            inbound_flights = itinerary.get('inbound', {}).get('flights', [])
            
            arrives_at = format_date(outbound_flights[-1].get('arrives_at', ''))
            departs_at = format_date(outbound_flights[0].get('departs_at', ''))
            origin = outbound_flights[0].get('origin', {})
            destination = outbound_flights[-1].get('destination', {})
            origin_airport = origin.get('airport', '')
            destination_airport = destination.get('airport', '')
            subtitle = "🛫: {}, 🛬: {}".format( departs_at, arrives_at)
            if len(outbound_flights) > 2:
                subtitle += ", {} stops".format(len(outbound_flights)-1)
            elif len(outbound_flights) > 1:
                subtitle += ", one stop at {}".format(outbound_flights[0].get('destination',{}).get('airport', ''))
            else:
                subtitle += ", non stop"
            element = dict(title= "{} ⇒ {}  Option #{}:  ${}".format(origin_airport, destination_airport, idx+1, price),
                           subtitle = subtitle,
                            buttons=[{"type":"web_url",
                                     "url":'https://www.google.com/search?q=flight%20{}%20to%20{}'.format(origin_airport, destination_airport),
                                     "title":"Reserve seat"}])
            if eva_origin.get('latitude') and eva_destination.get('latitude'):
                map_url = "http://maps.googleapis.com/maps/api/staticmap?size=382x220" \
                    "&path=geodesic:true|color:red|{0},{1}".format(eva_origin.get('latitude'), eva_origin.get('longitude'))
                for outbound_flight in outbound_flights:
                    destination_airport = outbound_flight.get('destination', {}).get('airport', '')
                    if destination_airport in AIRPORTS:
                        map_url += "|{0},{1}".format(AIRPORTS[destination_airport]['latitude'], AIRPORTS[destination_airport]['longitude'])
                map_url += "&markers=size:mid|label:1|{0},{1}".format(eva_origin.get('latitude'), eva_origin.get('longitude'))
                for of_idx, outbound_flight in enumerate(outbound_flights):
                    destination_airport = outbound_flight.get('destination', {}).get('airport', '')
                    if destination_airport in AIRPORTS:
                        map_url += "&markers=size:mid|label:{}|{},{}".format(of_idx+2, AIRPORTS[destination_airport]['latitude'], AIRPORTS[destination_airport]['longitude'])
            else:
                map_url = ''
            img_text = "Option {}: ${}".format(idx+1, price)
            imgix_helper = ImagixUrlHelper("botkit.imgix.net", map_url, sign_key=IMAGIX_SIGN_KEY,
                                           opts=dict( rect="0,0,382,200",
                                                        txtalign='bottom,center', 
                                                        txtcolor='ddf8f9ff',
                                                        txtsize=240, 
                                                        txtfit='max', 
                                                        txtpad=40, 
                                                        txtline=10, 
                                                        txtfont='PT Sans Caption,Bold',
                                                        txtlineclr='dd050505', 
                                                        txt=img_text
                                         ))
            img_url = str(imgix_helper)
            element['image_url'] = img_url
            elements = [element]
                
            for idx, flight in enumerate(outbound_flights):
                title = "Outbound Flight"
                flight_element = get_flight_element(flight, title, idx, "bbbbff")
                elements.append(flight_element)
                
            for flight in inbound_flights:
                title = "Return Flight"
                flight_element = get_flight_element(flight, title, idx, "ffbbbb")
                elements.append(flight_element)
                
            message = dict(attachment=dict(type="template", 
                                              payload=dict(template_type="generic", 
                                                           elements=elements)))
            messages.append(message)
            pprint(message)
    return messages
                       

def d_flights_low_fare_search():
    """Demo the Low Fare Flights Search"""
    return flights_low_fare_search("NYC", "TYO", "2016-06-25", return_date="2016-07-01", number_of_results=5)

if __name__ == '__main__':
    pprint(d_flights_low_fare_search())

