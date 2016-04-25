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

    latitude  = models.DecimalField(max_digits=13, decimal_places=10)
    longitude = models.DecimalField(max_digits=13, decimal_places=10)

    def __unicode__(self):
        return "%s, %s" % (self.latitude, self.longitude)

    def __repr__(self):
        return '<%s: %s>' %\
            (type(self).__name__, self)


class LocationType(MPTTModel, BaseModel):
    name = models.CharField(max_length=200, unique=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='sub_types', db_index=True)
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
            return root_node.get_leafnodes(False)[0]
        except cls.DoesNotExist, IndexError:
            return None

    @classmethod
    def largest_unit(cls):
        try:
            root_node = cls.objects.get(parent=None)
            return root_node.get_children()[0]
        except cls.DoesNotExist, IndexError:
            return None

    @classmethod
    def in_between(cls):
        if cls.objects.exists():
            return cls.objects.exclude(pk=LocationType.smallest_unit().pk).exclude(parent__isnull=True)
        else:
            return cls.objects.none()


class Location(MPTTModel, BaseModel):
    name = models.CharField(max_length=50)
    type = models.ForeignKey(LocationType, related_name='locations')
    code = models.CharField(max_length=100, null=True, blank=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='sub_locations', db_index=True)
    coordinates = models.ManyToManyField(Point, related_name='admin_div_locations') #would use this in the future. But ignore for now
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

    def is_sub_location(self, location):
        return location.is_ancestor_of(self)

    class Meta:
        app_label = 'survey'
        # unique_together = [('code', 'type'), ]


#
# class LocationCode(BaseModel):
#     location = models.ForeignKey(Location, null=False, related_name="code")
#     code = models.CharField(max_length=10, null=False, default=0)
#
#     @classmethod
#     def get_household_code(cls, interviewer):
#         location_hierarchy = interviewer.locations_in_hierarchy()
#         codes = cls.objects.filter(location__in=location_hierarchy).order_by('location').values_list('code', flat=True)
#         return ''.join(codes)
#
#
# class LocationAutoComplete(models.Model):
#     location = models.ForeignKey(Location, null=True)
#     text = models.CharField(max_length=500)
#
#     class Meta:
#         app_label = 'survey'
#
#
# def generate_auto_complete_text_for_location(location):
#     auto_complete = LocationAutoComplete.objects.filter(location=location)
#     if not auto_complete:
#         auto_complete = LocationAutoComplete(location=location)
#     else:
#         auto_complete = auto_complete[0]
#     parents = [location.name]
#     while location.tree_parent:
#         location = location.tree_parent
#         parents.append(location.name)
#     parents.reverse()
#     auto_complete.text = " > ".join(parents)
#     auto_complete.save()
#
#
# @receiver(post_save, sender=Location)
# def create_location_auto_complete_text(sender, instance, **kwargs):
#     generate_auto_complete_text_for_location(instance)
#     for location in instance.get_descendants():
#         generate_auto_complete_text_for_location(location)
#
#
# def auto_complete_text(self):
#     return LocationAutoComplete.objects.get(location=self).text
#
#
# Location.auto_complete_text = auto_complete_text