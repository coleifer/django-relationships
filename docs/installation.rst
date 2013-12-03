Installation
============

You can pip install django-relationships::

    pip install django-relationships

Alternatively, you can use the version hosted on GitHub, which may contain new
or undocumented features::

    git clone git://github.com/coleifer/django-relationships.git
    cd relationships
    python setup.py install


Adding to your Django Project
--------------------------------

After installing, adding relationships to your projects is a snap.  First,
add it to your projects' ``INSTALLED_APPS``::
    
    # settings.py
    INSTALLED_APPS = [
        ...
        'relationships'
    ]

Next you'll need to run a ``syncdb``::

    django-admin.py syncdb

If you're using `south` for schema migrations, you can use the migrations
provided by the app.
