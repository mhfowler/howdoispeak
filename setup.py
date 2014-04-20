"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['munging/iphone_backup_upload.py']
DATA_FILES = ["munging/secrets.json"]
OPTIONS = {
    'argv_emulation': True,
    'iconfile':'green_circles.icns',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    py_modules=["munging.common"]
)
