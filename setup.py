import os
from setuptools import setup, find_packages

from relationships import VERSION

f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = f.read()
f.close()

setup(
    name='django-relationships',
    version=".".join(map(str, VERSION)),
    description='descriptive relationships between auth.User',
    long_description=readme,
    author='Charles Leifer',
    author_email='coleifer@gmail.com',
    url='http://github.com/coleifer/django-relationships/tree/master',
    packages=find_packages(exclude=['example']),
    package_data = {
        'relationships': [
            'fixtures/*.json',
            'templates/*.html',
            'templates/*/*.html',
            'locale/*/LC_MESSAGES/*',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)


