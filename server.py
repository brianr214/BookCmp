import gevent
from gevent import pywsgi
from gevent import monkey;monkey.patch_all()
import urllib2

from BeautifulSoup import BeautifulSoup
import simplejson as json
import re
from copy import deepcopy

def process(url, src):
    t = urllib2.urlopen(url).read()
    soup = BeautifulSoup(t)
    books = []
    if src == "flipkart":
        for x in soup.findAll('div', {"class": 'gd-col gu12 browse-product fk-inf-scroll-item'}):
            a = x.find('div', {"class": "lu-title-wrapper"}).find('a')
            try:
                isbn = re.search('pid=(?P<isbn>\d{13})', a['href']).group('isbn')
                print "fk",isbn
                d = {
                    'url': url+a['href'],
                    'title': a.text,
                    'img': x.find('div', {"class": "list-unit"}).find('img')['src'],
                    'price': {"flipkart": x.find('div', {"class": "list-unit"}).find('div', {"class": "pu-price"}).text},
                    'author': '',
                    'isbn': isbn
                }
                books.append(d)
            except:
                pass
        return {'flipkart': books}
    elif src == 'bookadda':
        for x in soup.find('ul', {"class": "results"}).findAll('li'):
            url = x.find('a')['href']
            try:
                isbn = re.search(r'\d+\-(?P<isbn>\d{13})', url).group('isbn')
                print "ba", isbn
                d = {
                    'url': x.find('a')['href'],
                    'title': x.find('a').text,
                    'img': x.find('img')['src'],
                    'price': {"bookadda": x.find('span', {"class": "new_price"}).text},
                    'author': [y.text for y in x.findAll('a')[1:]],
                    'isbn': isbn
                }
                books.append(d)
            except:
                pass
        return {'bookadda': books}
    else:
        return {}

# def deduplicate(kw):
#     def update(fk, ba):
#         fk['price']['bookadda'] = ba['bookadda']['price']
#         return fk
#     master = [update(fk, ba) for fk in kw['flipkart'] for ba in kw['bookadda'] if fk['isbn']==ba['isbn']]
#     #add books in flipkart which are not in master
#     master.extend([fk for x in master for fk in kw['flipkart'] if fk['isbn'] != x['isbn']])
#     #add books in bookadda which are not in master
#     for fk in kw['bookadda']:
#         if any(fk['isbn'] == x['isbn'] for x in master for fk in kw['bookadda']):
#             master.append(fk)

#     return master

def handle(environ, start_response):
    start_response('200 OK', [('Content-Type', 'application/json')])
    sources = [('http://flipkart.com/search?q=haskell', 'flipkart'), ('http://www.bookadda.com/general-search?searchkey=haskell', 'bookadda')]
    jobs = [gevent.spawn(process, url, src) for url,src in sources]
    gevent.joinall(jobs)
    kw = {}
    for j in jobs:
        kw.update(j.value)
    #v = deduplicate(kw)
    v = kw
    yield json.dumps(v)


server = pywsgi.WSGIServer(('127.0.0.1', 1234), handle)
print "Serving on http://127.0.0.1:1234..."
server.serve_forever()
