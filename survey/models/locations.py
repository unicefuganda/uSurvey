from django.db import models
# from django.db.models.signals import post_save
from mptt.models import MPTTModel, TreeForeignKey
from mptt.managers import TreeManager
from survey.models.base import BaseModel


class Point(BaseModel):
    """
    This model represents an anonymous point on the globe. It should be
    replaced with something from GeoDjango soon, but I can't seem to get
    Spatialite to build right now...
    """

    latitude = models.DecimalField(max_digits=13, decimal_places=10)
    longitude = models.DecimalField(max_digits=13, decimal_places=10)

    def __unicode__(self):
        return "%s, %s" % (self.latitude, self.longitude)


class LocationType(MPTTModel, BaseModel):
    name = models.CharField(max_length=200, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='sub_types', db_index=True)
    location_code = models.PositiveIntegerField(null=True, blank=True)
    slug = models.SlugField()

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'survey'

    @classmethod
    def all(cls):
        return cls.objects.all().order_by('level')

    @classmethod
    def smallest_unit(cls):
        try:
            root_node = cls.objects.get(parent=None)
            return root_node.get_leafnodes(False).get(parent__isnull=False)
        except cls.DoesNotExist as IndexError:
            return None

    @classmethod
    def largest_unit(cls):
        try:
            root_node = cls.objects.get(parent=None)
            return root_node.get_children()[0]
        except cls.DoesNotExist:
            return None
        except IndexError:
            return None

    @classmethod
    def in_between(cls):
        if cls.objects.exists():
            return cls.objects.exclude(
                pk=LocationType.smallest_unit().pk).exclude(
                parent__isnull=True)
        else:
            return cls.objects.none()


class Location(MPTTModel, BaseModel):
    name = models.CharField(max_length=200, db_index=True)
    type = models.ForeignKey(LocationType, related_name='locations')
    code = models.CharField(max_length=200, null=True, blank=True)
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='sub_locations', db_index=True)
    # would use this in the future. But ignore for now
    coordinates = models.ManyToManyField(
        Point, related_name='admin_div_locations')
    tree = TreeManager()
    objects = models.Manager()

    class MPTTMeta:
        order_insertion_by = ['name']
        ordering = ['name', ]

    def __unicode__(self):
        return self.name

    @property
    def tree_parent(self):
        return self.parent

    @classmethod
    def country(cls):
        try:
            return Location.objects.get(parent__isnull=True)
        except Location.DoesNotExist:
            return None

    def is_sub_location(self, location):
        return location.is_ancestor_of(self)

    class Meta:
        app_label = 'survey'
        # unique_together = [('code', 'type'), ]
