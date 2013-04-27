from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.test import TestCase

from relationships.forms import RelationshipStatusAdminForm
from relationships.listeners import (attach_relationship_listener,
    detach_relationship_listener)
from relationships.models import Relationship, RelationshipStatus
from relationships.utils import (relationship_exists, extract_user_field,
    positive_filter, negative_filter)
from relationships.compat import User


class BaseRelationshipsTestCase(TestCase):
    """
    The fixture data defines:

    - 4 users, The Walrus, John, Paul and Yoko
    - 2 relationship status, Following & Blocking
    - 4 relationships
        - John is following Yoko
        - John is following Paul
        - Yoko is following John
        - Paul is blocking John
    """
    fixtures = ['relationships.json']

    def setUp(self):
        self.walrus = User.objects.get(username='The_Walrus')  # pk 1
        self.john = User.objects.get(username='John')  # pk 2
        self.paul = User.objects.get(username='Paul')  # pk 3
        self.yoko = User.objects.get(username='Yoko')  # pk 4

        self.following = RelationshipStatus.objects.get(from_slug='following')
        self.blocking = RelationshipStatus.objects.get(from_slug='blocking')

        self.site_id = settings.SITE_ID
        settings.SITE_ID = 1

        self.site = Site.objects.get_current()

    def tearDown(self):
        settings.SITE_ID = self.site_id

    def _sort_by_pk(self, list_or_qs):
        annotated = [(item.pk, item) for item in list_or_qs]
        annotated.sort()
        return map(lambda item_tuple: item_tuple[1], annotated)

    def assertQuerysetEqual(self, a, b):
        return self.assertEqual(self._sort_by_pk(a), self._sort_by_pk(b))


