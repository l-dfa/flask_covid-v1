flask_covid-v1
================

A simple web application to draw time series of cases of covid-19 
outbreak in selectable countries.

This is a major rework of a previous initial version of the same project.
So it's named from version 1.0+.

This project uses data from `European Centre for Disease Prevention and Control <https://www.ecdc.europa.eu/en>`_.
Data available in development environment range from 2019-12-31 to 2020-04-24.

If you wish an updated version of data, you can grab it 
`from this URL <https://opendata.ecdc.europa.eu/covid19/casedistribution/csv>`_
and substitute, using the same filename, ``.\covid\data\covid-20200424.csv``.
Alternatively, you can change the ``DATA_FILE`` value in ``.\configs\default_config.cfg`` file.

Prerequisites of the development environment
---------------------------------------------

Base environments:

* `git <https://git-scm.com/downloads>`_
* `python <https://www.python.org/downloads/>`_ >= 3.6

Third parties libraries:

* flask
* python-dotenv
* flask-wtf
* flask-babel
* pandas
* matplotlib
* beautifulsoup4
* lxml

Optionally, to translate to a language other than English, install:

* `poedit <https://poedit.net/download>`_

Optionally, to run functional tests:

* `geckodriver <https://github.com/mozilla/geckodriver/releases>`_.


To install the development environment
----------------------------------------

In cmd::

  git clone https://github.com/l-dfa/flask_covid-v1.git
  ren flask_covid-v1 flask_covid
  cd flask_covid
  python -m venv venv
  venv\Scripts\activate   # or venv/bin/activate on Linux
  python -m pip install --upgrade pip
  
Then if you wish to get the original project 3rd parties libraries::

  pip install -r requirements.txt
  
Otherwise, if you wish to install 3rd parties libraries from scratch
(it means: updated versions)::

  pip install flask
  pip install python-dotenv
  pip install flask-wtf
  pip install flask-babel
  pip install pandas
  pip install matplotlib
  pip install beautifulsoup4
  pip install lxml
  
Then some initial configuration::

  mkdir instance
  mkdir instance\data
  mkdir instance\logs
  copy  configs\config.cfg instance\config.cfg
  copy  configs\default_config.cfg  instance\default_config.cfg
  copy  configs\covid_data_test.csv instance\data\covid_data_test.csv
  copy  configs\covid-20200424.csv  instance\data\covid_data.csv
  
  
To exec application in development environment
-------------------------------------------------

In cmd, to run the development http server::

  cd flask_covid
  venv\Scripts\activate   # or venv/bin/activate on Linux
  flask run
  
Then, please, use a web browser to show http://localhost:5000


To add a language
------------------

flask_covid uses English as its primary language. If you wish to add another
language use this procedure::

  cd flask_covid
  venv\Scripts\activate   # or venv/bin/activate on Linux
  mkdir covid\translations     # where "it" is the requested language
  mkdir covid\translations\it  #   (italian in this case), substitute
  flask translate init it      #   it with your choice    
  # using poedit, please write the wanted translation in .\covid\translations\it\LC_MESSAGES\messages.po
  flask translate compile
                                  
In case you need to update, or to correct, the translations::

  cd flask_covid
  venv\Scripts\activate   # or venv/bin/activate on Linux
  flask translate update
  # using poedit, please write the wanted translation in .\covid\translations\it\LC_MESSAGES\messages.po
  flask translate compile
  
flask_covid is going to react to your browser language option. E.g.
using Firefox, in menu/Options/Language, in paragraph "*choose your
preferred language for diplaying pages*" you can choose what language
you wish to use to read Web pages; then, if the requested web site can
respond using your language is another pair of sleeves.


Test
--------------------

To run unit tests. In cmd::

  cd flask_covid
  venv\Scripts\activate   # or venv/bin/activate on Linux
  cd tests
  python unit_tests.py

To run fuctional tests, you need Geckodriver installed in your system, then
in cmd as usual::

  cd flask_covid
  venv\Scripts\activate   # or venv/bin/activate on Linux
  cd tests
  python functional_tests.py
  


License
----------

`CC BY-SA 4.0 <https://creativecommons.org/licenses/by-sa/4.0/>`_

