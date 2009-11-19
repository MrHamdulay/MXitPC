from distutils.core import setup
import py2exe
import os
import os.path
import sys

if len(sys.argv) == 1:
    sys.argv.append("py2exe")

directories = [os.path.join('gui', 'glade'),
               os.path.join('gui', 'images'),
               os.path.join('gui', 'images', 'chatemoti'),
               os.path.join('gui', 'images', 'moods'),
               os.path.join('gui', 'images', 'presence'),
               'sounds',
               'data',
              ]
MXit_data_files= []
for folder in directories:
    for files in os.listdir(folder):
        file = os.path.join(folder, files)
        if os.path.isfile(file):
            MXit_data_files.append((folder, [file]))

setup(
    name='MXitPC',
    version='beta 1',
    description='MXit PC Client',
    windows=[
        {
        'script': 'main.py',
        'icon_resources': [(1, os.path.join('gui', 'images', 'desktop.ico'))],
        }
    ],
    options = {
        'py2exe': {
            'packages':'encodings',
            'includes': 'cairo, pango, pangocairo, atk, twisted.web.resource, twisted, zope.interface',
            'excludes': 'gtk.glade',
            'compressed': 1,
            'optimize': 2,
        },
        
    },
    zipfile = "data/library.zip",
    data_files = MXit_data_files,
)
