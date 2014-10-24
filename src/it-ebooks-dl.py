import os
import sys
import datetime
import threading
import urllib.request
import urllib.error
from html.parser import HTMLParser


########## Edit these
dl_dir = 'X:\\test'
dl_next = 10
simultaneous_downloads = 5
save_count_file = 'current_count'
########## STOP edit


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


class GetEbooks:
    def __init__(self):
        self._books = []
        self._parse_links()

    def _save_curr_count(self, count):
        with open(save_count_file, 'w') as f:
            f.write(str(count+1))

    def _get_curr_count(self):
        if os.path.isfile(save_count_file):
            with open(save_count_file, 'r') as f:
                count = int(f.read())
            if not isinstance(count, int):
                count = 1
        else:
            count = 1
        return count

    def _parse_links(self):
        start = self._get_curr_count()
        for i in range(start, start+dl_next):
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
                self._books.append(parser.book_data)
                print("Parsed : ["+str(i)+"] "+parser.book_data['name'])
            except urllib.error.HTTPError as err:
                errors.append("Error Code "+err.code+" with link "+url)
                print("Up to date with books")
                break
            except:
                errors.append("some error")
        self._dl_ebooks()

    def _dl_worker(self, book):
        if book['inLanguage'].lower() == 'english':
            file_dir = dl_dir+'\\'+book['publisher']+'\\'
            try:
                os.makedirs(file_dir)
            except:
                pass
            finally:
                new_file = file_dir+book['publisher']+' - '+book['name']+' ('+book['datePublished']+').'+book['bookFormat'].lower()
                if not os.path.isfile(new_file):
                    print("getting book: "+book['name'])
                    header_stuff = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
                                    'Referer': book['url'],
                                    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
                    with urllib.request.urlopen(
                            urllib.request.Request(book['dl_link'], headers=header_stuff)) as response, \
                            open(new_file, 'wb') as out_file:
                        data = response.read()
                        out_file.write(data)
                else:
                    errors.append('Book: '+book['name']+' is already dl\'ed')
        else:
            errors.append('Book: '+book['num']+' is not in English')

    def _dl_ebooks(self):
        t = {}
        num = 0
        for book in self._books:
            num = book['num']
            t[num] = threading.Thread(target=self._dl_worker, args=(book,))
            t[num].start()
            if threading.active_count() <= simultaneous_downloads:
                continue
            else:
                self._save_curr_count(num)
                t[num].join()
        #wait until the last thread stops


if __name__ == '__main__':
    errors = []
    start_time = datetime.datetime.now().replace(microsecond=0)
    dl_ebooks = GetEbooks()
    print("\n\nRun Time: " + str(datetime.datetime.now().replace(microsecond=0) - start_time))
    for error in errors:
        print(error)