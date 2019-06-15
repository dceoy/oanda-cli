#!/usr/bin/env python

from setuptools import find_packages, setup

from oandacli import __version__

setup(
    name='oanda-cli',
    version=__version__,
    description='Command Line Interface for Oanda API',
    packages=find_packages(),
    author='Daichi Narushima',
    author_email='dnarsil+github@gmail.com',
    url='https://github.com/dceoy/oanda-cli',
    include_package_data=True,
    install_requires=[
        'docopt', 'pandas', 'pyyaml', 'redis', 'ujson', 'v20'
    ],
    entry_points={
        'console_scripts': ['oanda-cli=oandacli.cli.main:main'],
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Internet',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment'
    ],
    long_description="""\
oanda-cli
---------

Command Line Interface for Oanda API
"""
)
