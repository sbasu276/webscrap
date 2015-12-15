import sys
import csv
from BeautifulSoup import BeautifulSoup, SoupStrainer
from urllib2 import urlopen, URLError, HTTPError
from argparse import ArgumentParser

# List of urls for each SE where the error codes can be found
# will be replaced by constants in everest/se/constants/search_engine.py
SE_URL_MAP = {
    'bing'      :   'http://msdn.microsoft.com/en-US/library/bing-ads-operation-error-codes.aspx',
    'baidu'     :   'http://dev2.baidu.com/sms_zh/en/Error_Code',
    'yandex'    :   'http://tech.yandex.com/direct/doc/dg-v4/reference/ErrorCodes-docpage/',
    'google'    :   'http://developers.google.com/adwords/api/docs/reference/v201509/AdGroupAdService.ApiError',
    }

def parse_arguments():
    """ Process command line arguments
    """
    parser = ArgumentParser(description = 'Scrap error codes')
    parser.add_argument('-s','--search-engine', required=True,
                        help='SE for which scraping will be done')
    parser.add_argument('-f','--file-name', required=True,
                        help='Output csv file name without extension')
    args = parser.parse_args()
    return args
    
def make_soup(url):
    """ Make soup from URL
    """
    try:
        response = urlopen(url)
    except HTTPError, e:
        print >> sys.stderr, "HTTPError: ", url
        return False
    except URLError, e:
        print >> sys.stderr, "URLError: ", url
        return False
    soup = BeautifulSoup(response.read())
    return soup

def parse_rows(rows):
    """ Get data from each row
    """
    results = []
    for row in rows:
        cols = row.findAll('td')
        if cols:
            # Handles cases where <td> has nested tags like <p>
            code = ''.join(cols[0].findAll(text=True))
            code = code.encode('utf8')
            message = "".join(cols[1].findAll(text=True))
            message = message.encode('utf8')
            if message:
                # Trim extra spaces/ newlines from code/ message
                results.append([''.join(code.split()), ' '.join(message.split())])
    return results

def parse_desclist(desclist):
    """ Get data from description lists
    """
    codes = []
    messages = []
    results = []
    dts = desclist.findAll('dt')
    dds = desclist.findAll('dd')
    # Get codes
    for dt in dts:
        code = ''.join(dt.findAll(text=True))
        code = code.encode('utf8')
        code = code.strip('\n')
        codes.append(code)
    # Get messages
    for dd in dds:
        message = ''.join(dd.findAll(text=True))
        message = message.encode('utf8')
        message = ' '.join(message.split())
        messages.append(message)
    for x,y in zip(codes, messages):
        results.append([x,y])
    return results

def get_tables(soup):
    try:
        tables = soup.findAll('table')
    except AttributeError, e:
        print >> sys.stderr, "TableError: ", e
        return None
    return tables

def get_links(parent):
    """ Get links and error names 
    """
    link = []
    links = parent.findAll('a', href=True)
    for l in links:
        link.append([l['href'],l.string])    
    return link

def write_data_csv(outfilename, data):
    """ Write the data in csv format to outfilename
    """
    outfilename = outfilename+'.csv'
    with open(outfilename, "wb") as outfile:
       wr = csv.writer(outfile)
       wr.writerows(data)

def scrap_google(soup, filename):
    """ Scraps Error codes for Google Adwords
    """
    divtags = soup.findAll("div", {"class" : "tree"})
    # Get errorclass links and names
    links = get_links(divtags[2])
    dataset = []
    urlprefix = 'https://developers.google.com/adwords/api/docs/reference/v201509/'
    # Go to each link and scrap codes
    for link in links:
        url = urlprefix+str(link[0])
        page = make_soup(url)
        desclists = page.findAll('dl')
        data = parse_desclist(desclists[len(desclists)-1])
        outfilename = ''+str(link[1])
        write_data_csv(outfilename, data)
        dataset.append(data)
    dataset = reduce(lambda x,y: x+y, dataset)
    write_data_csv((filename+'_all_dump'), dataset)

def scrap_bing(soup, filename):
    """ Scraps Error codes for Bing Ads
    """    
    tables = get_tables(soup)
    if tables == None:
        return None
    for table in tables[1:]:
        try:
            rows = table.findAll('tr')
        except AttributeError, e:
            print >> sys.stderr, "RowError: ", e
            return None
        dataset = parse_rows(rows[1:])
    filename = filename + '_all_dump'
    write_data_csv(filename, dataset)
# End of def scrap_bing

def scrap_baidu(soup, filename):
    """ Scraps Error codes for Baidu
    """    
    tables = get_tables(soup)
    data = []
    namelist = []
    nametags = soup.findAll('h3')
    for nametag in nametags[1:]:
        name = ''.join(nametag.findAll(text = True))
        name = name.encode('utf8')
        name = '_'.join(name.split())
        namelist.append(name)
    print namelist
    index = 0
    if tables == None:
        return None
    for table in tables:
        try:
            rows = table.findAll('tr')
        except AttributeError, e:
            print >> sys.stderr, "RowError: ", e
            return None
        table_data = parse_rows(rows[1:])
        
        data.append(table_data)
        outfilename = filename + '_' +str(namelist[index])
        write_data_csv(outfilename, table_data)
        index = index+1
    # Flatten list
    data = reduce(lambda x,y: x+y, data)
    filename = filename + '_all_dump'
    write_data_csv(filename, data)
# End of def scrap_baidu

def scrap_yandex(soup, filename):
    """ Scraps Error codes for Yandex
    """
    tables = get_tables(soup)
    tables = tables[1:]
    dataset = []
    if tables == None:
        return None
    for table in tables:
        try:
            tbody = table.findAll('tbody')
        except AttributeError, e:
            print >> sys.stderr, "AttributeError: ", e
        for entry in tbody:
            try:
                rows = entry.findAll('tr')
            except AttributeError, e:
                print >> sys.stderr, "RowError: ", e
            rowindex = 1
            if entry == tbody[0]:
                errorclass = ''.join(rows[1].findAll(text=True))
                rowindex = 2
            else:
                errorclass = ''.join(rows[0].findAll(text=True))
            errorclass = errorclass.encode('utf8')
            errorclass = '_'.join(errorclass.split())

            data = parse_rows(rows[rowindex:])
            dataset.append(data)
            # Write to files
            outfilename = filename + '_' +str(errorclass)
            write_data_csv(outfilename, data)
    # Flatten list
    dataset = reduce(lambda x,y: x+y, dataset)
    filename = filename + '_all_dump'
    write_data_csv(filename, dataset)
# End of def scrap_yandex(soup,filename)

SE_FUNCTION_DICT = {
    'bing'      :   scrap_bing,
    'baidu'     :   scrap_baidu,
    'yandex'    :   scrap_yandex,
    'google'    :   scrap_google,
    }

def main():
    args = parse_arguments()
    url = SE_URL_MAP[args.search_engine]
    filename = args.file_name

    soup = make_soup(url)

    # Call concerned function to scrap
    dataset = SE_FUNCTION_DICT[args.search_engine](soup, filename)
    
    if dataset==None:
        return False
    # Return success
    return True
    
if __name__ == '__main__':
    status = main()
    sys.exit(status)
