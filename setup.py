#!/usr/bin/env python

from distutils.core import setup
from distutils.cmd import Command

class TestCommand(Command):
  user_options = []

  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  def run(self):
    import sys, subprocess
    raise SystemExit(subprocess.call(['trial','txframed']))


setup(name='txframed',
      version='0.9',
      url='http://github.com/mmattice/txframed/',
      description='Twisted Python Framed Protocol Support',
      author='Michael Mattice',
      author_email='mike@mattice.org',
      packages=['txframed',],
      install_requires = ['twisted'],
      license='apache',
      keywords = "twisted stx etx lrc",
      cmdclass = {'test': TestCommand},
      classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
      ],
     )
