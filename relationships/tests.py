from django.test import TestCase
from django.contrib.auth.models import User
from relationships.models import Relationship

class RelationshipsTestCase(TestCase):
    fixtures = ['relationships.json']
    
    def setUp(self):
        self.walrus = User.objects.get(username='The Walrus')
        self.john = User.objects.get(username='John')
        self.paul = User.objects.get(username='Paul')
        self.yoko = User.objects.get(username='Yoko')
    
    def test_related_names(self):
        rel = self.walrus.relationships.all()
        self.assertEquals(list(rel), [])
    
        rel = self.john.relationships.all()
        self.assertEquals(list(rel), [self.paul, self.yoko])
        
        rel = self.paul.relationships.all()
        self.assertEquals(list(rel), [self.john])
        
        rel = self.yoko.relationships.all()
        self.assertEquals(list(rel), [self.john])
        
        rel = self.walrus.related_to.all()
        self.assertEquals(list(rel), [])
        
        rel = self.john.related_to.all()
        self.assertEquals(list(rel), [self.yoko, self.paul])

        rel = self.paul.related_to.all()
        self.assertEquals(list(rel), [self.john])
        
        rel = self.yoko.related_to.all()
        self.assertEquals(list(rel), [self.john])
    
    def test_inherited_manager_methods(self):
        # does filter work?
        rel = self.john.relationships.filter(username='Paul')
        self.assertEquals(list(rel), [self.paul])
        
        # does filter work?
        rel = self.walrus.relationships.filter(username='Paul')
        self.assertEquals(list(rel), [])
        
        # does exclude work?
        rel = self.john.relationships.exclude(username='Paul')
        self.assertEquals(list(rel), [self.yoko])

        # does clear work?
        self.john.relationships.clear()
        rel = self.john.relationships.all()
        self.assertEquals(list(rel), [])

        # make sure yoko's relationship to john is still there
        rel = self.yoko.relationships.all()
        self.assertEquals(list(rel), [self.john])
    
    def test_add_method(self):
        _ = self.john.relationships.add(self.walrus)
        
        rel = self.john.relationships.all()
        self.assertEquals(list(rel), [self.walrus, self.paul, self.yoko])
        
        rel = self.john.related_to.all()
        self.assertEquals(list(rel), [self.yoko, self.paul])
        
        rel = self.walrus.relationships.all()
        self.assertEquals(list(rel), [])
        
        rel = self.walrus.related_to.all()
        self.assertEquals(list(rel), [self.john])
        
        # test that dupes aren't added
        _ = self.john.relationships.add(self.walrus)
        
        rel = self.john.relationships.all()
        self.assertEquals(list(rel), [self.walrus, self.paul, self.yoko])
    
    def test_remove_method(self):
        self.john.relationships.remove(self.yoko)
    
        rel = self.john.relationships.all()
        self.assertEquals(list(rel), [self.paul])
        
        rel = self.john.related_to.all()
        self.assertEquals(list(rel), [self.yoko, self.paul])
        
        rel = self.yoko.relationships.all()
        self.assertEquals(list(rel), [self.john])
        
        rel = self.yoko.related_to.all()
        self.assertEquals(list(rel), [])
        
        # no error
        self.john.relationships.remove(self.yoko)
    
    def test_custom_methods(self):
        rel = self.john.relationships.following()
        self.assertEquals(list(rel), [self.paul, self.yoko])
    
        rel = self.john.relationships.followers()
        self.assertEquals(list(rel), [self.yoko])
        
        rel = self.john.relationships.blocking()
        self.assertEquals(list(rel), [])
    
        rel = self.john.relationships.blockers()
        self.assertEquals(list(rel), [self.paul])
        
        rel = self.john.relationships.friends()
        self.assertEquals(list(rel), [self.yoko])
        
        ###
        rel = self.paul.relationships.following()
        self.assertEquals(list(rel), [])
    
        rel = self.paul.relationships.followers()
        self.assertEquals(list(rel), [self.john])
        
        rel = self.paul.relationships.blocking()
        self.assertEquals(list(rel), [self.john])
    
        rel = self.paul.relationships.blockers()
        self.assertEquals(list(rel), [])
        
        rel = self.paul.relationships.friends()
        self.assertEquals(list(rel), [])

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
