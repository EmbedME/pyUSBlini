# This file is part of the pyUSBlini project.
#
# Copyright(c) 2021-2024 Thomas Fischl (https://www.fischl.de)
# 
# pyUSBlini is free software: you can redistribute it and/or modify
# it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyUSBlini is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# along with pyUSBlini.  If not, see <http://www.gnu.org/licenses/>

from setuptools import setup

setup(name='usblini',
      version='1.2',
      description='USBlini - USB to LIN interface',
      long_description=open('README.md').read(),
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5'
      ],
      url='https://github.com/EmbedME/pyUSBlini',
      author='Thomas Fischl',
      author_email='tfischl@gmx.de',
      license="LGPL-3.0",
      packages=['usblini'],
      install_requires=[
          'libusb1',
      ],
      zip_safe=False)
