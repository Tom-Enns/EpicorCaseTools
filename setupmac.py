#to run this setup enter the following in the terminal:  python setupmac.py py2app
from setuptools import setup

APP = ['ui.py']
DATA_FILES = [('', ['CaseToolsIcon.icns', 'gear.png'])]
OPTIONS = {
    'argv_emulation': True,
    'packages': ['requests', 'charset_normalizer', 'chardet'],
    'iconfile': 'CaseToolsIcon.icns',
    'plist': {
        'CFBundleName': 'Epicor Case Tools',
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)