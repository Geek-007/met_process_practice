#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 yangkang <yangkang@gagogroup.com>. All rights reserved.
from setuptools import setup, find_packages

maintainer = '吴沁淳,杨康'
maintainer_email = 'wuqinchun@gagogroup.com, yangkang@gagogroup.com'
author = maintainer
author_email = maintainer_email
short_description = "数据下载"

long_description = """

"""

install_requires = [
]
version = '0.1'

NAME = 'datasource'
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
            "datasource": ["../data/*"],
      },
      include_package_data=True
      )
