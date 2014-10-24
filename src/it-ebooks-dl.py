import os
import datetime
import threading
import queue
import urllib.request
import urllib.error
from html.parser import HTMLParser


########## Edit these
dl_dir = 'X:\\test'
dl_next = 10
num_threads = 5
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
        self._q = queue.Queue()
        #create thread pool
        for i in range(num_threads):
            t = threading.Thread(target=self._parse_start)
            t.daemon = True
            t.start()
        #fill queue
        start = self._get_curr_count()
        last_book_num = 0
        for num in range(start, start+dl_next):
            last_book_num = num
            self._q.put(num)
        #wait until all threads are complete
        self._q.join()
        self._save_curr_count(last_book_num)

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

    def _parse_start(self):
        while True:
            num = self._q.get()
            self._parse_worker(num)
            self._q.task_done()

    def _parse_worker(self, book_num):
        url = "http://it-ebooks.info/book/"+str(book_num)
        try:
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request)
            html = response.read().decode('utf-8')
            parser = MyHTMLParser()
            parser.clear()
            parser.feed(html)
            parser.book_data['url'] = url
            parser.book_data['num'] = book_num
            print("Parsed : ["+str(book_num)+"] "+parser.book_data['name'])
            self._dl_worker(parser.book_data)
        except urllib.error.HTTPError as err:
            errors.append("Error Code "+err.code+" with link "+url)
            print("Up to date with books")
        except:
            errors.append("some error")

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
                    print("DL'ing: ["+str(book['num'])+"] "+book['name'])
                    header_stuff = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
                                    'Referer': book['url'],
                                    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
                    with urllib.request.urlopen(
                            urllib.request.Request(book['dl_link'], headers=header_stuff)) as response, \
                            open(new_file, 'wb') as out_file:
                        data = response.read()
                        out_file.write(data)
                else:
                    print("Have: ["+str(book['num'])+"] "+book['name'])
                    errors.append("Book: ["+str(book['num'])+"] "+book['name']+" is already dl\'ed")
        else:
            print("Not English: ["+str(book['num'])+"] "+book['name'])
            errors.append("Book: ["+str(book['num'])+"] "+book['name']+" is not in english")



if __name__ == '__main__':
    errors = []
    start_time = datetime.datetime.now().replace(microsecond=0)
    dl_ebooks = GetEbooks()
    print("\n\nRun Time: " + str(datetime.datetime.now().replace(microsecond=0) - start_time))
    for error in errors:
        print(error)