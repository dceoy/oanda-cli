#!/usr/bin/env python

from setuptools import find_packages, setup

from oandacli import __version__

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='oanda-cli',
    version=__version__,
    author='Daichi Narushima',
    author_email='dnarsil+github@gmail.com',
    description='Command Line Interface for Oanda API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dceoy/oanda-cli',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'docopt', 'pandas', 'pyyaml', 'redis', 'ujson', 'v20'
    ],
    entry_points={'console_scripts': ['oanda-cli=oandacli.cli.main:main']},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3',
        'Topic :: Office/Business :: Financial :: Investment'
    ],
    python_requires='>=3.6'
)
