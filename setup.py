#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup for ITBConcierge."""

import io
import re

from setuptools import find_packages, setup


def readme():
    with io.open('README.md', encoding='utf-8') as fp:
        return fp.read()


setup(
    name='itbconcierge',
    version='1.0.0',
    description="ITB Concierge promotes good communication.",
    long_description=readme(),
    long_description_content_type='text/markdown',
    author='Yusuke Oya',
    author_email='curio@antique-cafe.net',
    url='https://github.com/curio184/itbconcierge',
    license='MIT',
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='slack ethereum token-economy',
    install_requires=[
        'sqlalchemy',
        'reslackbot',
        'requests==2.22.0',
        'pyopenssl',
        'web3==5.4.0',
        'cobra_hdwallet',
        'cytoolz',
        'typing',
        'sqlalchemy-migrate'
    ],
)