class RelationshipsTestCase(BaseRelationshipsTestCase):
    def setUp(self):
        BaseRelationshipsTestCase.setUp(self)
        self.second_site = Site.objects.create(name='ex2.com', domain='ex2.com')

    def test_manager(self):
        rel = self.walrus.relationships.all()
        self.assertQuerysetEqual(rel, [])

        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.paul, self.yoko])

        rel = self.paul.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])

        rel = self.yoko.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])

    def test_related_name(self):
        rel = self.walrus.related_to.all()
        self.assertQuerysetEqual(rel, [])

        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.paul, self.yoko])

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
        self.john.relationships.add(self.walrus)

        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.walrus, self.paul, self.yoko])

        # check that it wasn't added symmetrically
        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.paul, self.yoko])

        # check that it doesn't show up in walrus' relationships
        rel = self.walrus.relationships.all()
        self.assertQuerysetEqual(rel, [])

        # but it *does* show up in walrus' reverse relationships
        rel = self.walrus.related_to.all()
        self.assertQuerysetEqual(rel, [self.john])

        # test that dupes aren't added
        self.john.relationships.add(self.walrus)

        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.walrus, self.paul, self.yoko])

    def test_add_symmetrical(self):
        _, _ = self.john.relationships.add(self.walrus, symmetrical=True)

        # should show up in john's relationships
        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.walrus, self.paul, self.yoko])

        # should also show up that walrus has a relationship to john
        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.walrus, self.paul, self.yoko])

        # and same for walrus...
        rel = self.walrus.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])

        rel = self.walrus.related_to.all()
        self.assertQuerysetEqual(rel, [self.john])

    def test_remove_method(self):
        self.john.relationships.remove(self.yoko)

        # no longer shows up in the relationships
        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.paul])

        # the reverse relationship is still intact
        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.paul, self.yoko])

        rel = self.yoko.relationships.all()
        self.assertQuerysetEqual(rel, [self.john])

        rel = self.yoko.related_to.all()
        self.assertQuerysetEqual(rel, [])

        # no error
        self.john.relationships.remove(self.yoko)

    def test_remove_symmetrical(self):
        self.john.relationships.remove(self.yoko, symmetrical=True)

        rel = self.john.relationships.all()
        self.assertQuerysetEqual(rel, [self.paul])

        rel = self.john.related_to.all()
        self.assertQuerysetEqual(rel, [self.paul])

        rel = self.yoko.relationships.all()
        self.assertQuerysetEqual(rel, [])

        rel = self.yoko.related_to.all()
        self.assertQuerysetEqual(rel, [])

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

    def test_exists(self):
        self.assertTrue(self.john.relationships.exists(self.yoko))
        self.assertTrue(self.john.relationships.exists(self.paul))
        self.assertFalse(self.john.relationships.exists(self.walrus))

        self.assertTrue(self.paul.relationships.exists(self.john))
        self.assertFalse(self.paul.relationships.exists(self.yoko))
        self.assertFalse(self.paul.relationships.exists(self.walrus))

    def test_exists_with_status(self):
        self.assertTrue(self.john.relationships.exists(self.yoko, self.following))
        self.assertTrue(self.john.relationships.exists(self.paul, self.following))
        self.assertFalse(self.john.relationships.exists(self.walrus, self.following))

        self.assertFalse(self.john.relationships.exists(self.yoko, self.blocking))
        self.assertFalse(self.john.relationships.exists(self.paul, self.blocking))
        self.assertFalse(self.john.relationships.exists(self.walrus, self.blocking))

        self.assertFalse(self.paul.relationships.exists(self.john, self.following))
        self.assertFalse(self.paul.relationships.exists(self.yoko, self.following))
        self.assertFalse(self.paul.relationships.exists(self.walrus, self.following))

        self.assertTrue(self.paul.relationships.exists(self.john, self.blocking))
        self.assertFalse(self.paul.relationships.exists(self.yoko, self.blocking))
        self.assertFalse(self.paul.relationships.exists(self.walrus, self.blocking))

    def test_oneway_methods(self):
        self.assertQuerysetEqual(self.john.relationships.only_from(self.following), [self.paul])
        self.assertQuerysetEqual(self.john.relationships.only_to(self.following), [])

        self.assertQuerysetEqual(self.john.relationships.only_from(self.blocking), [])
        self.assertQuerysetEqual(self.john.relationships.only_to(self.blocking), [self.paul])

    def test_site_behavior(self):
        # relationships are site-dependent

        # walrus is now following John on the current site
        self.walrus.relationships.add(self.john)

        # walrus is now following Paul on another site
        status = RelationshipStatus.objects.following()
        r, _ = Relationship.objects.get_or_create(
            from_user=self.walrus,
            to_user=self.paul,
            site=self.second_site,
            status=status,
        )

        # the 'following' method is siteified
        self.assertQuerysetEqual(self.walrus.relationships.following(), [self.john])

        # ... the .all() method is not
        self.assertQuerysetEqual(self.walrus.relationships.all(), [self.john, self.paul])

        # remove only works on the current site, so paul will *NOT* be removed
        self.walrus.relationships.remove(self.paul)
        self.assertQuerysetEqual(self.walrus.relationships.all(), [self.john, self.paul])


class RelationshipsListenersTestCase(BaseRelationshipsTestCase):
    def setUp(self):
        BaseRelationshipsTestCase.setUp(self)
        attach_relationship_listener()

    def tearDown(self):
        detach_relationship_listener()
        BaseRelationshipsTestCase.tearDown(self)

    def test_following_and_blocking(self):
        # check initial state, john is following paul & yoko
        self.assertQuerysetEqual(self.john.relationships.following(), [self.paul, self.yoko])

        # when john blocks paul, his 'following' relationship will be deleted
        self.john.relationships.add(self.paul, self.blocking)
        self.assertQuerysetEqual(self.john.relationships.blocking(), [self.paul])
        self.assertQuerysetEqual(self.john.relationships.following(), [self.yoko])

        # check initial state for paul
        self.assertQuerysetEqual(self.paul.relationships.blocking(), [self.john])

        # when paul follows john his 'blocking' relationship will be deleted
        self.paul.relationships.add(self.john, self.following)
        self.assertQuerysetEqual(self.paul.relationships.following(), [self.john])
        self.assertQuerysetEqual(self.paul.relationships.blocking(), [])

    def test_listener_disconnecting(self):
        # this test simply ensures the default behavior
        detach_relationship_listener()

        # have john start blocking paul
        self.john.relationships.add(self.paul, self.blocking)

        # the blocking relationship is created and the original following
        # relationship is left intact
        self.assertQuerysetEqual(self.john.relationships.blocking(), [self.paul])
        self.assertQuerysetEqual(self.john.relationships.following(), [self.paul, self.yoko])

        # have paul start following john
        self.paul.relationships.add(self.john, self.following)

        # the following relationship is created and the original blocking
        # relationship is left intact
        self.assertQuerysetEqual(self.paul.relationships.following(), [self.john])
        self.assertQuerysetEqual(self.paul.relationships.blocking(), [self.john])


