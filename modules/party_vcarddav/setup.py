#!/usr/bin/env python
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from setuptools import setup
import re
import os
import ConfigParser


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

config = ConfigParser.ConfigParser()
config.readfp(open('tryton.cfg'))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
major_version, minor_version, _ = info.get('version', '0.0.1').split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)

requires = ['vobject >= 0.8.0', 'PyWebDAV >= 0.9.8']
for dep in info.get('depends', []):
    if not re.match(r'(ir|res|webdav)(\W|$)', dep):
        requires.append('trytond_%s >= %s.%s, < %s.%s' %
            (dep, major_version, minor_version, major_version,
                minor_version + 1))
requires.append('trytond >= %s.%s, < %s.%s' %
    (major_version, minor_version, major_version, minor_version + 1))

setup(name='trytond_party_vcarddav',
    version=info.get('version', '0.0.1'),
    description='Tryton module for CardDAV',
    long_description=read('README'),
    author='Tryton',
    url='http://www.tryton.org/',
    download_url=("http://downloads.tryton.org/" +
        info.get('version', '0.0.1').rsplit('.', 1)[0] + '/'),
    package_dir={'trytond.modules.party_vcarddav': '.'},
    packages=[
        'trytond.modules.party_vcarddav',
        ],
    package_data={
        'trytond.modules.party_vcarddav': (info.get('xml', [])
            + ['tryton.cfg', 'locale/*.po']),
        },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Framework :: Tryton',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Legal Industry',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: Bulgarian',
        'Natural Language :: Czech',
        'Natural Language :: Dutch',
        'Natural Language :: English',
        'Natural Language :: French',
        'Natural Language :: German',
        'Natural Language :: Russian',
        'Natural Language :: Spanish',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Office/Business',
        ],
    license='GPL-3',
    install_requires=requires,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    party_vcarddav = trytond.modules.party_vcarddav
    """,
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
    )
