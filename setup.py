#!/usr/bin/env python

from setuptools import setup

_depends = '''
numpy
'''

setup( \
  name='symath', \
  version='0.1.17', \
  description='symbolic mathematics for python', \
  author='Brandon Niemczyk', \
  author_email='brandon.niemczyk@gmail.com', \
  url='http://github.com/bniemczyk/symbolic', \
  packages=['symath', 'symath.solvers', 'symath.graph'], \
  test_suite='tests', \
  license='BSD', \
  install_requires=_depends, \
  classifiers = [ \
    'Development Status :: 3 - Alpha', \
    'Intended Audience :: Developers', \
    'Intended Audience :: Science/Research', \
    'License :: OSI Approved :: BSD License', \
    'Topic :: Scientific/Engineering :: Mathematics' \
    ]
  )
