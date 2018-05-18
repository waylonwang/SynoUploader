from distutils.core import setup
import py2exe

APP = ['SynoUploader.py']
DATA_FILES = ['icons','setting.cfg']
options = {'iconfile':'icons/SynoUploader.icns'}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
