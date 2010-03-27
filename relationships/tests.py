from django.test import TestCase
from django.contrib.auth.models import User
from relationships.models import Relationship

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
        
        resp = self.client.get('/relationships/John/walrus-friends/')
        self.assertEquals(resp.status_code, 404)
    
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
