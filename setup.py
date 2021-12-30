from setuptools import setup, find_packages

VERSION = '0.1'
DESCRIPTION = 'A crawler for exploring player profiles on chess.com'

setup(
    name = "chess_crawler",
    version = VERSION,
    author="Oskari Timgren",
    author_email="<oskari.timgren@gmail.com>",
    description=DESCRIPTION,
    packages=find_packages(where = 'src'),
    package_dir = {'':"src"},
    install_requires=['bs4', 'js2py', 'mysqlclient', 'numpy', 'pandas',
                         'requests', 'sqlalchemy', 'sqlalchemy_utils','tqdm'],    
    keywords=['python'],
)