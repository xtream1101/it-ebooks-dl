import os
import json
import datetime
import threading
import queue
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
        # Find everything we are looking_for
        for item, my_tag in self.looking_for.items():
            if tag == my_tag and ('itemprop', item) in attrs:
                self.item_found[item] = True
        # Get download link
        if tag == 'a' and 'href' == attrs[0][0] and attrs[0][1].startswith('http://filepi.com'):
            self.book_data['dl_link'] = attrs[0][1]

    def handle_data(self, data):
        # Save the data we are looking for
        for item, found in self.item_found.items():
            if found:
                self.book_data[item] = data
                self.item_found[item] = False


class CreateJSON:
    def __init__(self, book_list):
        self._book_list_file = book_list
        self._output_list = {}
        self._saved_list = {}
        self._curr_count = 1
        self._last_book = False
        self._error404_group = 0  # Num of 404's in together
        self._load_list()

        self._q = queue.Queue()
        for i in range(g_num_parse_threads):
            t = threading.Thread(target=self._parse_start)
            t.daemon = True
            t.start()

        while not self._last_book:
            end_count = self._curr_count+g_num_parse_threads
            for item in range(self._curr_count, end_count):
                self._q.put(item)
            self._curr_count = end_count

            self._q.join()

        print("\n")
        self._save_list()

    def _save_list(self):
        json_to_save = dict(list(self._output_list.items()) + list(self._saved_list.items()))
        with open(self._book_list_file, 'w') as outfile:
            json.dump(json_to_save, outfile, sort_keys=True,  indent=4)

    def _load_list(self):
        try:
            with open(self._book_list_file) as data_file:
                data = json.load(data_file)
        except:
            pass
        else:
            self._saved_list = data

    def _parse_start(self):
        while True:
            num = self._q.get()
            print("Parsed: "+str(num)+" books\tElapsed Time: " + elapsed_time(), end='\r')
            self._parse_worker(num)
            self._q.task_done()

    def _parse_worker(self, book_num):
        """
        Parse the page for the book information
        """
        if str(book_num) not in self._saved_list:  # Do not parse the page if we already have that book data
            url = "http://it-ebooks.info/book/"+str(book_num)
            try:
                request = urllib.request.Request(url)
                response = urllib.request.urlopen(request)
                html = response.read().decode('utf-8')
            except:
                errors.append("Error: Book #"+str(book_num))
            else:
                # Catch 404 page
                if html.find('Page Not Found') != -1:
                    self._error404_group += 1
                    if self._error404_group > 10:  # If we hid 10 404 pages in a row we know we reached the end
                        self._last_book = True
                else:
                    self._error404_group = 0
                    # Parse page
                    parser = MyHTMLParser()
                    parser.clear()
                    parser.feed(html)
                    parser.book_data['url'] = url
                    parser.book_data['num'] = book_num
                    self._output_list[int(book_num)] = parser.book_data


class DownloadEbooks:
    def __init__(self, book_list):
        self._book_list_file = book_list
        self._saved_list = {}
        self._load_list()
        self._num_books = len(self._saved_list)
        self._current_count = 0

        self._q = queue.Queue()
        for i in range(g_num_dl_threads):
            t = threading.Thread(target=self._dl_start)
            t.daemon = True
            t.start()

        for key in self._saved_list:
            self._q.put(key)

        self._q.join()
        print("\n")

    def _load_list(self):
        try:
            with open(self._book_list_file) as data_file:
                data = json.load(data_file)
        except:
            pass
        else:
            self._saved_list = data

    def _dl_start(self):
        while True:
            num = self._q.get()
            self._current_count += 1
            print(str(self._current_count)+' out of '+str(self._num_books)+"\tElapsed Time: "+elapsed_time(), end='\r')
            self._dl_worker(self._saved_list[num])
            self._q.task_done()

    def _dl_worker(self, book):
        """
        Download the e-book
        """
        if book['inLanguage'].lower() == 'english':
            book['publisher'] = self._sanitize(book['publisher'])
            book['name'] = self._sanitize(book['name'])
            file_dir = g_dl_dir+'/'+book['publisher']+'/'
            try:
                os.makedirs(file_dir)
            except:
                pass
            finally:
                if book['bookFormat'] is None:
                    book['bookFormat'] = 'pdf'
                ext = book['bookFormat'].lower()
                file_name = book['publisher']+' - '+book['name']+' ('+book['datePublished']+').'+ext
                new_file = file_dir+file_name

                dl_file = True
                if os.path.isfile(new_file):
                    dl_file = False
                    # If file exists, but is under 100kb, then re-download
                    if os.path.getsize(new_file) < 100 * 1024:
                        dl_file = True
                        os.remove(new_file)

                if dl_file:
                    header_stuff = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
                                    'Referer': book['url']}
                    dl_success = False
                    while not dl_success:
                        with urllib.request.urlopen(
                                urllib.request.Request(book['dl_link'], headers=header_stuff)) as response, \
                                open(new_file, 'wb') as out_file:
                            data = response.read()
                            out_file.write(data)
                        # If file did not fully dl, try again
                        if os.path.getsize(new_file) < 100 * 1024:
                            errors.append("Re-downloaded: ["+str(book['num'])+"] "+book['name'])
                            dl_success = False
                            os.remove(new_file)
                        else:
                            dl_success = True
        else:
            errors.append("Book: ["+str(book['num'])+"] "+book['name']+" is not in english")

    def _sanitize(self, string):
        """
        Catch and replace and invalid windows filename chars
        """
        replace_chars = [
            ['\\', '-'], [':', '-'], ['/', '-'],
            ['?', ''],   ['<', '>'], ['`', '`'],
            ['|', '-'],  ['*', '`'], ['"', '\'']
        ]
        for ch in replace_chars:
            string = string.replace(ch[0], ch[1])
        return string


def elapsed_time():
    return str(datetime.datetime.now().replace(microsecond=0) - start_time)

if __name__ == '__main__':
    ########## Edit these
    g_dl_dir = 'X:/downloads/ebooks/it-ebooks'
    g_json_save = g_dl_dir+'/it-ebooks.json'
    g_num_parse_threads = 10
    g_num_dl_threads = 5
    ########## STOP edit

    errors = []
    start_time = datetime.datetime.now().replace(microsecond=0)
    # Create json file by parsing the site
    book_parse = CreateJSON(g_json_save)
    # Download ebooks that were parsed
    book_dl = DownloadEbooks(g_json_save)
    for error in errors:
        print(error)