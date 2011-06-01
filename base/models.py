from appengine_django.models import BaseModel
from google.appengine.ext import db
import facebook
from constants import *
import simplejson as json

json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)
# Create your models here.

class Device(BaseModel):
    guid = db.StringProperty(required = True)
    uri = db.StringProperty(required = True)
    extra = db.StringProperty(required = False)

class Logging(BaseModel):
    guid = db.StringProperty(required = True)
    text = db.StringProperty()
    timeStamp = db.IntegerProperty()

class Schedule(BaseModel):
    device = db.ReferenceProperty(Device)
    xmlText = db.StringProperty(required = True)
    timeStamp = db.IntegerProperty(required = True)
    type = db.StringProperty(required = True)

class Map(BaseModel):
    name = db.StringProperty()
    description = db.StringProperty(required = False)
    width = db.FloatProperty()
    height = db.FloatProperty()
    draw = db.TextProperty()
    geoloc = db.GeoPtProperty(required = False)
    
    def serialize(self):
        return {'name' : self.name,
              'description' : self.description,
              'width' : self.width,
              'height' : self.height,
              'draw' : json.loads(self.draw),
              'geoloc' : self.geoloc}
    
    def toJson(self):
        return json.dumps(self.serialize())

class Object(BaseModel):
    name = db.StringProperty()
    description = db.StringProperty(required = False)
    posX = db.FloatProperty()
    posY = db.FloatProperty()
    width = db.FloatProperty()
    height = db.FloatProperty()
    
    def serialize(self):
        return {'name' : self.name,
              'description' : self.description,
              'posX' : self.posX,
              'posY' : self.posY,
              'width' : self.width,
              'height' : self.height}
    
    def toJson(self):
        return json.dumps(self.serialize())
    
    def getAllCheckins(self):
        return db.GqlQuery("SELECT * FROM Edge WHERE end = :1 AND type = :2", self, EDGE_TYPE_CHECKIN)

class Link(BaseModel):
    object = db.ReferenceProperty(Object)
    # redundant information for fast lookup
    map = db.ReferenceProperty(Map)
    userId = db.IntegerProperty()
    type = db.CategoryProperty()

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profileUrl = db.StringProperty(required=True)
    accessToken = db.StringProperty(required=False)
    
    @staticmethod
    def getUserByToken(accessToken):
        graph = facebook.GraphAPI(accessToken)
        try:
            profile = graph.get_object("me")
        except:
            return None
        
        user = User.get_by_key_name(profile['id'])
        if not user:
            user = User(key_name=str(profile["id"]),
                        id=str(profile["id"]),
                        name=profile["name"],
                        profileUrl=profile["link"],
                        accessToken=accessToken)
            user.put()
        elif user.accessToken != accessToken:
            user.accessToken = accessToken
            user.put()
        return user
        
        
    @staticmethod
    def getUserById(userId, accessToken=None):
        user = User.get_by_key_name(userId)
        if not user:
            graph = facebook.GraphAPI(accessToken)
            try:
                profile = graph.get_object(str(userId))
            except:
                return None
            user = User(key_name=str(profile["id"]),
                            id=str(profile["id"]),
                            name=profile["name"],
                            profileUrl=profile["link"],
                            accessToken=accessToken)
            user.put()
        elif user.accessToken != accessToken:
            user.accessToken = accessToken
            user.put()
        return user
    
    @staticmethod
    def getCurrentUser(request):
        #dir(request)
        cookie = facebook.get_user_from_cookie(
        request.COOKIES, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
        user = None
        if cookie:
            # Store a local instance of the user data so we don't need
            # a round-trip to Facebook on every request
            user = User.get_by_key_name(cookie["uid"])
            if not user:
                graph = facebook.GraphAPI(cookie["accessToken"])
                profile = graph.get_object("me")
                user = User(key_name=str(profile["id"]),
                            id=str(profile["id"]),
                            name=profile["name"],
                            profileUrl=profile["link"],
                            accessToken=cookie["accessToken"])
                user.put()
            elif user.accessToken != cookie["accessToken"]:
                user.accessToken = cookie["accessToken"]
                user.put()
        return user
        
    
        
    def checkin(self, object):
        if type(object) == str:
            object = Object.gql("WHERE name = :1", object).get()
            if not object:
                raise Exception("Cannot find object")
                return False
            
        for edge in Edge.gql("WHERE start = :1", self):
            edge.delete()
            
        newEdge = Edge(type = EDGE_TYPE_CHECKIN,
                       start = self,
                       end = object)
        newEdge.put()
        return True
    
    def getAllCheckins(self):
        return db.GqlQuery("SELECT * FROM Edge WHERE start = :1 AND type = :2", self, EDGE_TYPE_CHECKIN)
        

class Edge(BaseModel):
    type = db.IntegerProperty()
    start = db.ReferenceProperty(collection_name = "edge_start_reference_set")
    end = db.ReferenceProperty(collection_name = "edge_end_reference_set")
    prop = db.ReferenceProperty(required = False)
