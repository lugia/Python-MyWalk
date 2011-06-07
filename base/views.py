from django.shortcuts import render_to_response
from models import *
from utils import *
import time
import pprint
import urllib2
import simplejson as json

def test(request):
    return renderTextResponse("abc")


"""
-> mywalk.com/subscribe?guid=[string]&uri=[string]&extra=[string]

"""    
def subscribe(request):
    guid = idx(request.REQUEST, "guid")
    uri = idx(request.REQUEST, "uri")
    extra = idx(request.REQUEST, "extra")
    
    if guid == None or uri == None:
        return renderJsonErrorResponse("Invalid request")
    
    device = Device.get_by_key_name(guid)
#    return renderJsonErrorResponse("Device already exists")
    
    if device:
        device.uri = uri
        device.extra = extra
    else:
        device = Device(key_name = guid, guid = guid, uri = uri, extra = extra)
    
    device.put()
    
    return renderTextResponse("Successfully subscribe device : %s" % guid)

"""
-> logging?guid=[string]&text=[string]&timestamp=[time]
"""
def logging(request):
    guid = idx(request.REQUEST, "guid")
    text = idx(request.REQUEST, "text")
    timeStamp = idx(request.REQUEST, "timestamp")
    
    if guid == None or text == None or timeStamp == None:
        return renderJsonErrorResponse("Invalid request")
    
    device = Device.get_by_key_name(guid)
    
    if not device:
        return renderJsonErrorResponse("Device is not subscribed")
    
    log = Logging(guid = guid, text = text, timeStamp = long(timeStamp))
    log.put()
    
    return renderTextResponse("Successfully add log")

"""
-> addSchedule?guid=[string]&xml_text=[string]&scheduleTime=[time]&type=[string]      

(type = "IN_APP/ TILE/ TOAST") 
"""

def addSchedule(request):
    guid = idx(request.REQUEST, "guid")
    xmlText = idx(request.REQUEST, "xml_text")
    timeStamp = idx(request.REQUEST, "scheduleTime")
    creationTime = idx(request.REQUEST, "creationTime")
    type = idx(request.REQUEST, "type")
    
    if guid == None or xmlText == None or timeStamp == None or creationTime == None or type == None:
        return renderJsonErrorResponse("Invalid request")
    
    device = Device.get_by_key_name(guid)
    
    if not device:
        return renderJsonErrorResponse("Device is not subscribed")
    
    schedule = Schedule(device = device, 
                        xmlText = xmlText, 
                        timeStamp = long(timeStamp),
                        creationTime = long(creationTime), 
                        type = type)
    
    schedule.put()
    
    return renderTextResponse("Successfully add schedule")


"""
-> removeSchedule?guid=[string]&type=[string]
(remove all schedule with that type of that guid)
"""
def removeSchedule(request):
    guid = idx(request.REQUEST, "guid")
    type = idx(request.REQUEST, "type")
    time = idx(request.REQUEST, "upToTime")
    
    
    if guid == None or type == None:
        return renderJsonErrorResponse("Invalid request")
    
    device = Device.get_by_key_name(guid)
    
    if not device:
        return renderJsonErrorResponse("Device is not subscribed")
    
    query = Schedule.gql("WHERE device = :1 AND type = :2 AND creationTime < :3", device, type, time)

    count = 0    
    for schedule in query:
        count = count + 1
        schedule.delete()
        
    return renderTextResponse("Successfully removed %d schedules" % count)


def pushSchedule(schedule):
    opener = urllib2.build_opener()
    
    opener.addheaders = [('X-NotificationClass', '3')]
    
    if schedule.type == 'TOAST' :
        opener.addheaders = [('X-WindowsPhone-Target', 'toast'), ('X-NotificationClass', '2')]
    elif schedule.type == 'TILE':
        opener.addheaders = [('X-WindowsPhone-Target', 'token'), ('X-NotificationClass', '1')]
        
    req = urllib2.Request(url = schedule.device.uri, data = schedule.xmlText)
    assert req.get_method() == 'POST'
    response = opener.open(req)
    return response.code
    
def cron(request):
    timeNow = long(time.time())
    query = Schedule.gql("WHERE timeStamp < :1 ", timeNow) 

    count = 0
    results = []    
    for schedule in query:
        count = count + 1
        firedSchedule = FiredSchedule(device = schedule.device,
                                        xmlText = schedule.xmlText,
                                        timeStamp = schedule.timeStamp,
                                        creationTime = schedule.creationTime,
                                        type = schedule.type)
        try:
            code = pushSchedule(schedule)
            firedSchedule.returnCode = code
            results.append('pushed: return code = ' + str(code))
        except:
            results.append('exception thrown')
            firedSchedule.returnCode = -1
            pass
        
        firedSchedule.put()
        schedule.delete()
        
    return renderTextResponse("Successfully pushed %d schedules <br /> %s" % (count, '<br />'.join(results)))

def nukedata(request):
    for d in Device.all(keys_only=True):
        db.delete(d)
    
    for l in Logging.all(keys_only=True):
        db.delete(l)
    
    for s in Schedule.all(keys_only=True):
        db.delete(s)
    
    for s in FiredSchedule.all(keys_only=True):
        db.delete(s)
        
        
    return renderTextResponse("Nuked data")

def main(request):
    DEVICE = "1. Device"
    LOGGING = "2. Logging"
    SCHEDULE = "3. Schedule"
    FIREDSCHEDULE = "4. Fired Schedule"
    
    ret = {"0. Time" : long(time.time()),
           DEVICE : [], LOGGING : [], SCHEDULE : [], FIREDSCHEDULE : []}
    
    for d in Device.all():
        ret[DEVICE].append({"guid" : d.guid,
                              "uri" : d.uri,
                              "extra" : d.extra})
    
    for l in Logging.all():
        ret[LOGGING].append({"guid" : l.guid,
                              "text" : l.text,
                              "timestamp" : l.timeStamp})
    
    for s in Schedule.all():
        ret[SCHEDULE].append({"guid" : s.device.guid,
                               "xml" : s.xmlText,
                               "time" : s.timeStamp,
                               "creationTime" : s.creationTime,
                               "type" : s.type})

    for s in FiredSchedule.all():
        ret[FIREDSCHEDULE].append({"guid" : s.device.guid,
                               "xml" : s.xmlText,
                               "time" : s.timeStamp,
                               "creationTime" : s.creationTime,
                               "type" : s.type,
                               "returnCode" : s.returnCode})
        
        
    return renderTextResponse("<pre>" + pprint.pformat(ret) + "</pre>")


