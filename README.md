Stock
=====

A Flask-based webshop with pjax. 


About Flask
-----------
[Flask][flask] is a BSD-licensed microframework for Python based on
[Werkzeug][wz], [Jinja2][jinja2] and good intentions.

See <http://flask.pocoo.org> for more info.


Setup/Configuration
-------------------
1. Download this repository via
   `git clone git@github.com:hobbyhobbit/Stock.git`


TODO: mention makefile

2. Add the secret keys for CSRF protection by running the `generate_keys.py`
   script at `src/application/generate_keys.py`, which will generate the
   secret keys module at src/application/secret_keys.py

Add the following to your .(git|hg|bzr)ignore file to keep the secret keys
out of version control:

<pre class="console">
  # Keep secret keys out of version control
  secret_keys.py
</pre>


Install python dependencies
---------------------------
The local dev environment requires installation of Jinja2, PIL, and simplejson,
which can be installed via:

<pre class="console">
  pip install -r requirements_dev.txt
</pre>


Start the Application
-------------------------
To run the application using WSGI:
<pre class="console"> 
    ...    
</pre>


Licenses
--------
See licenses/ folder


Package Version
---------------


Credits
-------

Project based on the [Flask on App Engine Project Template][gaet] by Kamal Gill

[Font Awesome][fontawesome] by Dave Gandy

[Pjax] by Chris Wanstrath

Teacher illustration by Wilhelm Busch (Public domain), via [Wikimedia Commons][Busch]

[Busch]: http://commons.wikimedia.org/wiki/File%3AMax_und_Moritz_(Busch)_040.png
[Pjax]: https://github.com/defunkt/jquery-pjax
[gaet]: https://github.com/kamalgill/flask-appengine-template
[flask]: http://flask.pocoo.org
[fontawesome]: http://fortawesome.github.com/Font-Awesome/
[jinja2]: http://jinja.pocoo.org/2/documentation/
[wz]: http://werkzeug.pocoo.org/
