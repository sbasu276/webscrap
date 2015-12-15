import sys
from BeautifulSoup import BeautifulSoup, SoupStrainer
import urllib2

url = 'https://tech.yandex.com/direct/doc/dg-v4/reference/ErrorCodes-docpage/'
resp = urllib2.urlopen(url)
soup = BeautifulSoup(resp)
print soup.findAll('table')
#for link in soup.findAll('a', href=True):
#        print link['href']