class RelationshipsViewsTestCase(BaseRelationshipsTestCase):
    def test_list_views(self):
        url = reverse('relationship_list', args=['John'])
        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], self.john.relationships.following())

        url = reverse('relationship_list', args=['John', 'followers'])
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], self.john.relationships.followers())

        url = reverse('relationship_list', args=['John', 'following'])
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], self.john.relationships.following())

        url = reverse('relationship_list', args=['John', 'friends'])
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertQuerysetEqual(resp.context['relationship_list'], self.john.relationships.friends())

        url = reverse('relationship_list', args=['John', 'blocking'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        self.client.login(username='John', password='John')
        url = reverse('relationship_list', args=['John', 'blocking'])
        resp = self.client.get(url)
        self.assertQuerysetEqual(resp.context['relationship_list'], self.john.relationships.blocking())

        # this is private, only Paul can see who he's blocking
        url = reverse('relationship_list', args=['Paul', 'blocking'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

        # non existant relationship status slug
        url = reverse('relationship_list', args=['John', 'walrus-friends'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_add_remove_login_required(self):
        # login required
        url = reverse('relationship_add', args=['The_Walrus', 'following'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        url = reverse('relationship_remove', args=['The_Walrus', 'following'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_add_remove_requires_post(self):
        self.client.login(username='John', password='John')

        url = reverse('relationship_add', args=['The_Walrus', 'following'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # a relationship has not been created yet
        self.assertFalse(self.john.relationships.exists(self.walrus, self.following))

        url = reverse('relationship_remove', args=['Yoko', 'following'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # the relationship has not been removed
        self.assertTrue(self.john.relationships.exists(self.yoko, self.following))

    def test_adding(self):
        self.client.login(username='John', password='John')

        url = reverse('relationship_add', args=['The_Walrus', 'following'])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

        # the relationship has been created
        self.assertTrue(self.john.relationships.exists(self.walrus, self.following))

        # the relationship is not symmetrical, though
        self.assertFalse(self.walrus.relationships.exists(self.john, self.following))

        # a nonexistant user causes a 404
        url = reverse('relationship_add', args=['Nobody', 'following'])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)

    def test_adding_symm(self):
        self.client.login(username='John', password='John')

        url = reverse('relationship_add', args=['The_Walrus', 'friends'])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

        # the relationship has been created
        self.assertTrue(self.john.relationships.exists(self.walrus, self.following))

        # the relationship is symmetrical
        self.assertTrue(self.walrus.relationships.exists(self.john, self.following))

    def test_removing(self):
        self.client.login(username='John', password='John')

        url = reverse('relationship_remove', args=['Yoko', 'following'])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(self.john.relationships.exists(self.yoko, self.following))

        # the symmetrical relationship was not removed
        self.assertTrue(self.yoko.relationships.exists(self.john, self.following))

        # non existant user causes a 404
        url = reverse('relationship_remove', args=['Nobody', 'following'])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)

    def test_removing_symm(self):
        self.client.login(username='John', password='John')

        url = reverse('relationship_remove', args=['Yoko', 'friends'])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

        self.assertFalse(self.john.relationships.exists(self.yoko, self.following))

        # the symmetrical relationship was not removed
        self.assertFalse(self.yoko.relationships.exists(self.john, self.following))


class RelationshipsTagsTestCase(BaseRelationshipsTestCase):
    def test_add_url_filter(self):
        t = Template('{% load relationship_tags %}{{ user|add_relationship_url:"following" }}')
        c = Context({'user': self.paul})

        rendered = t.render(c)
        url = reverse('relationship_add', args=['Paul', 'following'])
        self.assertEqual(rendered, url)

        # check that a symmetrical slug can be used
        t = Template('{% load relationship_tags %}{{ user|add_relationship_url:"friends" }}')
        c = Context({'user': self.paul})

        rendered = t.render(c)
        url = reverse('relationship_add', args=['Paul', 'friends'])
        self.assertEqual(rendered, url)

        t = Template('{% load relationship_tags %}{{ user|add_relationship_url:blocking }}')
        c = Context({'user': self.paul, 'blocking': self.blocking})
        rendered = t.render(c)
        url = reverse('relationship_add', args=['Paul', 'blocking'])
        self.assertEqual(rendered, url)

    def test_remove_url_filter(self):
        t = Template('{% load relationship_tags %}{{ user|remove_relationship_url:"following" }}')
        c = Context({'user': self.paul})
        rendered = t.render(c)
        url = reverse('relationship_remove', args=['Paul', 'following'])
        self.assertEqual(rendered, url)

        # check that a symmetrical slug can be used
        t = Template('{% load relationship_tags %}{{ user|remove_relationship_url:"friends" }}')
        c = Context({'user': self.paul})

        rendered = t.render(c)
        url = reverse('relationship_remove', args=['Paul', 'friends'])
        self.assertEqual(rendered, url)

        t = Template('{% load relationship_tags %}{{ user|remove_relationship_url:blocking }}')
        c = Context({'user': self.paul, 'blocking': self.blocking})
        rendered = t.render(c)
        url = reverse('relationship_remove', args=['Paul', 'blocking'])
        self.assertEqual(rendered, url)

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

        group_qs = Group.objects.all().order_by('name')

        # john is friends w/ yoko so show yoko's groups
        t = Template('{% load relationship_tags %}{% for group in qs|friend_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.john, 'qs': group_qs})
        rendered = t.render(c)
        self.assertEqual(rendered, 'characters|john_yoko|')

        # paul is friends w/ nobody, so no groups
        c = Context({'user': self.paul, 'qs': group_qs})
        rendered = t.render(c)
        self.assertEqual(rendered, '')

        # john is following paul & yoko
        t = Template('{% load relationship_tags %}{% for group in qs|following_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.john, 'qs': group_qs})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|characters|john_yoko|')

        # yoko is followed by john
        t = Template('{% load relationship_tags %}{% for group in qs|followers_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.yoko, 'qs': group_qs})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|john_yoko|')

        # paul is blocking john, so every group but ones with him
        t = Template('{% load relationship_tags %}{% for group in qs|unblocked_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.paul, 'qs': group_qs})
        rendered = t.render(c)
        self.assertEqual(rendered, 'characters|')

        # oh no, john is blocking yoko
        self.john.relationships.add(self.yoko, RelationshipStatus.objects.blocking())
        c = Context({'user': self.john, 'qs': group_qs})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|')

        # make sure it works with a model string
        t = Template('{% load relationship_tags %}{% for group in "auth.group"|unblocked_content:user %}{{ group.name }}|{% endfor %}')
        c = Context({'user': self.john})
        rendered = t.render(c)
        self.assertEqual(rendered, 'beatles|')


class RelationshipStatusAdminFormTestCase(BaseRelationshipsTestCase):
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


class RelationshipUtilsTestCase(BaseRelationshipsTestCase):
    def test_extract_user_field(self):
        # just test a known pass and known fail
        from django.contrib.comments.models import Comment
        from django.contrib.sites.models import Site

        self.assertEqual(extract_user_field(Comment), 'user')
        self.assertEqual(extract_user_field(Site), None)

    def test_positive_filter(self):
        following = RelationshipStatus.objects.following()

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

        group_qs = Group.objects.all().order_by('name')

        # groups people paul follows are in (nobody)
        paul_following_groups = positive_filter(
            group_qs,
            self.paul.relationships.following(),
            'user')
        self.assertQuerysetEqual(paul_following_groups, [])

        # when paul follows john he will see john's groups
        self.paul.relationships.add(self.john, following)
        paul_following_groups = positive_filter(
            group_qs,
            self.paul.relationships.following(),
            'user')
        self.assertQuerysetEqual(paul_following_groups, [beatles, john_yoko])

        # now john's + walrus's
        self.paul.relationships.add(self.walrus, following)
        paul_following_groups = positive_filter(
            group_qs,
            self.paul.relationships.following(),
            'user')
        self.assertQuerysetEqual(paul_following_groups, [beatles, characters, john_yoko])

        # everybody's - distinct groups, no dupes
        self.paul.relationships.add(self.yoko, following)
        paul_following_groups = positive_filter(
            group_qs,
            self.paul.relationships.following(),
            'user')
        self.assertQuerysetEqual(paul_following_groups, [beatles, characters, john_yoko])

        # just groups walrus & yoko are in
        self.paul.relationships.remove(self.john, following)
        paul_following_groups = positive_filter(
            group_qs,
            self.paul.relationships.following(),
            'user')
        self.assertQuerysetEqual(paul_following_groups, [characters, john_yoko])

        # just walrus' groups
        self.paul.relationships.remove(self.yoko)
        paul_following_groups = positive_filter(
            group_qs,
            self.paul.relationships.following(),
            'user')
        self.assertQuerysetEqual(paul_following_groups, [characters])

        self.paul.relationships.remove(self.walrus)

    def test_negative_filter(self):
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

        group_qs = Group.objects.all().order_by('name')

        # groups people paul blocks are *not* in (yoko & walrus)
        # since john is in the john_yoko group, just characters will show up
        paul_blocking_groups = negative_filter(
            group_qs,
            self.paul.relationships.blocking(),
            'user')
        self.assertQuerysetEqual(paul_blocking_groups, [characters])

        # block yoko and no groups
        self.paul.relationships.add(self.yoko, blocking)
        paul_blocking_groups = negative_filter(
            group_qs,
            self.paul.relationships.blocking(),
            'user')
        self.assertQuerysetEqual(paul_blocking_groups, [])

        # block walrus - everyone is blocked, no groups
        self.paul.relationships.add(self.walrus, blocking)
        paul_blocking_groups = negative_filter(
            group_qs,
            self.paul.relationships.blocking(),
            'user')
        self.assertQuerysetEqual(paul_blocking_groups, [])

        # unblock john and we'll get beatles
        self.paul.relationships.remove(self.john, blocking)
        paul_blocking_groups = negative_filter(
            group_qs,
            self.paul.relationships.blocking(),
            'user')
        self.assertQuerysetEqual(paul_blocking_groups, [beatles])

        # unblock yoko
        self.paul.relationships.remove(self.yoko, blocking)
        paul_blocking_groups = negative_filter(
            group_qs,
            self.paul.relationships.blocking(),
            'user')
        self.assertQuerysetEqual(paul_blocking_groups, [beatles, john_yoko])

        # unblock walrus and we have them all
        self.paul.relationships.remove(self.walrus, blocking)
        paul_blocking_groups = negative_filter(
            group_qs,
            self.paul.relationships.blocking(),
            'user')
        self.assertQuerysetEqual(paul_blocking_groups, [beatles, characters, john_yoko])

    def test_relationship_exists(self):
        self.assertTrue(relationship_exists(self.john, self.yoko, 'following'))
        self.assertTrue(relationship_exists(self.john, self.yoko, 'followers'))
        self.assertTrue(relationship_exists(self.john, self.yoko, 'friends'))

        self.assertTrue(relationship_exists(self.yoko, self.john, 'following'))
        self.assertTrue(relationship_exists(self.yoko, self.john, 'followers'))
        self.assertTrue(relationship_exists(self.yoko, self.john, 'friends'))

        self.assertTrue(relationship_exists(self.john, self.paul, 'following'))
        self.assertFalse(relationship_exists(self.john, self.paul, 'followers'))
        self.assertFalse(relationship_exists(self.john, self.paul, 'friends'))

        self.assertFalse(relationship_exists(self.paul, self.john, 'following'))
        self.assertTrue(relationship_exists(self.paul, self.john, 'followers'))
        self.assertFalse(relationship_exists(self.paul, self.john, 'friends'))

        self.assertTrue(relationship_exists(self.paul, self.john, 'blocking'))
        self.assertFalse(relationship_exists(self.paul, self.john, 'blockers'))
