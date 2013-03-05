import random
import string
import sys
from django.conf import settings

from django.core.management import BaseCommand
from core import models
from core.auth import User


ZIPCODES = ['78701', '78702', '78703', '78704', '78705']


class Command(BaseCommand):
    args = '<num rows> <filename>'

    def handle(self, *args, **options):
        num_rows = int(args[0])

        users = models.get_users(settings.DB)

        for i in xrange(0, num_rows):
            models.set_listing(settings.DB, _random_user(users), _random_string(), _random_string(1000),
                               random.random() * 100.0, _random_zipcode())
            if i % 1000 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()


def _random_string(max_length=200):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(max_length))


def _random_zipcode():
    return ZIPCODES[int(random.random() * len(ZIPCODES))]


def _random_user(users):
    return User(users[int(random.random() * 10)])