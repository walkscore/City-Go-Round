Getting Started With Agency Data
--------------------------------

To get your local dev server filled with agencies, simply do the following:

    cd /path/to/sources
    ./data/do_data_import

After you've imported, visit the following URL to properly set their locations:

    http://localhost:8080/admin/feeds/update/

Remember that `appcfg.py` must be on your path. (It should be if you installed the App Engine SDK.)



Building Agency Data From Scratch
---------------------------------

You probably don't need to do this as we always check in `agencies.csv`, the output of this process. However, if you need to rebuild, here's how:

Input files:

    service.csv - ntdid => passenger_miles
    ntdprogram.csv - canonical agency name => agency contact information
    ntd_agencies.csv - base NTD agency list
    gtfs_data_exchange_ids.csv - ntdid => gtfs_data_exchange_id
  
Build `agencies.csv` from input files. This takes a while, because geocoding is fairly slow.

    $ python compile_importable_csv.py

use the bulk importer to load everything into the db

    $ cd ..
    $ export PYTHONPATH=/path/to/sources:path/to/sources/citygoround
    $ export DJANGO_SETTINGS_MODULE=settings
    $ /path/to/google_appengine/appcfg.py upload_data . --filename=./data/agencies.csv --kind=Agency --config_file=./data/agency_loader.py --url=http://localhost:8080/remote_api --has_header

After you've imported, visit the following URL to properly set their locations:

    http://localhost:8080/admin/feeds/update/

