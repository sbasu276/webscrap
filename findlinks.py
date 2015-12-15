import sys
from BeautifulSoup import BeautifulSoup, SoupStrainer
import urllib2

url = str(sys.argv[1])
resp = urllib2.urlopen(url)
soup = BeautifulSoup(resp)
for link in soup.findAll('a', href=True):
        print link['href']
