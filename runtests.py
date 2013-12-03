#!/usr/bin/env python
import sys
from os.path import dirname, abspath

import django
from django.conf import settings

if len(sys.argv) > 1 and 'postgres' in sys.argv:
    sys.argv.remove('postgres')
    db_engine = 'django.db.backends.postgresql_psycopg2'
    db_name = 'test_main'
else:
    db_engine = 'django.db.backends.sqlite3'
    db_name = ''

if not settings.configured:
    if django.VERSION < (1, 4):
        tl = (
            'django.template.loaders.filesystem.load_template_source',
            'django.template.loaders.app_directories.load_template_source',
        )
    else:
        tl = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )
    settings.configure(
        DATABASES=dict(default=dict(ENGINE=db_engine, NAME=db_name)),
        SITE_ID=1,
        TEMPLATE_LOADERS=tl,
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
        ),
        ROOT_URLCONF='relationships.relationships_tests.urls',
        INSTALLED_APPS=[
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'relationships',
            'relationships.relationships_tests',
        ],
    )

from django.test.utils import get_runner


def runtests(*test_args):
    if not test_args:
        test_args = ['relationships_tests']
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])
