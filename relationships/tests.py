from django import forms
from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.template import Template, Context
from relationships.forms import RelationshipStatusAdminForm
from relationships.models import Relationship, RelationshipStatus
from relationships.utils import extract_user_field, positive_filter, negative_filter

class RelationshipsTestCase(TestCase):
    fixtures = ['relationships.json']
    
    def setUp(self):
        self.walrus = User.objects.get(username='The_Walrus')
        self.john = User.objects.get(username='John')
        self.paul = User.objects.get(username='Paul')
        self.yoko = User.objects.get(username='Yoko')
    
    def assertQuerysetEqual(self, a, b):
        return self.assertEqual(list(a), list(b))
    
    def test_related_names(self):
        rel = self.walrus.relationships.all()
        self.assertQuerysetEqual(rel, [])
    
        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.paul, self.yoko])
        
        rel = self.paul.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])
        
        rel = self.yoko.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])
        
        rel = self.walrus.related_to.all()
        self.assertQuerysetEqual(rel, [])
        
        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.yoko, self.paul])

        rel = self.paul.related_to.all()
        self.assertQuerysetEqual(rel, [self.john])
        
        rel = self.yoko.related_to.all()
        self.assertQuerysetEqual(rel, [self.john])
    
    def test_inherited_manager_methods(self):
        # does filter work?
        rel = self.john.relationships.filter(username='Paul')
        self.assertQuerysetEqual(rel, [self.paul])
        
        # does filter work?
        rel = self.walrus.relationships.filter(username='Paul')
        self.assertQuerysetEqual(rel, [])
        
        # does exclude work?
        rel = self.john.relationships.exclude(username='Paul')
        self.assertQuerysetEqual(rel, [self.yoko])

        # does clear work?
        self.john.relationships.clear()
        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [])

        # make sure yoko's relationship to john is still there
        rel = self.yoko.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])
    
    def test_add_method(self):
        _ = self.john.relationships.add(self.walrus)
        
        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.walrus, self.paul, self.yoko])
        
        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.yoko, self.paul])
        
        rel = self.walrus.relationships.all()
        self.assertQuerysetEqual(rel, [])
        
        rel = self.walrus.related_to.all()
        self.assertQuerysetEqual(rel, [self.john])
        
        # test that dupes aren't added
        _ = self.john.relationships.add(self.walrus)
        
        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.walrus, self.paul, self.yoko])
    
    def test_remove_method(self):
        self.john.relationships.remove(self.yoko)
    
        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.paul])
        
        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.yoko, self.paul])
        
        rel = self.yoko.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])
        
        rel = self.yoko.related_to.all()
        self.assertQuerysetEqual(rel, [])
        
        # no error
        self.john.relationships.remove(self.yoko)
    
    def test_custom_methods(self):
        rel = self.john.relationships.following()
        self.assertQuerysetEqual(rel, [self.paul, self.yoko])
    
        rel = self.john.relationships.followers()
        self.assertQuerysetEqual(rel, [self.yoko])
        
        rel = self.john.relationships.blocking()
        self.assertQuerysetEqual(rel, [])
    
        rel = self.john.relationships.blockers()
        self.assertQuerysetEqual(rel, [self.paul])
        
        rel = self.john.relationships.friends()
        self.assertQuerysetEqual(rel, [self.yoko])
        
        ###
        rel = self.paul.relationships.following()
        self.assertQuerysetEqual(rel, [])
    
        rel = self.paul.relationships.followers()
        self.assertQuerysetEqual(rel, [self.john])
        
        rel = self.paul.relationships.blocking()
        self.assertQuerysetEqual(rel, [self.john])
    
        rel = self.paul.relationships.blockers()
        self.assertQuerysetEqual(rel, [])
        
        rel = self.paul.relationships.friends()
        self.assertQuerysetEqual(rel, [])

        # test exists() method
        self.assertTrue(self.john.relationships.exists(self.yoko))
        self.assertTrue(self.john.relationships.exists(self.paul))
        self.assertTrue(self.yoko.relationships.exists(self.john))
        self.assertTrue(self.paul.relationships.exists(self.john))

        self.assertFalse(self.john.relationships.exists(self.walrus))
        self.assertFalse(self.walrus.relationships.exists(self.john))
        self.assertFalse(self.paul.relationships.exists(self.yoko))
        self.assertFalse(self.yoko.relationships.exists(self.paul))
        
        self.assertTrue(self.john.relationships.exists(self.yoko, 1))
        self.assertTrue(self.john.relationships.exists(self.paul, 1))
        self.assertTrue(self.yoko.relationships.exists(self.john, 1))
        self.assertTrue(self.paul.relationships.exists(self.john, 2))
        
        self.assertFalse(self.john.relationships.exists(self.yoko, 2))
        self.assertFalse(self.john.relationships.exists(self.paul, 2))
        self.assertFalse(self.john.relationships.exists(self.walrus, 1))

        self.assertFalse(self.paul.relationships.exists(self.yoko, 2))
        self.assertFalse(self.paul.relationships.exists(self.john, 1))
        self.assertFalse(self.paul.relationships.exists(self.walrus, 1))
        
        self.assertTrue(self.john.relationships.symmetrical_exists(self.yoko, 1))
        self.assertFalse(self.john.relationships.symmetrical_exists(self.paul, 1))
        self.assertFalse(self.john.relationships.symmetrical_exists(self.walrus, 1))
        
        self.assertTrue(self.yoko.relationships.symmetrical_exists(self.john, 1))
        self.assertFalse(self.yoko.relationships.symmetrical_exists(self.paul, 1))
        self.assertFalse(self.yoko.relationships.symmetrical_exists(self.walrus, 1))


