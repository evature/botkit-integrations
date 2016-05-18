'''
Created on May 4, 2016

@author: marina
'''

class MessagingProviders(object):
    facebook = 'FACEBOOK'
    line = 'LINE'
    telegram = 'TELEGRAM'
    slack = 'SLACK'

class SortBy(object):
    """ sort by enums """
    price = "price" 
    price_per_person = 'price per person' 
    distance = "distance" 
    rating = "rating" 
    guest_rating = "guest rating" 
    stars = "stars" 
    name = "name" 
    popularity = "popularity" 
    recommendations = "recommendations" 
 
class SortOrder(object):
    """Enumeration of the Sort Order attribute"""
    values = ('ascending', 'descending', 'reverse',)
    ascending, descending, reverse = values
    