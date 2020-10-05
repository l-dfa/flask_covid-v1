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

To run fuctional tests, you need Geckodriver installed in your system. Then,
in cmd as usual::

  cd flask_covid
  venv\Scripts\activate   # or venv/bin/activate on Linux
  cd tests
  python functional_tests.py
  
To install the production environment
----------------------------------------

Here I show the general guidelines to follow to configure a
WEB server with this application. I hide here and there some details. Please
be warned about this: you need to do some googling to get them.

I wrote these guidelines after the installation of ver.1.0
of flask_covid on my site, without a double check. So: BE CAREFUL. I do
not assume responsabilites!

Using a CentOS 7 server, with Python 3 (as python), Nginx installed, and
TCP port 5000 enabled.
Using root account, in Bash, we install the application::

  cd /usr/share/nginx/html
  git clone https://github.com/l-dfa/flask_covid-v1.git    # get application
  ren flask_covid-v1 flask_covid
  cd flask_covid
  python -m venv venv                     # install project's python virtual environment
  venv/bin/activate                       # activate project's virtual env.
  python -m pip install --upgrade pip     # upgrade pip of this virtual env.
  pip install -r requirements.txt         # get libraries
  pip install gunicorn                    # get gunicorn
  
  # application configuration
  mkdir logs                              # here we'll put nginx logs
  mkdir instance                          # application configuration
  mkdir instance\data
  mkdir instance\logs                     # and here application logs
  copy  configs\config.cfg instance\config.cfg
  copy  configs\default_config.cfg  instance\default_config.cfg    # edit this file contents to adapt to your needs
  copy  configs\covid-20200424.csv  instance\data\covid19-worldwide.csv
  
  # to test the application run (not unit/functional tests!):
  gunicorn --bind 127.0.0.1:5000 wsgi:app
  # in another bash:
  wget http://127.0.0.1:5000  # you'll get index.html file, please check it. If not, check configuration
  # previous bash: stop local gunicorn (ctrl+c)
  
Then, configure gunicorn service. In /etc/systemd/system directory
write a gunicorn_covid.service file with these contents::

  [Unit]
  Description=covid gunicorn daemon
  
  [Service]
  Type=simple
  User=root
  WorkingDirectory=/usr/share/nginx/html/flask_covid
  Environment="PATH=/usr/share/nginx/html/flask_covid/venv/bin"
  Environment="SECRET_KEY=put_here_your_secret_key"
  ExecStart=/usr/share/nginx/html/flask_covid/venv/bin/gunicorn --bind 127.0.0.1:5000  -w 4  wsgi:app
  
  [Install]
  WantedBy=multi-user.target

Then start the gunicorn_covid service::

  systemctl daemon-reload
  systemctl start gunicorn_covid
  systemctl status -l gunicorn_covid      # this must say gunicorn_covid is running
  wget http://127.0.0.1:5000              # you'll get index.html file, please check it

We are almost there. Now we need "only" to configure nginx as proxy from 
server:80 to 127.0.0.1:5000. We are not going do show how configure https certificate
using Certbot, even if this is an https site configuration.
In /etc/nginx/sites-available put your site configuration file. For example
the file your_site.com with this contents::

  server {
      # listen   80;
      server_name your_site.com;
  
      root         /usr/share/nginx/html/flask_covid;
      index index.html index.htm;
  
      access_log /usr/share/nginx/html/flask_covid/logs/access.log;
      error_log  /usr/share/nginx/html/flask_covid/logs/error.log warn;
  
  
      location /the_indicated_google_file.html {
          alias /usr/share/nginx/html/flask_covid/covid/static/the_indicated_google_file.html;
      }
  
      location / {
          proxy_pass       http://127.0.0.1:5000/;      # THIS is the key point: redirect from port 80 to localhost:5000
          proxy_redirect   off;
  
          proxy_set_header Host $http_host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          
      }
  
   # managed by Certbot
  
      listen 443 ssl; # managed by Certbot
      ssl_certificate /etc/letsencrypt/live/covid.defalcoalfano.it/fullchain.pem; # managed by Certbot
      ssl_certificate_key /etc/letsencrypt/live/covid.defalcoalfano.it/privkey.pem; # managed by Certbot
      include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
      ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
  
  }
  
  server {
      if ($host = your_site.com) {
          return 301 https://$host$request_uri;
      } # managed by Certbot
  
      listen 80;
      server_name your_site.com;
      return 301 https://$host$request_uri;
      #return 404; # managed by Certbot
  }
  
Now we enable the site linking it from the enabled sites directory and
restarting nginx::


  ln -s /etc/nginx/sites-available/your_site.com /etc/nginx/sites-enabled/
  nginx -t                                                # check configuration syntax errors
  systemctl restart nginx                                 # nginx restart
  wget https://your_site.com                              # for sure you'll get index.html, isn't it?
  


License
----------

`CC BY-SA 4.0 <https://creativecommons.org/licenses/by-sa/4.0/>`_

