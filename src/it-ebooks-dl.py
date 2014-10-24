import urllib.request
import urllib.error
from html.parser import HTMLParser




class MyHTMLParser(HTMLParser):
    def clear(self):
        self.book_data = {}
        self.item_found = {}
        self.looking_for = {'name': 'h1',
                            'publisher': 'a',
                            'datePublished': 'b',
                            'inLanguage': 'b',
                            'bookFormat': 'b'
                           }

    def handle_starttag(self, tag, attrs):
        #find everything we are looking_for
        for item, my_tag in self.looking_for.items():
            if tag == my_tag and ('itemprop', item) in attrs:
                self.item_found[item] = True
        #get download link
        if tag == 'a' and 'href' == attrs[0][0] and attrs[0][1].startswith('http://filepi.com'):
            self.book_data['dl_link'] = attrs[0][1]

    def handle_data(self, data):
        #save the data we are looking for
        for item, found in self.item_found.items():
            if found:
                self.book_data[item] = data
                self.item_found[item] = False





dl_dir = 'X:\\test'
start = 1
dl_next = 2
books = []
for i in range(1,start+dl_next):
    print("Started",i)
    url = "http://it-ebooks.info/book/"+str(i)
    try:
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        html = response.read().decode('utf-8')
        parser = MyHTMLParser()
        parser.clear()
        parser.feed(html)
        parser.book_data['url'] = url
        parser.book_data['num'] = i
        books.append(parser.book_data)
    except urllib.error.HTTPError as err:
        print("Error Code",err.code,"with link",url)


print(books)

for book in books:
    if book['inLanguage'].lower() == 'english':
        print("getting book:"+book['name'])
        header_stuff = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
                        'Referer': book['url'],
                        'Accept':"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        with urllib.request.urlopen(
                urllib.request.Request(book['dl_link'], headers=header_stuff)) as response, \
                open(dl_dir+'\\'+book['publisher']+' - '+book['name']+' ('+book['datePublished']+').'+book['bookFormat'].lower(), 'wb') as out_file:
            data = response.read()
            out_file.write(data)
    else:
        print('Book: '+book['num']+' is not in English')
