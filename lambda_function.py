#!/usr/bin/env python
#
# Source: https://github.com/Strosel/Carnet-alexa
# Huge thank you to https://github.com/reneboer/python-carnet-client/
#

import re
import json
import time

import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '/modules'))
import requests

from urlparse import urlsplit

class VWCarnet(object):
    def __init__(self, args):
        self.talk = ""
        self.carnet_username = ""
        self.carnet_password = ""
        if args['type'] == "IntentRequest":
            self.intent = args['intent']['name']
            if "Info" in self.intent:
                self.carnet_task = args['intent']['name'][:-10]
            else:
                self.carnet_task = args['intent']['slots']['task']['value']
        elif args['type'] == "LaunchRequest" or "InfoIntent" in args['type']:
            self.intent = "Info"
            self.carnet_task = args['type'].replace("InfoIntent","")

        # Fake the VW CarNet mobile app headers
        self.headers = { 'Accept': 'application/json, text/plain, */*', 'Content-Type': 'application/json;charset=UTF-8', 'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; D5803 Build/23.5.A.1.291; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36' }
        self.session = requests.Session()
        self.timeout_counter = 30 # seconds

        try:
            self._carnet_logon()
        except:
            self.talk += "Sorry, I can't log in at this time. Have you entered the correct credentials?"

    def _carnet_logon(self):
        AUTHHEADERS = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; D5803 Build/23.5.A.1.291; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36'}

        auth_base = "https://security.volkswagen.com"
        base = "https://www.volkswagen-car-net.com"

        # Regular expressions to extract data
        csrf_re = re.compile('<meta name="_csrf" content="([^"]*)"/>')
        redurl_re = re.compile('<redirect url="([^"]*)"></redirect>')
        viewstate_re = re.compile('name="javax.faces.ViewState" id="j_id1:javax.faces.ViewState:0" value="([^"]*)"')
        authcode_re = re.compile('code=([^"]*)&')
        authstate_re = re.compile('state=([^"]*)')

        def extract_csrf(r):
            return csrf_re.search(r.text).group(1)

        def extract_redirect_url(r):
            return redurl_re.search(r.text).group(1)

        def extract_view_state(r):
            return viewstate_re.search(r.text).group(1)

        def extract_code(r):
            return authcode_re.search(r).group(1)

        def extract_state(r):
            return authstate_re.search(r).group(1)

        # Request landing page and get CSFR:
        r = self.session.get(base + '/portal/en_GB/web/guest/home')
        if r.status_code != 200:
            return ""
        csrf = extract_csrf(r)

        # Request login page and get CSRF
        AUTHHEADERS["Referer"] = base + '/portal'
        AUTHHEADERS["X-CSRF-Token"] = csrf
        r = self.session.post(base + '/portal/web/guest/home/-/csrftokenhandling/get-login-url', headers=AUTHHEADERS)
        if r.status_code != 200:
            return ""
        responseData = json.loads(r.content)
        lg_url = responseData.get("loginURL").get("path")

        # no redirect so we can get values we look for
        r = self.session.get(lg_url, allow_redirects=False, headers = AUTHHEADERS)
        if r.status_code != 302:
            return ""
        ref_url = r.headers.get("location")

        # now get actual login page and get session id and ViewState
        r = self.session.get(ref_url, headers = AUTHHEADERS)
        if r.status_code != 200:
            return ""
        view_state = extract_view_state(r)

        # Login with user details
        AUTHHEADERS["Faces-Request"] = "partial/ajax"
        AUTHHEADERS["Referer"] = ref_url
        AUTHHEADERS["X-CSRF-Token"] = ''

        post_data = {
            'loginForm': 'loginForm',
            'loginForm:email': self.carnet_username,
            'loginForm:password': self.carnet_password,
            'loginForm:j_idt19': '',
            'javax.faces.ViewState': view_state,
            'javax.faces.source': 'loginForm:submit',
            'javax.faces.partial.event': 'click',
            'javax.faces.partial.execute': 'loginForm:submit loginForm',
            'javax.faces.partial.render': 'loginForm',
            'javax.faces.behavior.event': 'action',
            'javax.faces.partial.ajax': 'true'
        }

        r = self.session.post(auth_base + '/ap-login/jsf/login.jsf', data=post_data, headers = AUTHHEADERS)
        if r.status_code != 200:
            return ""
        ref_url = extract_redirect_url(r).replace('&amp;', '&')

        # redirect to link from login and extract state and code values
        r = self.session.get(ref_url, allow_redirects=False, headers = AUTHHEADERS)
        if r.status_code != 302:
            return ""
        ref_url2 = r.headers.get("location")

        code = extract_code(ref_url2)
        state = extract_state(ref_url2)

        # load ref page
        r = self.session.get(ref_url2, headers = AUTHHEADERS)
        if r.status_code != 200:
            return ""

        AUTHHEADERS["Faces-Request"] = ""
        AUTHHEADERS["Referer"] = ref_url2
        post_data = {
            '_33_WAR_cored5portlet_code': code,
            '_33_WAR_cored5portlet_landingPageUrl': ''
        }
        r = self.session.post(base + urlsplit(
            ref_url2).path + '?p_auth=' + state + '&p_p_id=33_WAR_cored5portlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_count=1&_33_WAR_cored5portlet_javax.portlet.action=getLoginStatus',
                   data=post_data, allow_redirects=False, headers=AUTHHEADERS)
        if r.status_code != 302:
            return ""

        ref_url3 = r.headers.get("location")
        r = self.session.get(ref_url3, headers=AUTHHEADERS)

        # We have a new CSRF
        csrf = extract_csrf(r)

        # Update headers for requests
        self.headers["Referer"] = ref_url3
        self.headers["X-CSRF-Token"] = csrf
        self.url = ref_url3

    def _carnet_post(self, command):
        #print(command)
        r = self.session.post(self.url + command, headers = self.headers)
        return r.content

    def _carnet_post_action(self, command, data):
        #print(command)
        r = self.session.post(self.url + command, json=data, headers = self.headers)
        return r.content


    def _carnet_retrieve_carnet_info(self):
        vehicle_data = {}
        vehicle_data_messages = json.loads(self._carnet_post( '/-/msgc/get-new-messages'))
        vehicle_data_location = json.loads(self._carnet_post('/-/cf/get-location'))

        vehicle_data_status = json.loads(self._carnet_post('/-/vsr/get-vsr'))
        vehicle_data_details = json.loads(self._carnet_post('/-/vehicle-info/get-vehicle-details'))
        vehicle_data_emanager = json.loads(self._carnet_post('/-/emanager/get-emanager'))

        vehicle_data['messages'] = vehicle_data_messages
        vehicle_data['location'] = vehicle_data_location
        vehicle_data['status'] = vehicle_data_status
        vehicle_data['details'] = vehicle_data_details
        vehicle_data['emanager'] = vehicle_data_emanager

        return vehicle_data

    def _carnet_start_charge(self):
        post_data = {
            'triggerAction': True,
            'batteryPercent': '100'
        }
        return json.loads(self._carnet_post_action('/-/emanager/charge-battery', post_data))

    def _carnet_stop_charge(self):
        post_data = {
            'triggerAction': False,
            'batteryPercent': '99'
        }
        return json.loads(self._carnet_post_action('/-/emanager/charge-battery', post_data))


    def _carnet_start_climat(self):
        post_data = {
            'triggerAction': True,
            'electricClima': True
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-climatisation', post_data))


    def _carnet_stop_climat(self):
        post_data = {
            'triggerAction': False,
            'electricClima': True
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-climatisation', post_data))

    def _carnet_start_window_melt(self):
        post_data = {
            'triggerAction': True
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-windowheating', post_data))

    def _carnet_stop_window_melt(self):
        post_data = {
            'triggerAction': False
        }
        return json.loads(self._carnet_post_action('/-/emanager/trigger-windowheating', post_data))

    def _carnet_print_carnet_info(self):
        vehicle_data = self._carnet_retrieve_carnet_info()
        vehicle_located  = self._google_get_location(str(vehicle_data['location']['position']['lng']), str(vehicle_data['location']['position']['lat']))
        if vehicle_located and self.carnet_task != "Location":
            addr = "It's located at "+vehicle_located
        elif vehicle_located and self.carnet_task == "Location":
            addr = "Your car is located at "+vehicle_located
        else:
            addr = "I'm sorry but i couldn't get an address for your cars location"

        if vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateFront'] != "OFF" and vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateRear'] != "OFF":
            windowstate = "heating in the front and rear"
        elif vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateFront'] == "OFF" and vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateRear'] != "OFF":
            windowstate = "heating in the rear"
        elif vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateFront'] != "OFF" and vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateRear'] == "OFF":
            windowstate = "heating in the front"
        elif vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateFront'] == "OFF" and vehicle_data['emanager']['EManager']['rpc']['status']['windowHeatingStateRear'] == "OFF":
            windowstate = "not heating"

        if self.carnet_task == "":
            if vehicle_data['emanager']['EManager']['rbc']['status']['extPowerSupplyState'] == "AVAILABLE" and vehicle_data['emanager']['EManager']['rbc']['status']['pluginState'] == "DISCONNECTED":
                self.talk += "Your car has driven "+str(vehicle_data['details']['vehicleDetails']['distanceCovered']).replace('.','')+"km, The battery is charging and currently at "+str(vehicle_data['emanager']['EManager']['rbc']['status']['batteryPercentage'])+"%, The climate-control is "+str(vehicle_data['emanager']['EManager']['rpc']['status']['climatisationState'])+", Windows are "+windowstate+" and "+addr
            if vehicle_data['emanager']['EManager']['rbc']['status']['extPowerSupplyState'] == "AVAILABLE" and vehicle_data['emanager']['EManager']['rbc']['status']['pluginState'] != "DISCONNECTED":
                self.talk += "Your car has driven "+str(vehicle_data['details']['vehicleDetails']['distanceCovered']).replace('.','')+"km, The battery is charging externaly and currently at "+str(vehicle_data['emanager']['EManager']['rbc']['status']['batteryPercentage'])+"%, The climate-control is "+str(vehicle_data['emanager']['EManager']['rpc']['status']['climatisationState'])+", Windows are "+windowstate+" and "+addr
            else:
                self.talk += "Your car has driven "+str(vehicle_data['details']['vehicleDetails']['distanceCovered']).replace('.','')+"km, The battery is at "+str(vehicle_data['emanager']['EManager']['rbc']['status']['batteryPercentage'])+"%, The climate-control is "+str(vehicle_data['emanager']['EManager']['rpc']['status']['climatisationState'])+", Windows are "+windowstate+" and "+addr
        elif self.carnet_task == "Location":
            self.talk += addr
        elif self.carnet_task == "Battery":
            self.talk += "Your car's battery is currently at "+str(vehicle_data['emanager']['EManager']['rbc']['status']['batteryPercentage'])+"%"
        elif self.carnet_task == "Charge":
            if vehicle_data['emanager']['EManager']['rbc']['status']['extPowerSupplyState'] == "AVAILABLE" and vehicle_data['emanager']['EManager']['rbc']['status']['pluginState'] == "DISCONNECTED":
                self.talk += "Your car is Charging"
            elif vehicle_data['emanager']['EManager']['rbc']['status']['extPowerSupplyState'] == "AVAILABLE" and vehicle_data['emanager']['EManager']['rbc']['status']['pluginState'] != "DISCONNECTED":
                self.talk += "Your car is Charging externaly"
            else:
                self.talk += "Your car is not Charging"
        elif self.carnet_task == "Heat":
            self.talk += "Your car's climate-control is "+str(vehicle_data['emanager']['EManager']['rpc']['status']['climatisationState'])+" and Windows are "+windowstate
        elif self.carnet_task == "Distance":
            self.talk += "Your car has driven "+str(vehicle_data['details']['vehicleDetails']['distanceCovered']).replace('.','')+"km"
        else:
            self.talk += "Sorry, i couldnt get that information right now"

    def _carnet_print_action(self, resp):
        if not 'actionNotification' in resp:
            self.talk += "Sorry, I can't do that right now"
        else:
            if self.intent == "StartTaskIntent":
                self.talk += "I started %s for you" % (self.carnet_task)
            elif self.intent == "StopTaskIntent":
                self.talk += "I stopped %s for you" % (self.carnet_task)

    def _carnet_do_action(self):
        if "Info" in self.intent:
            self._carnet_print_carnet_info()
            return True
        elif self.intent == "StartTaskIntent":
            if 'charg' in self.carnet_task:
                resp = self._carnet_start_charge()
                self._carnet_print_action(resp)
                return True

            elif 'climat' in self.carnet_task or ('heat' in self.carnet_task and 'window' not in self.carnet_task):
                resp = self._carnet_start_climat()
                self._carnet_print_action(resp)
                return True

            elif 'window' in self.carnet_task:
                resp = self._carnet_start_window_melt()
                self._carnet_print_action(resp)
                return True
            else:
                self.talk = "I didn't quite get that"
                return True
        elif self.intent == "StopTaskIntent":
            if 'charg' in self.carnet_task:
                resp = self._carnet_stop_charge()
                self._carnet_print_action(resp)
                return True

            elif 'climat' in self.carnet_task or ('heat' in self.carnet_task and 'window' not in self.carnet_task):
                resp = self._carnet_stop_climat()
                self._carnet_print_action(resp)
                return True

            elif 'window' in self.carnet_task:
                resp = self._carnet_stop_window_melt()
                self._carnet_print_action(resp)
                return True
            else:
                self.talk = "I didn't quite get that"
                return True

    def _google_get_location(self, lng, lat):
        counter = 0
        location = False
        while counter < 3:
            lat_reversed = str(lat)[::-1]
            lon_reversed = str(lng)[::-1]
            lat = lat_reversed[:6] + lat_reversed[6:]
            lon = lon_reversed[:6] + lon_reversed[6:]
            try:
                req = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + str(lat[::-1]) + ',' + str(lon[::-1]))
            except:
                time.sleep(2)
                continue
            data = json.loads(req.content)
            if 'status' in data and data['status'] == 'OK':
                location = data["results"][0]["formatted_address"]
                break

            time.sleep(2)
            continue

        return location


def main(event, context):

    vw = VWCarnet(event['request'])
    if vw.talk == "":
        vw._carnet_do_action()
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "SSML",
                "ssml": "<speak>"+vw.talk+"</speak>",
            }
        }
    }
    return response
