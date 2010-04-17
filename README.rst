====================
django-relationships
====================

Descriptive relationships between auth.users::

    In [4]: john.relationships.friends()
    Out[4]: [<User: Yoko>]

    In [5]: john.relationships.following()
    Out[5]: [<User: Paul>, <User: Yoko>]

    In [6]: john.relationships.followers()
    Out[6]: [<User: Yoko>]

    In [7]: john.relationships.blockers()
    Out[7]: [<User: Paul>]

    In [8]: paul.relationships.blocking()
    Out[8]: [<User: John>]


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


Installation
------------

`python setup.py install`

OR

put the ``relationships`` folder on your python-path
