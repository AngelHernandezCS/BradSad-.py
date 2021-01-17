import time, discord, requests, random
import oauth2 as oauth, urllib
import requests_oauthlib
import json
import pytz
from datetime import datetime, timedelta
import os
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError
class schoology:
    def __init__(self, consumer_key, consumer_secret, domain='https://www.schoology.com', three_legged=False,
                    request_token=None, request_token_secret=None, access_token=None, access_token_secret=None):
            #establishes the root and domain which we already know 
            self.API_ROOT = 'https://api.schoology.com/v1'
            self.DOMAIN_ROOT = domain
            
            #allows to establish the key and secret we give it     
            self.consumer_key = consumer_key
            self.consumer_secret = consumer_secret
            
            #tokens for 3 legged oauth
            self.request_token = request_token
            self.request_token_secret = request_token_secret
            self.access_token = access_token
            self.access_token_secret = access_token_secret

            #requests self user with oauth using given secret and key 
            self.oauth = requests_oauthlib.OAuth1Session(self.consumer_key, self.consumer_secret)
            self.three_legged = three_legged

    def getusercode(self):
        #using the key and secret provided, gets a dictionary of the user's information. ex: name, usercode, student id, etc.
        try:
            user = self.oauth.get("https://api.schoology.com/v1/users/me")
            return user.json()
        except JSONDecodeError:
            return None

    def getusercourses(self,usercode):
        #using the key,secret, and usercode, gets all of the user's classes in a dictionary
        try:
            classes = self.oauth.get("https://api.schoology.com/v1/users/" + usercode + "/sections")
            return classes.json()
        except JSONDecodeError:
            return{}
            
    def getassignments(self, start, limit, classcode):
        #using the key,secret,usercode, and classcode selected, gets a massive dictionary of all the assignments
        try:
            getlink = "https://api.schoology.com/v1/sections/" + str(classcode) + "/assignments"+"?start="+str(start)+"&limit="+str(limit)
            courses = self.oauth.get(getlink)
            return courses.json()
        except JSONDecodeError:
            return{}