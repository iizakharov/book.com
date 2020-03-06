import os
from uuid import uuid4

from django.db import models
from django.db.models import Q
from django.utils.deconstruct import deconstructible


@deconstructible
class PathAndRename(object):

    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = f'{uuid4().hex}.{ext}'

        return os.path.join(self.path, filename)


path_and_rename = PathAndRename("static/img/tmp")


class Hotel(models.Model):
    class Meta:
        verbose_name = 'Отель'
        verbose_name_plural = 'Отели'
        ordering = ['name']

    ONE = 'ON'
    TWO = 'TW'
    THREE = 'TR'
    FOUR = 'FR'
    FIVE = 'FV'
    STARS_CHOICES = [
        (ONE, '1*'),
        (TWO, '2*'),
        (THREE, '3*'),
        (FOUR, '4*'),
        (FIVE, '5*'),
    ]

    name = models.CharField(verbose_name='Название отеля', max_length=64,
                            unique=True)
    description = models.TextField(verbose_name='Описание отеля', blank=True)
    stars = models.CharField(max_length=2, choices=STARS_CHOICES, default=ONE)
    is_active = models.BooleanField(verbose_name='Активен', default=True)

    def __str__(self):
        return self.name


class RoomAgent(models.Model):
    class Meta:
        verbose_name = 'Агент'
        verbose_name_plural = 'Агенты'
        ordering = ['name']

    name = models.CharField(verbose_name='Имя агента', max_length=64,
                            unique=True)
    description = models.CharField(verbose_name='Краткое описание агента',
                                   max_length=128, blank=True)
    is_active = models.BooleanField(verbose_name='Активен', default=True)

    def __str__(self):
        return self.name


class RoomManager(models.Manager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query is not None:
            or_lookup = (
                    Q(name__icontains=query) |
                    Q(description__icontains=query)
            )
            # distinct() is often necessary with Q lookups
            qs = qs.filter(or_lookup).distinct()
        return qs


class Room(models.Model):
    class Meta:
        verbose_name = 'Номер'
        verbose_name_plural = 'Номера'
        ordering = ['name']
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    name = models.CharField(verbose_name='Имя', max_length=32)
    price = models.DecimalField(verbose_name='Цена', max_digits=12,
                                decimal_places=2, default=0)
    adult = models.BooleanField(verbose_name='Взрослый', default=True)
    kids = models.BooleanField(verbose_name='Детский', default=False)
    infants = models.BooleanField(verbose_name='Детский', default=False)
    image = models.ImageField(upload_to=path_and_rename, blank=True)
    description = models.TextField(verbose_name='Описание', blank=True)
    is_active = models.BooleanField(verbose_name='Номер активен', default=True)

    objects = RoomManager()

    def __str__(self):
        return "{} ({})".format(self.name, self.hotel.name)

    def __unicode__(self):
        return f'{self.name}'

    @property
    def get_avatar(self):
        try:
            avatar = self.images.filter(is_avatar=True).first().image.url
        except AttributeError:
            avatar = '/static/img/any.webp'
        return avatar


class RoomGallery(models.Model):
    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'
        ordering = ['image']

    room = models.ForeignKey(Room, on_delete=models.CASCADE,
                             related_name='images',
                             verbose_name='Название номера')
    image = models.ImageField(upload_to=path_and_rename,
                              height_field='image_height',
                              width_field='image_width',
                              verbose_name='Изображение номера'
                              )
    is_avatar = models.BooleanField(verbose_name='Главное изображение номера',
                                    default=False)
    image_height = models.PositiveIntegerField(null=True, blank=True,
                                               editable=False, default='100')
    image_width = models.PositiveIntegerField(null=True, blank=True,
                                              editable=False, default='100')

    def __str__(self):
        return f'{self.room.name}'