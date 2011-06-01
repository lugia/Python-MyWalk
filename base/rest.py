from models import *
from utils import *
import time
import base64
import Crypto.Cipher.AES
import StringIO
import facebook

MAX_TIME_DIFF = 5 * 60 #5 mins

def serialze(o):
    if hasattr(o, "serialize"):
        return o.serialize()
    raise TypeError("%r is not JSON serializable" % (o))

def test(request):
    return renderTextResponse("<strong>booya</strong>")
    return renderJsonResponse("yeah")


def map(request, segments=""):
    segments = segments.split("/")
    args = reduce(lambda x,y: x + ["Map", y], segments, [])
    obj = db.get(db.Key.from_path(*args))
    if obj == None:
        return renderJsonResponse("{error : 'invalid object'}")
    #return renderJsonResponse(obj.name)
    return renderJsonResponse(json.dumps(obj, default=serialze))

def allrooms(request, segments=""):
    segments = segments.split("/")
    args = reduce(lambda x,y: x + ["Map", y], segments, [])
    obj = db.get(db.Key.from_path(*args))
    if obj == None:
        return renderJsonResponse("{error : 'invalid object'}")
    
    children = Object.all().ancestor(obj).fetch(1000)
    
    out = json.dumps(children, default=serialze)
    
    return renderJsonResponse(out)

def userCheckins(request, userId=""):
    user = User.getUserById(userId)
    if user == None:
        return renderJsonResponse("{error : 'invalid user'}")
    checkIns = []
    
    for edge in user.getAllCheckins(): 
        checkIns.append(edge.end.name)
            
    return renderJsonResponse(json.dumps({'checkins' : checkIns}))

def roomCheckins(request, segments=""):
    
    segments = segments.split("/")
    if len(segments) < 2:
        return renderJsonResponse("{error : 'invalid request'}")
    
    args = reduce(lambda x,y: x + ["Map", y], segments[0:-1], []) + ["Object", segments[-1]]
    obj = db.get(db.Key.from_path(*args))
    if obj == None:
        return renderJsonErrorResponse('invalid object')
    
    users = []
    
    for edge in obj.getAllCheckins(): 
        users.append(edge.start.id)
            
    return renderJsonResponse({'users' : users})

def checkin(request):
    if request.method != 'POST':
        return renderJsonErrorResponse('must be POST request')
    
    if not (request.POST.has_key('key') and request.POST.has_key('data')):
        return renderJsonErrorResponse("invalid request")

    key = decrypt(base64.b64decode(request.POST['key']))
    cipher = Crypto.Cipher.AES.new(key)
    data = json.loads(clipPadding(cipher.decrypt(base64.b64decode(request.POST['data']))))

    
    if not (data.has_key('token') and data.has_key('path') and data.has_key('time')):
        return renderJsonErrorResponse("invalid request")
    
    if time.time() - int(data['time']) > MAX_TIME_DIFF:
        return renderJsonErrorResponse("request expired")
    
    user = User.getUserByToken(data['token'])
    if user == None:
        return renderJsonErrorResponse('invalid user')

    pathSegments = data['path'].split("/")
    args = reduce(lambda x,y: x + ["Map", y], pathSegments[0:-1], []) + ["Object", pathSegments[-1]]
    obj = db.get(db.Key.from_path(*args))
    if obj == None:
        return renderJsonErrorResponse('invalid object')
    
    
    if not user.checkin(obj): 
        return renderJsonErrorResponse("cannot checkin")
    
    checkIns = []
    for edge in user.getAllCheckins(): 
        checkIns.append(edge.end.name)
            
    return renderJsonResponse({'checkins' : checkIns})
     


def oldCheckin(request, segments=""):
    
    segments = segments.split("/")
    if len(segments) == 1:
        return userCheckins(request, segments[0])
    
    if len(segments) < 3:
        return renderJsonErrorResponse('invalid request')
    userId = segments[0]
    
    user = User.getUserById(userId)
    if user == None:
        return renderJsonErrorResponse('invalid user')
    args = reduce(lambda x,y: x + ["Map", y], segments[1:-1], []) + ["Object", segments[-1]]
    obj = db.get(db.Key.from_path(*args))
    if obj == None:
        return renderJsonErrorResponse('invalid object')
    
    checkIns = []
    
    if not user.checkin(obj): 
        raise Exception("Cannot checkin")
    for edge in user.getAllCheckins(): 
        checkIns.append(edge.end.name)
            
    return renderJsonResponse({'checkins' : checkIns})


"""
key=oq3f2p34YXw5pTKg5aaqMxrcNxuUybPJoDuwHeKj1uHfE6g43wA9KWCyWJFhDHcMWXsGhJmIddFCwzW2XF9nQYxq93LcnZB4tTZyhekMkXSm3cDi0auWR8HkHMJgJPlYTQQg1sHaMBuoXRAB9ABcinp9vgCb2P%2FjrZGC8hnX4Z3OkgiGS%2FyPQh32BqUfUJu4AiuLkfWSBshcnU2reVps%2FHar3SwFY5Esz70D1KYNZaMJcgapTDerOfwzQ9LVl5ASkxWIRWYN2LbEpToOkdFEQf9lDpYrbgy2qqgTGs0tfJHN%2F1BpYg6leBaBpW3KJi2q%2FtGlo5r0R3o2Btetp3%2F83DLg%3D%3D&data=TdH2JvJAGP3N3DHnXtzLoqGZhQ4HjlgETjhzQsiRfxQBMDWB9RStppKLnOhFv8RFxdlcCsPMJFZbONhvixTDOyk3MQO%2F4r6YBWEiVHcIi9ul9IaIYbK8ST88j31evk6KCehZO2BflRUctu7CyDvY47LiWt3IUdCQOJGBgdK6UIEyXgdrVTLkbhpJlkN2BdsobMVb6bd609S0oNRGLlTCVtTB872sS1sAU2By2BjSl8pBEJT%2FT3sVu8ptN9Hhc9ccNCvdjzChdFOCqJ6pw%2F7wvPHSautp9PrmHfWBs6vOYnfRRJQFcWYQqkLwQXW5ZEV0RVJqGbk3Fm2RZpVJdtzJgqRNsLCnyJTTNjEhDfoJ2nKhd3kSH9rDjzcqrXizn819fa1rek2DGi%2Fdrsf4l9scfoJksg%3D%3D
"""