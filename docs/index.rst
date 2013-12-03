.. django-relationships documentation master file, created by
   sphinx-quickstart on Wed Jul 13 09:47:16 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-relationships's documentation!
================================================

Descriptive relationships between auth.users::

    >>> john.relationships.friends()
    [<User: Yoko>]

    >>> john.relationships.following()
    [<User: Paul>, <User: Yoko>]

    >>> john.relationships.followers()
    [<User: Yoko>]

    >>> john.relationships.blockers()
    [<User: Paul>]

    >>> paul.relationships.blocking()
    [<User: John>]


You can create as many types of relationships as you like, or just use the
default ones, 'following' and 'blocking'.


From, To and Symmetrical
------------------------

Relationship types define each of the following cases:

* from - 'following', who **I** am following
* to - 'followers', who is following **me**
* symmetrical - 'friends', **we** follow eachother

Relationship types can be *login_required*, or *private*, and if you want
to make a relationship type unviewable (i.e. you may not want to allow
users to see who is blocking them), simply give it a unmatchable slug,
like '!blockers'.


Contents:

.. toctree::
   :maxdepth: 3
   
   installation
   getting_started

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

