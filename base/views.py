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
    
    if device:
        return renderJsonErrorResponse("Device already exists")
    
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
    type = idx(request.REQUEST, "type")
    
    if guid == None or xmlText == None or timeStamp == None or type == None:
        return renderJsonErrorResponse("Invalid request")
    
    device = Device.get_by_key_name(guid)
    
    if not device:
        return renderJsonErrorResponse("Device is not subscribed")
    
    schedule = Schedule(device = device, 
                        xmlText = xmlText, 
                        timeStamp = long(timeStamp), 
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
    
    if guid == None or type == None:
        return renderJsonErrorResponse("Invalid request")
    
    device = Device.get_by_key_name(guid)
    
    if not device:
        return renderJsonErrorResponse("Device is not subscribed")
    
    query = Schedule.gql("WHERE device = :1 AND type = :2", device, type)

    count = 0    
    for schedule in query:
        count = count + 1
        schedule.delete()
        
    return renderTextResponse("Successfully removed %d schedules" % count)


def pushSchedule(schedule):
    opener = urllib2.build_opener()
    opener.addheaders = [('X-WindowsPhone-Target', 'toast'), ('X-NotificationClass', '2')]
    
    req = urllib2.Request(url = schedule.device.uri, data = schedule.xmlText)
    assert req.get_method() == 'POST'
    response = opener.open(req)
    return response.code
    
def cron(request):
    timeNow = long(time.time())
    query = Schedule.gql("WHERE timeStamp < :1 ", timeNow) 

    count = 0    
    for schedule in query:
        count = count + 1
        pushSchedule(schedule)
        schedule.delete()
        
    return renderTextResponse("Successfully pushed %d schedules" % count)

def nukedata(request):
    for d in Device.all():
        d.delete()
    
    for l in Logging.all():
        l.delete()
    
    for s in Schedule.all():
        s.delete()
        
    return renderTextResponse("Nuked data")

def main(request):
    ret = {"Device" : [], "Logging" : [], "Schedule" : []}
    
    for d in Device.all():
        ret["Device"].append({"guid" : d.guid,
                              "uri" : d.uri,
                              "extra" : d.extra})
    
    for l in Logging.all():
        ret["Logging"].append({"guid" : l.guid,
                              "text" : l.text,
                              "timestamp" : l.timeStamp})
    
    for s in Schedule.all():
        ret["Schedule"].append({"guid" : s.device.guid,
                               "xml" : s.xmlText,
                               "time" : s.timeStamp,
                               "type" : s.type})
        
        
    return renderTextResponse("<pre>" + pprint.pformat(ret) + "</pre>")


