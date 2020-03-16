"""
WSGI config for expenses project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os, site, sys
from dotenv import load_dotenv

# Tell wsgi to add the Python site-packages to it's path.
site.addsitedir('/code/env/lib/python3.8/site-packages')

# Fix markdown.py (and potentially others) using stdout
sys.stdout = sys.stderr

# Calculate the path based on the location of the WSGI script.
project = os.path.dirname(os.path.dirname(__file__))
workspace = os.path.dirname(project)
sys.path.append(project)
sys.path.append(workspace)
project_folder = os.path.expanduser('~/code')  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

#import os

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "the_tool.settings"
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "the_tool.settings")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expenses.settings')

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
#from django.core.wsgi import get_wsgi_application
#application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)

# from django.core.handlers.wsgi import WSGIHandler
# application = WSGIHandler()

import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
application = get_wsgi_application()