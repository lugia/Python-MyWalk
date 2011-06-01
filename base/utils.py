from django.http import HttpResponse
import simplejson as json

def idx(a, id, default = None):
    if a.has_key(id):
        return a[id]
    return default

def printItems(dictObj, indent):
    ret = ""
    ret = ret + '  '*indent + '<ul>\n'
    for k,v in dictObj.iteritems():
        if isinstance(v, dict):
            ret = ret + '  '*indent + '<li>' + k+ ':'+ '</li>'
            ret = ret +  printItems(v, indent+1)
        else:
            ret = ret +  ' '*indent + '<li>' + str(k) + ':' + str(v) + '</li>'
    ret = ret + '  '*indent + '</ul>\n'
    return ret

def renderJsonResponse(msg):
    if type(msg) != str:
        msg = json.dumps(msg)
    #return renderTextResponse(msg, "application/json")
    return renderTextResponse(msg, "text/plain")

def renderJsonErrorResponse(msg):
    return renderJsonResponse({'error' : msg})

def renderTextResponse(text, mimetype="text/html"):
    return HttpResponse(text, mimetype=mimetype)

def getPartsFromRequest(request):
    ret = request.get_full_path().split("/")
    if ret[0] == '':
        ret = ret[1:]
    return ret

