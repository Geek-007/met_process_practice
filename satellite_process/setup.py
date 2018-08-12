#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 yangkang <yangkang@gagogroup.com>. All rights reserved.
from setuptools import setup, find_packages

maintainer = '杨康'
maintainer_email = 'yangkang@gagogroup.com'
author = maintainer
author_email = maintainer_email
short_description = "遥感数据处理工具"

long_description = """

"""

install_requires = [
]
version = '1.0'

NAME = 'rstools'
PACKAGES = [NAME] + ["%s.%s" % (NAME, i) for i in find_packages(NAME)]
url = ''
download_url = ''
classifiers = [
    'Programming Language :: Python :: 3.5'
]
setup(author=author,
      version=version,
      author_email=author_email,
      description=short_description,
      long_description=long_description,
      install_requires=install_requires,
      maintainer=maintainer,
      name=NAME,
      packages=PACKAGES,
      url=url,
      download_url=download_url,
      classifiers=classifiers,
      package_data={
            "rstools":["./*"]
      },
      include_package_data=True
      )
