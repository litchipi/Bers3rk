#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
     name='bers3rk',
     version='0.1',
     author="Litchi Pi",
     author_email="litchi.pi@protonmail.com",
     description="A easily customizable bruteforce performer",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/litchipi/Bers3rk",
     packages=['bers3rk'],
     license="GPLv3",
     classifiers=[
         "Programming Language :: Python :: 3",
     ],
 )
