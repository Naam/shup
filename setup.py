#!/usr/bin/env python
# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

import shup

setup(name='shup',
      version=shup.__version__,

      author='Nahim El Atmani',
      author_email='nahim+dev@naam.me',
      license="GPL3",

      url='https://github.com/Naam/shup',
      description='File sharing (images, code snippets, movies...) made easy.',
      long_description=open("README.rst").read(),
      keywords="upload sharing share file tool upload snippet code image",

      python_requires='>=3',
      provides=['shup'],
      install_requires=["paramiko>=1.16.0", "progressbar2>=3.34.3"],
      packages=find_packages(),
      package_data={
         'shup': ['shup.cfg'],
         },

      entry_points={
         'console_scripts': [
            'shup = shup.shup:main',
            ],
         },

      classifiers=['Development Status :: 4 - Beta',
         'Intended Audience :: System Administrators',
         'Intended Audience :: Information Technology',
         'Natural Language :: English',
         'Operating System :: OS Independent',
         'Programming Language :: Python :: 3',
         'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
         'Topic :: System :: Archiving',
         'Topic :: Communications :: File Sharing',
         'Programming Language :: Python :: 3',
         'Programming Language :: Python :: 3.2',
         'Programming Language :: Python :: 3.3',
         'Programming Language :: Python :: 3.4',
         'Programming Language :: Python :: 3.5',
         'Programming Language :: Python :: 3.6',
         'Programming Language :: Python :: 3.7',
         ],
      )
