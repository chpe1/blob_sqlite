# BLOB SQLITE

## Table of Contents
1. [General Info](#general-info)
2. [Technologies](#technologies)
3. [Installation](#installation)

### General Info
***
This script creates a copy of a sqlite database, parses the BLOB tables and, for each table found, creates a new BLOB_TEXT table in which the ASCII characters of the original table have been extracted.
This allows to query on this new table.
The script requires a SQLITE database as input.

### Library
***
* [BINARY2STRING](https://github.com/glmcdona/binary2strings)

### Installation
***

Warning, this script uses the binary2strings library. It is recommended to install Visual Studio 2019 to use this library.

```
$ git clone https://github.com/chpe1/blob_sqlite.git  
$ cd ../path/to/the/file  
$ pip install --upgrade -r requirements.txt  
$ python main.py mybase.db
```
