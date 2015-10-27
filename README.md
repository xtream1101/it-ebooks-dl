# Depreciated, use project [scrape-itebooks](https://github.com/xtream1101/scrape-itebooks)


it-ebooks-dl
============

Downloads all e-books from it-ebooks.info


Requires
--------

* Python 3.4


Vars
----
 
  * `g_dl_dir` - Directory to download e-books to (must exist)
  * `g_json_save` - File to save the parsed json data to
  * `g_num_parse_threads` - Number of threads for the parser to use
  * `g_num_dl_threads` - Number of threads for the downloader to use


Use
---

1. Change the vars as needed (bottom of script)
2. Run in the command line by just calling this .py script with no args. 
    * Each time you do, it will parse any books you do not have in your json file and add them to it.
    * It will then download any missing e-books 
