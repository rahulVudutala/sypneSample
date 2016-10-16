import logging
import operator
logging.basicConfig(level=logging.DEBUG)
from spyne import Application, rpc, ServiceBase, \
    Integer, Unicode
from spyne import Iterable
from urllib2 import urlopen
import urllib2,cookielib
import json
from spyne.decorator import srpc
from spyne.protocol.http import HttpRpc
from spyne.protocol.json import JsonDocument
from spyne.server.wsgi import WsgiApplication
from datetime import datetime
from collections import OrderedDict
class HelloWorldService(ServiceBase):
    @srpc(str, str, str, _returns=Iterable(Unicode))
    def checkcrime(lat, lon, radius):
        crimeTypes={}
        dangerousStreets={}
        dangerList=[]
        addressList=[]
        uniqueAddressList=[]
        crimeHours=OrderedDict()
        crimeHours['12:01am-3am']=0
        crimeHours['3:01am-6am']=0
        crimeHours['6:01am-9am']=0
        crimeHours['9:01am-12noon']=0
        crimeHours['12:01pm-3:00pm']=0
        crimeHours['3:01pm-6pm']=0
        crimeHours['6:01pm-9pm']=0
        crimeHours['9:01pm-12midnight']=0
        finalAns=OrderedDict()
        site= "https://api.spotcrime.com/crimes.json?lat="+str(lat)+"&lon="+str(lon)+"&radius="+str(radius)+"&key=."
        count=0
        streetCount=0
        req = urllib2.Request(site)
        try:
            page = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            print e.fp.read()
        content = page.read()
        wjdata = json.loads(content)
        for address in wjdata['crimes']:
#           number of crimes
            count=count+1
#           most dangerous streets
            addressStr=address['address']
            if "OF" in addressStr:
                streetName=addressStr.split("OF")
                addressList.append((streetName[1]).lstrip())
            elif "BLOCK BLOCK" in addressStr:
                streetName=addressStr.split("BLOCK BLOCK")
                addressList.append((streetName[1]).lstrip())
            elif "BLOCK" in addressStr:
                streetName=addressStr.split("BLOCK")
                addressList.append((streetName[1]).lstrip())
            elif "&" in addressStr:
                streetName=addressStr.split("&")
                addressList.append((streetName[0]).lstrip())
                addressList.append((streetName[1]).lstrip())
            else:
                addressList.append(str(streetName).lstrip())

#           different types of crimes  
            if crimeTypes.get(address['type']) is None:
                crimeTypes[address['type']]=1
            else:
                crimeTypes[address['type']]=crimeTypes[address['type']]+1
#           number of crimes happened in different hours
            dt, start, stan = address['date'].split()
            time=start+" "+stan
            in_time = datetime.strptime(time, "%I:%M %p")
            out_time = datetime.strftime(in_time, "%H:%M")
            if out_time>'00:00' and out_time<='03:00':
                crimeHours["12:01am-3am"]=crimeHours["12:01am-3am"]+1
            elif out_time>'03:00' and out_time<='06:00':
                crimeHours["3:01am-6am"]=crimeHours["3:01am-6am"]+1
            elif out_time>'06:00' and out_time<='09:00':
                crimeHours["6:01am-9am"]=crimeHours["6:01am-9am"]+1
            elif out_time>'09:00' and out_time<='12:00':
                crimeHours["9:01am-12noon"]=crimeHours["9:01am-12noon"]+1
            elif out_time>'12:00' and out_time<='15:00':
                crimeHours["12:01pm-3:00pm"]=crimeHours["12:01pm-3:00pm"]+1
            elif out_time>'15:00' and out_time<='18:00':
                crimeHours["3:01pm-6pm"]=crimeHours["3:01pm-6pm"]+1
            elif out_time>'18:00' and out_time<='21:00':
                crimeHours["6:01pm-9pm"]=crimeHours["6:01pm-9pm"]+1
            else:
                crimeHours["9:01pm-12midnight"]=crimeHours["9:01pm-12midnight"]+1
#       for loop completed here
#       dangerous streets processing start here
        uniqueAddressList=list(set(addressList))
        for street in uniqueAddressList:
            streetCount=0
            for street1 in addressList:
                if street1==street:
                    streetCount=streetCount+1
            dangerousStreets[street]=streetCount
        sortedDangerousStreets = sorted(dangerousStreets, key = dangerousStreets.get, reverse = True)
        for elem in sortedDangerousStreets:
            dangerList.append(str(elem))
        topThree = dangerList[:3]
        finalAns['total crime']=count
        finalAns['the_most_dangerous_streets']=topThree
        finalAns['crime_type_count']=crimeTypes
        finalAns['event_time_count']=crimeHours
        yield finalAns
application = Application([HelloWorldService],
    tns='spyne.examples.hello',
    in_protocol=HttpRpc(validator='soft'),
    out_protocol=JsonDocument()
)
if __name__ == '__main__':
    # You can use any Wsgi server. Here, we chose
    # Python's built-in wsgi server but you're not
    # supposed to use it in production.
    from wsgiref.simple_server import make_server
    wsgi_app = WsgiApplication(application)
    server = make_server('0.0.0.0', 8000, wsgi_app)
    server.serve_forever()