#!/usr/bin/env python

from setuptools import setup

setup( \
  name='symath', \
  version='0.1.13', \
  description='symbolic mathematics for python', \
  author='Brandon Niemczyk', \
  author_email='brandon.niemczyk@gmail.com', \
  url='http://github.com/bniemczyk/symbolic', \
  packages=['symath', 'symath.solvers'], \
  test_suite='tests', \
  license='BSD', \
  classifiers = [ \
    'Development Status :: 3 - Alpha', \
    'Intended Audience :: Developers', \
    'Intended Audience :: Science/Research', \
    'License :: OSI Approved :: BSD License', \
    'Topic :: Scientific/Engineering :: Mathematics' \
    ]
  )
