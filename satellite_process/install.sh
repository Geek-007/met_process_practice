python setup.py sdist
python setup.py bdist_wheel --universal
python setup.py build && python setup.py install