class RelationshipsViewsTestCase(TestCase):
    fixtures = ['relationships.json']
    
    def setUp(self):
        self.walrus = User.objects.get(username='The_Walrus')
        self.john = User.objects.get(username='John')
        self.paul = User.objects.get(username='Paul')
        self.yoko = User.objects.get(username='Yoko')
    
    def assertQuerysetEqual(self, a, b):
        return self.assertEqual(list(a), list(b))
    
    def test_list_views(self):
        resp = self.client.get('/relationships/John/')
        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], list(self.john.relationships.all()))
        
        resp = self.client.get('/relationships/John/followers/')
        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], list(self.john.relationships.followers()))
        
        resp = self.client.get('/relationships/John/following/')
        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], list(self.john.relationships.following()))
        
        resp = self.client.get('/relationships/John/friends/')
        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], list(self.john.relationships.friends()))
        
        resp = self.client.get('/relationships/John/blocking/')
        self.assertEqual(resp.status_code, 302)
        
        self.client.login(username='John', password='John')
        resp = self.client.get('/relationships/John/blocking/')
        self.assertQuerysetEqual(resp.context['relationship_list'], list(self.john.relationships.blocking()))
        
        # this is private, only Paul can see who he's blocking
        resp = self.client.get('/relationships/Paul/blocking/')
        self.assertEqual(resp.status_code, 404)
        
        resp = self.client.get('/relationships/John/walrus-friends/')
        self.assertEqual(resp.status_code, 404)
        
    def test_add_remove_views(self):
        # login required
        resp = self.client.get('/relationships/add/The_Walrus/following/')
        self.assertEqual(resp.status_code, 302)
        
        resp = self.client.get('/relationships/remove/The_Walrus/following/')
        self.assertEqual(resp.status_code, 302)
        
        self.client.login(username='John', password='John')
        resp = self.client.get('/relationships/add/The_Walrus/following/')
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.get('/relationships/remove/The_Walrus/following/')
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.post('/relationships/add/The_Walrus/following/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.john.relationships.exists(self.walrus, 1))
        
        resp = self.client.post('/relationships/remove/The_Walrus/following/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.john.relationships.exists(self.walrus, 1))
        
        resp = self.client.post('/relationships/add/Nobody/following/')
        self.assertEqual(resp.status_code, 404)


class RelationshipsTagsTestCase(TestCase):
    fixtures = ['relationships.json']
    
    def setUp(self):
        self.walrus = User.objects.get(username='The_Walrus')
        self.john = User.objects.get(username='John')
        self.paul = User.objects.get(username='Paul')
        self.yoko = User.objects.get(username='Yoko')
        self.following = RelationshipStatus.objects.get(from_slug='following')
        self.blocking = RelationshipStatus.objects.get(from_slug='blocking')
    
    def test_add_url_filter(self):
        t = Template('{% load relationship_tags %}{{ user|add_relationship_url:"following" }}')
        c = Context({'user': self.paul})
        rendered = t.render(c)
        self.assertEqual(rendered, '/relationships/add/Paul/following/')
        
        t = Template('{% load relationship_tags %}{{ user|add_relationship_url:blocking }}')
        c = Context({'user': self.paul, 'blocking': self.blocking})
        rendered = t.render(c)
        self.assertEqual(rendered, '/relationships/add/Paul/blocking/')
    
    def test_remove_url_filter(self):
        t = Template('{% load relationship_tags %}{{ user|remove_relationship_url:"following" }}')
        c = Context({'user': self.paul})
        rendered = t.render(c)
        self.assertEqual(rendered, '/relationships/remove/Paul/following/')
        
        t = Template('{% load relationship_tags %}{{ user|remove_relationship_url:blocking }}')
        c = Context({'user': self.paul, 'blocking': self.blocking})
        rendered = t.render(c)
        self.assertEqual(rendered, '/relationships/remove/Paul/blocking/')
    
    def test_if_relationship_tag(self):
        t = Template('{% load relationship_tags %}{% if_relationship john paul "following" %}y{% else %}n{% endif_relationship %}')
        c = Context({'john': self.john, 'paul': self.paul})
        rendered = t.render(c)
        self.assertEqual(rendered, 'y')
        
        t = Template('{% load relationship_tags %}{% if_relationship paul john "following" %}y{% else %}n{% endif_relationship %}')
        c = Context({'john': self.john, 'paul': self.paul})
        rendered = t.render(c)
        self.assertEqual(rendered, 'n')
        
        t = Template('{% load relationship_tags %}{% if_relationship paul john "followers" %}y{% else %}n{% endif_relationship %}')
        c = Context({'john': self.john, 'paul': self.paul})
        rendered = t.render(c)
        self.assertEqual(rendered, 'y')
        
        t = Template('{% load relationship_tags %}{% if_relationship paul john "friends" %}y{% else %}n{% endif_relationship %}')
        c = Context({'john': self.john, 'paul': self.paul})
        rendered = t.render(c)
        self.assertEqual(rendered, 'n')
        
        t = Template('{% load relationship_tags %}{% if_relationship john yoko "friends" %}y{% else %}n{% endif_relationship %}')
        c = Context({'john': self.john, 'yoko': self.yoko})
        rendered = t.render(c)
        self.assertEqual(rendered, 'y')

    def test_status_filters(self):
        # create some groups to filter
        from django.contrib.auth.models import Group
        beatles = Group.objects.create(name='beatles')
        john_yoko = Group.objects.create(name='john_yoko')
        characters = Group.objects.create(name='characters')

        self.walrus.groups.add(characters)

        self.john.groups.add(beatles)
        self.john.groups.add(john_yoko)

        self.paul.groups.add(beatles)

        self.yoko.groups.add(john_yoko)
        self.yoko.groups.add(characters)

        # john is friends w/ yoko so show yoko's groups
        t = Template('{% load relationship_tags %}{% for group in qs|friend_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.john, 'qs': Group.objects.all()})
        rendered = t.render(c)
        self.assertEqual(rendered, 'john_yoko|characters|')

        # paul is friends w/ nobody, so no groups
        c = Context({'user': self.paul, 'qs': Group.objects.all()})
        rendered = t.render(c)
        self.assertEqual(rendered, '')

        # john is following paul & yoko
        t = Template('{% load relationship_tags %}{% for group in qs|following_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.john, 'qs': Group.objects.all()})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|john_yoko|characters|')

        # yoko is followed by john
        t = Template('{% load relationship_tags %}{% for group in qs|followers_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.yoko, 'qs': Group.objects.all()})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|john_yoko|')

        # paul is blocking john, so every group but ones with him
        t = Template('{% load relationship_tags %}{% for group in qs|unblocked_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.paul, 'qs': Group.objects.all()})
        rendered = t.render(c)
        self.assertEqual(rendered, 'characters|')

        # oh no, john is blocking yoko
        self.john.relationships.add(self.yoko, RelationshipStatus.objects.blocking())
        c = Context({'user': self.john, 'qs': Group.objects.all()})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|')

        # make sure it works with a model string
        t = Template('{% load relationship_tags %}{% for group in "auth.group"|unblocked_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.john})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|')
        
        

class RelationshipStatusAdminFormTestCase(TestCase):
    fixtures = ['relationships.json']

    def setUp(self):
        self.walrus = User.objects.get(username='The_Walrus')
        self.john = User.objects.get(username='John')
        self.paul = User.objects.get(username='Paul')
        self.yoko = User.objects.get(username='Yoko')
        self.following = RelationshipStatus.objects.get(from_slug='following')
        self.blocking = RelationshipStatus.objects.get(from_slug='blocking')

    def test_no_dupes(self):
        payload = {
            'name': 'Testing',
            'verb': 'testing',
            'from_slug': 'testing',
            'to_slug': 'testers',
            'symmetrical_slug': 'tests'
        }
        form = RelationshipStatusAdminForm(payload)
        self.assertTrue(form.is_valid())
        test_status = form.save()

        # saving again should work
        form = RelationshipStatusAdminForm(payload, instance=test_status)
        self.assertTrue(form.is_valid())

        payload['from_slug'] = 'testers'
        payload['to_slug'] = 'testing'
        
        # saving will work since it will not test against the current instance
        form = RelationshipStatusAdminForm(payload, instance=test_status)
        self.assertTrue(form.is_valid())

        # setting the from_slug to the to_slug will raise an error
        payload['from_slug'] = 'testers'
        payload['to_slug'] = 'testers'
        form = RelationshipStatusAdminForm(payload, instance=test_status)
        self.assertFalse(form.is_valid())

        # setting the from_slug to the symmetrical_slug will raise an error
        payload['from_slug'] = 'tests'
        form = RelationshipStatusAdminForm(payload, instance=test_status)
        self.assertFalse(form.is_valid())

        # setting to a pre-existing from_slug will fail
        payload['from_slug'] = 'following'
        form = RelationshipStatusAdminForm(payload)
        self.assertFalse(form.is_valid())
        self.assertTrue('from_slug' in form.errors)

        # setting the from_slug to a pre-existing to_slug will also fail
        payload['from_slug'] = 'followers'
        form = RelationshipStatusAdminForm(payload)
        self.assertFalse(form.is_valid())
        self.assertTrue('from_slug' in form.errors)

        # setting the from_slug to a pre-existing symetrical_slug will also fail
        payload['from_slug'] = 'friends'
        form = RelationshipStatusAdminForm(payload)
        self.assertFalse(form.is_valid())
        self.assertTrue('from_slug' in form.errors)


class RelationshipUtilsTestCase(TestCase):
    fixtures = ['relationships.json']
    
    def setUp(self):
        self.walrus = User.objects.get(username='The_Walrus')
        self.john = User.objects.get(username='John')
        self.paul = User.objects.get(username='Paul')
        self.yoko = User.objects.get(username='Yoko')

    def assertQuerysetEqual(self, a, b):
        return self.assertEqual(list(a), list(b))
        
    def test_extract_user_field(self):
        # just test a known pass and known fail
        from django.contrib.comments.models import Comment
        from django.contrib.sites.models import Site
        
        self.assertEqual(extract_user_field(Comment), 'user')
        self.assertEqual(extract_user_field(Site), None)

    def test_positive_filter(self):
        following = RelationshipStatus.objects.following()
        blocking = RelationshipStatus.objects.blocking()

        # create some groups to filter
        from django.contrib.auth.models import Group
        beatles = Group.objects.create(name='beatles')
        john_yoko = Group.objects.create(name='john_yoko')
        characters = Group.objects.create(name='characters')

        self.walrus.groups.add(characters)

        self.john.groups.add(beatles)
        self.john.groups.add(john_yoko)

        self.paul.groups.add(beatles)

        self.yoko.groups.add(john_yoko)
        self.yoko.groups.add(characters)

        # groups people paul follows are in (nobody)
        paul_following_groups = positive_filter(Group.objects.all(),
            self.paul.relationships.following(), 'user')
        self.assertQuerysetEqual(paul_following_groups, [])

        # when paul follows john he will see john's groups
        self.paul.relationships.add(self.john, following)
        paul_following_groups = positive_filter(Group.objects.all(),
            self.paul.relationships.following(), 'user')
        self.assertQuerysetEqual(paul_following_groups, [beatles, john_yoko])

        # now john's + walrus's
        self.paul.relationships.add(self.walrus, following)
        paul_following_groups = positive_filter(Group.objects.all(),
            self.paul.relationships.following(), 'user')
        self.assertQuerysetEqual(paul_following_groups, [beatles, john_yoko, characters])

        # everybody's - distinct groups, no dupes
        self.paul.relationships.add(self.yoko, following)
        paul_following_groups = positive_filter(Group.objects.all(),
            self.paul.relationships.following(), 'user')
        self.assertQuerysetEqual(paul_following_groups, [beatles, john_yoko, characters])

        # just groups walrus & yoko are in
        self.paul.relationships.remove(self.john, following)
        paul_following_groups = positive_filter(Group.objects.all(),
            self.paul.relationships.following(), 'user')
        self.assertQuerysetEqual(paul_following_groups, [john_yoko, characters])

        # just walrus' groups
        self.paul.relationships.remove(self.yoko)
        paul_following_groups = positive_filter(Group.objects.all(),
            self.paul.relationships.following(), 'user')
        self.assertQuerysetEqual(paul_following_groups, [characters])
        
        self.paul.relationships.remove(self.walrus)

    def test_negative_filter(self):
        following = RelationshipStatus.objects.following()
        blocking = RelationshipStatus.objects.blocking()

        # create some groups to filter
        from django.contrib.auth.models import Group
        beatles = Group.objects.create(name='beatles')
        john_yoko = Group.objects.create(name='john_yoko')
        characters = Group.objects.create(name='characters')

        self.walrus.groups.add(characters)

        self.john.groups.add(beatles)
        self.john.groups.add(john_yoko)

        self.paul.groups.add(beatles)

        self.yoko.groups.add(john_yoko)
        self.yoko.groups.add(characters)

        # groups people paul blocks are *not* in (yoko & walrus)
        # since john is in the john_yoko group, just characters will show up
        paul_blocking_groups = negative_filter(Group.objects.all(), 
            self.paul.relationships.blocking(), 'user')
        self.assertQuerysetEqual(paul_blocking_groups, [characters])

        # block yoko and no groups
        self.paul.relationships.add(self.yoko, blocking)
        paul_blocking_groups = negative_filter(Group.objects.all(),
            self.paul.relationships.blocking(), 'user')
        self.assertQuerysetEqual(paul_blocking_groups, [])

        # block walrus - everyone is blocked, no groups
        self.paul.relationships.add(self.walrus, blocking)
        paul_blocking_groups = negative_filter(Group.objects.all(),
            self.paul.relationships.blocking(), 'user')
        self.assertQuerysetEqual(paul_blocking_groups, [])

        # unblock john and we'll get beatles
        self.paul.relationships.remove(self.john, blocking)
        paul_blocking_groups = negative_filter(Group.objects.all(),
            self.paul.relationships.blocking(), 'user')
        self.assertQuerysetEqual(paul_blocking_groups, [beatles])

        # unblock yoko
        self.paul.relationships.remove(self.yoko, blocking)
        paul_blocking_groups = negative_filter(Group.objects.all(),
            self.paul.relationships.blocking(), 'user')
        self.assertQuerysetEqual(paul_blocking_groups, [beatles, john_yoko])

        # unblock walrus and we have them all
        self.paul.relationships.remove(self.walrus, blocking)
        paul_blocking_groups = negative_filter(Group.objects.all(),
            self.paul.relationships.blocking(), 'user')
        self.assertQuerysetEqual(paul_blocking_groups, [beatles, john_yoko, characters])
