import django


# Django 1.5 add support for custom auth user model
if django.VERSION >= (1, 5) and django.VERSION < (1, 7): #1.7 User init is done in app config 
    from django.contrib.auth import get_user_model
    User = get_user_model()
else:
    try:
        from django.contrib.auth.models import User
    except ImportError:
        raise ImportError(u"User model is not to be found.")

# location of patterns, url, include changes in 1.4 onwards
try:
    from django.conf.urls import patterns, url, include
except:
    from django.conf.urls.defaults import patterns, url, include



####Hack!!!! direct copy from django 1.4.7 package#####
def create_many_related_manager(superclass, rel):
    """Creates a manager that subclasses 'superclass' (which is a Manager)
    and adds behavior for many-to-many related objects."""
    class ManyRelatedManager(superclass):
        def __init__(self, model=None, query_field_name=None, instance=None, symmetrical=None,
                     source_field_name=None, target_field_name=None, reverse=False,
                     through=None, prefetch_cache_name=None):
            super(ManyRelatedManager, self).__init__()
            self.model = model
            self.query_field_name = query_field_name
            self.core_filters = {'%s__pk' % query_field_name: instance._get_pk_val()}
            self.instance = instance
            self.symmetrical = symmetrical
            self.source_field_name = source_field_name
            self.target_field_name = target_field_name
            self.reverse = reverse
            self.through = through
            self.prefetch_cache_name = prefetch_cache_name
            self._fk_val = self._get_fk_val(instance, source_field_name)
            if self._fk_val is None:
                raise ValueError('"%r" needs to have a value for field "%s" before '
                                 'this many-to-many relationship can be used.' %
                                 (instance, source_field_name))
            # Even if this relation is not to pk, we require still pk value.
            # The wish is that the instance has been already saved to DB,
            # although having a pk value isn't a guarantee of that.
            if instance.pk is None:
                raise ValueError("%r instance needs to have a primary key value before "
                                 "a many-to-many relationship can be used." %
                                 instance.__class__.__name__)

        def _get_fk_val(self, obj, field_name):
            """
            Returns the correct value for this relationship's foreign key. This
            might be something else than pk value when to_field is used.
            """
            if not self.through:
                # Make custom m2m fields with no through model defined usable.
                return obj.pk
            fk = self.through._meta.get_field(field_name)
            if fk.rel.field_name and fk.rel.field_name != fk.rel.to._meta.pk.attname:
                attname = fk.rel.get_related_field().get_attname()
                return fk.get_prep_lookup('exact', getattr(obj, attname))
            else:
                return obj.pk

        def get_query_set(self):
            try:
                return self.instance._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                db = self._db or router.db_for_read(self.instance.__class__, instance=self.instance)
                return super(ManyRelatedManager, self).get_query_set().using(db)._next_is_sticky().filter(**self.core_filters)

        def get_prefetch_query_set(self, instances):
            instance = instances[0]
            from django.db import connections
            db = self._db or router.db_for_read(instance.__class__, instance=instance)
            query = {'%s__pk__in' % self.query_field_name:
                         set(obj._get_pk_val() for obj in instances)}
            qs = super(ManyRelatedManager, self).get_query_set().using(db)._next_is_sticky().filter(**query)

            # M2M: need to annotate the query in order to get the primary model
            # that the secondary model was actually related to. We know that
            # there will already be a join on the join table, so we can just add
            # the select.

            # For non-autocreated 'through' models, can't assume we are
            # dealing with PK values.
            fk = self.through._meta.get_field(self.source_field_name)
            source_col = fk.column
            join_table = self.through._meta.db_table
            connection = connections[db]
            qn = connection.ops.quote_name
            qs = qs.extra(select={'_prefetch_related_val':
                                      '%s.%s' % (qn(join_table), qn(source_col))})
            select_attname = fk.rel.get_related_field().get_attname()
            return (qs,
                    attrgetter('_prefetch_related_val'),
                    attrgetter(select_attname),
                    False,
                    self.prefetch_cache_name)

        # If the ManyToMany relation has an intermediary model,
        # the add and remove methods do not exist.
        if rel.through._meta.auto_created:
            def add(self, *objs):
                self._add_items(self.source_field_name, self.target_field_name, *objs)

                # If this is a symmetrical m2m relation to self, add the mirror entry in the m2m table
                if self.symmetrical:
                    self._add_items(self.target_field_name, self.source_field_name, *objs)
            add.alters_data = True

            def remove(self, *objs):
                self._remove_items(self.source_field_name, self.target_field_name, *objs)

                # If this is a symmetrical m2m relation to self, remove the mirror entry in the m2m table
                if self.symmetrical:
                    self._remove_items(self.target_field_name, self.source_field_name, *objs)
            remove.alters_data = True

        def clear(self):
            self._clear_items(self.source_field_name)

            # If this is a symmetrical m2m relation to self, clear the mirror entry in the m2m table
            if self.symmetrical:
                self._clear_items(self.target_field_name)
        clear.alters_data = True

        def create(self, **kwargs):
            # This check needs to be done here, since we can't later remove this
            # from the method lookup table, as we do with add and remove.
            if not self.through._meta.auto_created:
                opts = self.through._meta
                raise AttributeError("Cannot use create() on a ManyToManyField which specifies an intermediary model. Use %s.%s's Manager instead." % (opts.app_label, opts.object_name))
            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            new_obj = super(ManyRelatedManager, self.db_manager(db)).create(**kwargs)
            self.add(new_obj)
            return new_obj
        create.alters_data = True

        def get_or_create(self, **kwargs):
            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            obj, created = \
                super(ManyRelatedManager, self.db_manager(db)).get_or_create(**kwargs)
            # We only need to add() if created because if we got an object back
            # from get() then the relationship already exists.
            if created:
                self.add(obj)
            return obj, created
        get_or_create.alters_data = True

        def _add_items(self, source_field_name, target_field_name, *objs):
            # source_field_name: the PK fieldname in join table for the source object
            # target_field_name: the PK fieldname in join table for the target object
            # *objs - objects to add. Either object instances, or primary keys of object instances.

            # If there aren't any objects, there is nothing to do.
            from django.db.models import Model
            if objs:
                new_ids = set()
                for obj in objs:
                    if isinstance(obj, self.model):
                        if not router.allow_relation(obj, self.instance):
                           raise ValueError('Cannot add "%r": instance is on database "%s", value is on database "%s"' %
                                               (obj, self.instance._state.db, obj._state.db))
                        fk_val = self._get_fk_val(obj, target_field_name)
                        if fk_val is None:
                            raise ValueError('Cannot add "%r": the value for field "%s" is None' %
                                             (obj, target_field_name))
                        new_ids.add(self._get_fk_val(obj, target_field_name))
                    elif isinstance(obj, Model):
                        raise TypeError("'%s' instance expected, got %r" % (self.model._meta.object_name, obj))
                    else:
                        new_ids.add(obj)
                db = router.db_for_write(self.through, instance=self.instance)
                vals = self.through._default_manager.using(db).values_list(target_field_name, flat=True)
                vals = vals.filter(**{
                    source_field_name: self._fk_val,
                    '%s__in' % target_field_name: new_ids,
                })
                new_ids = new_ids - set(vals)

                if self.reverse or source_field_name == self.source_field_name:
                    # Don't send the signal when we are inserting the
                    # duplicate data row for symmetrical reverse entries.
                    signals.m2m_changed.send(sender=self.through, action='pre_add',
                        instance=self.instance, reverse=self.reverse,
                        model=self.model, pk_set=new_ids, using=db)
                # Add the ones that aren't there already
                self.through._default_manager.using(db).bulk_create([
                    self.through(**{
                        '%s_id' % source_field_name: self._fk_val,
                        '%s_id' % target_field_name: obj_id,
                    })
                    for obj_id in new_ids
                ])

                if self.reverse or source_field_name == self.source_field_name:
                    # Don't send the signal when we are inserting the
                    # duplicate data row for symmetrical reverse entries.
                    signals.m2m_changed.send(sender=self.through, action='post_add',
                        instance=self.instance, reverse=self.reverse,
                        model=self.model, pk_set=new_ids, using=db)

        def _remove_items(self, source_field_name, target_field_name, *objs):
            # source_field_name: the PK colname in join table for the source object
            # target_field_name: the PK colname in join table for the target object
            # *objs - objects to remove

            # If there aren't any objects, there is nothing to do.
            if objs:
                # Check that all the objects are of the right type
                old_ids = set()
                for obj in objs:
                    if isinstance(obj, self.model):
                        old_ids.add(self._get_fk_val(obj, target_field_name))
                    else:
                        old_ids.add(obj)
                # Work out what DB we're operating on
                db = router.db_for_write(self.through, instance=self.instance)
                # Send a signal to the other end if need be.
                if self.reverse or source_field_name == self.source_field_name:
                    # Don't send the signal when we are deleting the
                    # duplicate data row for symmetrical reverse entries.
                    signals.m2m_changed.send(sender=self.through, action="pre_remove",
                        instance=self.instance, reverse=self.reverse,
                        model=self.model, pk_set=old_ids, using=db)
                # Remove the specified objects from the join table
                self.through._default_manager.using(db).filter(**{
                    source_field_name: self._fk_val,
                    '%s__in' % target_field_name: old_ids
                }).delete()
                if self.reverse or source_field_name == self.source_field_name:
                    # Don't send the signal when we are deleting the
                    # duplicate data row for symmetrical reverse entries.
                    signals.m2m_changed.send(sender=self.through, action="post_remove",
                        instance=self.instance, reverse=self.reverse,
                        model=self.model, pk_set=old_ids, using=db)

        def _clear_items(self, source_field_name):
            db = router.db_for_write(self.through, instance=self.instance)
            # source_field_name: the PK colname in join table for the source object
            if self.reverse or source_field_name == self.source_field_name:
                # Don't send the signal when we are clearing the
                # duplicate data rows for symmetrical reverse entries.
                signals.m2m_changed.send(sender=self.through, action="pre_clear",
                    instance=self.instance, reverse=self.reverse,
                    model=self.model, pk_set=None, using=db)
            self.through._default_manager.using(db).filter(**{
                source_field_name: self._fk_val
            }).delete()
            if self.reverse or source_field_name == self.source_field_name:
                # Don't send the signal when we are clearing the
                # duplicate data rows for symmetrical reverse entries.
                signals.m2m_changed.send(sender=self.through, action="post_clear",
                    instance=self.instance, reverse=self.reverse,
                    model=self.model, pk_set=None, using=db)

    return ManyRelatedManager