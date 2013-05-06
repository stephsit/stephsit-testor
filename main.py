#!/usr/bin/env python
# THIS IS USED AS AN EXAMPLE OF EXPLORING THE PANDORA JSON URLS. 
# NO WARRANTY IS GIVEN OF ANY KIND FOR THE DATA OUTPUT FROM USING THIS.
# SIMULTANEOUSLY HITTING THE PANDORA API IS PROBABLY PROHIBITTED.

import webapp2
import os
import sys
import json
sys.path.insert(0, 'libs')
import mechanize
import cookielib
from bs4 import BeautifulSoup
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
import lxml

def isUp(site):
    url = 'http://' + site
    data = urlfetch.fetch(url, headers={
                              'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31'})
    return data.headers

def getUrl(url):
    if memcache.get(url):
        return memcache.get(url)
    else:
        br = mechanize.Browser()
        cj = cookielib.LWPCookieJar()
        br.set_cookiejar(cj)
        br.set_handle_equiv(True)
        br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        r = br.open(url)
        html = r.read()
        external = []
        for i in br.links():
            if i.url != '#':
                if i.url[0] == '/':
                    i.url = url + i.url
                external.append(i.url)
        s = BeautifulSoup(html, "lxml")
        images = []
        for tag in s.findAll('img'):
            try:
                t = tag['src']
                if t[1] != 'i':
                    #t = url + t
                    if not "http://www.pandora" in t:
                        if not "/static" in t:
                            images.append(t)
            except:
                pass
        scripts = []
        for script in s.findAll('script'):
            try:
                t = script['src']
                if t[0] != '/':
                    #t = url + t
                    scripts.append(t)
            except:
                pass
        data = {'images': images, 'links': external, 'scripts': scripts}
        memcache.set(url, data)
        return data
def sStr(s):
    sa = s.strip('http://').strip('//').strip('s://')
    return sa

def getSite(site):
    if memcache.get('site://' + site):
        return memcache.get('site://' + site)
    else:
        data = getUrl('http://www.' + str(site))
        external = []
        count = 0
        for i in data['images']:
            count += 1
            i = i.split('.com')[0] + '.com'
            external.append(sStr(i))
        for i in data['scripts']:
            count += 1
            i = i.split('.com')[0] + '.com'
            external.append(sStr(i))
        for i in data['links'][1:115]:
            if "http://www.pandora" in i:
                count += 1
                try:
                    images = getUrl(i)['images']
                    scripts = getUrl(i)['scripts']
                    for i in images:
                        i = i.split('.com')[0] + '.com'
                        external.append(sStr(i))
                    for i in scripts:
                        i = i.split('.com')[0] + '.com'
                        external.append(sStr(i))
                except:
                    pass
        data = {'external': list(set(external)), 'count': count}
        print data
        memcache.set('site://' + site, data)
        return data

class IndexHandler(webapp2.RequestHandler):
    def get(self, site):
        """
            INDEX HANDLER: main page e.g. www.host.com
        """
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        headers = isUp(site)
        self.response.out.write(template.render(path, {'data': getSite(site), 'header': headers['set-cookie']}))

class IndxHandler(webapp2.RequestHandler):
    def get(self):
        url = 'http://www.pandora.com'
        html = urlfetch.fetch(url, validate_certificate=False, headers={
                              'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.65 Safari/537.31'}).content
        #html = html2text.HTML2Text(html)
        self.response.out.write(html)



# SET APP VARIABLES
app = webapp2.WSGIApplication([
    ('/(.+)', IndexHandler)
], debug=True)
