'''
Created on May 18, 2016

@author: marina
'''
from enums import MessagingProviders
from amadeus import flights_low_fare_search, amadeus_results_to_facebook
from expedia import get_ean_tags_from_webhook_input, expedia_search_request_to_facebook

def get_structured_message(messaging_provider, text=None, image_url=None):
    """ helper function that returns structured response for text and image url """
    response = None
    if text is not None or image_url is not None and messaging_provider in [MessagingProviders.facebook, MessagingProviders.line]:
        response = []
        if messaging_provider == MessagingProviders.facebook:
            if text is not None:
                response.append(dict(text=text))
            if image_url is not None:
                response.append(dict(attachment=dict(type="image", payload=dict(url=image_url))))
        elif messaging_provider == MessagingProviders.line:
            if text is not None:
                response.append(dict(contentType=1, toType=1, text=text))
            if image_url is not None:
                response.append(dict(contentType=2, toType=1,
                             originalContentUrl=image_url,
                             previewImageUrl=image_url))
    return response

def amadeus_flight_search_webhook(body):
    """
        body input: {origin, destination, departDateMin, departDateMax,
            returnDateMin, returnDateMax, travelers,
            attributes, sortBy, sortOrder}
        response format of the messagingProvider
    """
    if body.get('messagingProvider') == MessagingProviders.facebook:
        origin = body.get('origin', {})
        origin_airport = origin.get('allAirportsCode')
        if not origin_airport:
            if origin.get('airports'):
                origin_airport = origin.get('airports')[0]
        destination = body.get('destination', {})
        destination_airport = destination.get('allAirportsCode')
        if not destination_airport:
            if destination.get('airports'):
                destination_airport = destination.get('airports')[0]
        departure_date = body.get('departDateMin', '').split('T')[0]
        return_date = body.get('returnDateMin', None)
        if return_date:
            return_date = return_date.split('T')[0]
        adults = None
        travelers = body.get('travelers', {})
        if 'Adult' in  travelers or 'Elderly' in travelers:
            adults = int(travelers.get('Adult', 0)) + int(travelers.get('Elderly', 0))
        amadeus_results = flights_low_fare_search(origin_airport, destination_airport, departure_date,
                                return_date=return_date,
                                adults=adults,
                                children=travelers.get('Child', 0),
                                infants=travelers.get('Infant', 0),
                                max_price=None, currency=None,
                                number_of_results=3,
                                non_stop=None,
                                arrive_by=None,
                                return_by=None,
                                include_airlines=None,
                                exclude_airlines=None,
                                travel_class=None,
                                )
        return amadeus_results_to_facebook(amadeus_results, origin, destination)

def expedia_hotel_search_webhook(body):
    """
        body input: {location, arriveDate, duration, travelers, attributes, sortBy,
                        sortOrder, messagingProvider}
        response format of the messagingProvider
    """
    ean_tags = get_ean_tags_from_webhook_input(body)
    if body.get('messagingProvider') == MessagingProviders.facebook:
        return expedia_search_request_to_facebook(ean_tags)

def flight_boarding_pass_webhook(body):
    """
        body input: {messagingProvider}
        response format of the messagingProvider
    """
    say_it = "Here is your boarding pass"
    image_url = "https://d2hbukybm05hyt.cloudfront.net/images/singapore-bp.jpg"
    return get_structured_message(body.get('messagingProvider'), say_it, image_url)

def flight_itinerary_webhook(body):
    """
        body input: {messagingProvider}
        response format of the messagingProvider
    """
    say_it = "Here is your Itinerary"
    image_url = "https://d2hbukybm05hyt.cloudfront.net/images/itinerary.jpg"
    return get_structured_message(body.get('messagingProvider'), say_it, image_url)

def reservation_cancel_webhook(body):
    """
        body input: {messagingProvider}
        response format of the messagingProvider
    """
    say_it = "Please follow this link https://www.checkmytrip.com to cancel your reservation"
    return get_structured_message(body.get('messagingProvider'), text=say_it)

def flight_gate_number_webhook(body):
    """
        body input: {messagingProvider}
        response format of the messagingProvider
    """
    say_it = "Your flight is boarding in 25 minutes at Gate D4"
    return get_structured_message(body.get('messagingProvider'), text=say_it)

def flight_boarding_time_webhook(body):
    """
        body input: {messagingProvider}
        response format of the messagingProvider
    """
    say_it = "Your flight starts boarding in 20 minutes"
    return get_structured_message(body.get('messagingProvider'), text=say_it)

def flight_departure_time_webhook(body):
    """
        body input: {messagingProvider}
        response format of the messagingProvider
    """
    say_it = "Your flight departs at 7:35 am"
    return get_structured_message(body.get('messagingProvider'), text=say_it)

def flight_arrival_time_webhook(body):
    """
        body input: {messagingProvider}
        response format of the messagingProvider
    """
    say_it = "Your flight arrives at 9:45 pm"
    return get_structured_message(body.get('messagingProvider'), text=say_it)

