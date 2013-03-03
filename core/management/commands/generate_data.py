import random
import string
import sys
from bson import json_util

from django.core.management import BaseCommand
from mongoengine.django.auth import User
from core.models import Listing


ZIPCODES = ['78701', '78702', '78703', '78704', '78705']


class Command(BaseCommand):
    args = '<num rows> <filename>'

    def handle(self, *args, **options):
        with open(args[1], 'w') as out:
            num_rows = int(args[0])

            users = User.objects.filter(username__ne='admin')

            for i in xrange(0, num_rows):
                if i % 1000 == 0:
                    sys.stdout.write(".")
                    sys.stdout.flush()

                # title, description, zipcode, amount, owner
                l = Listing(title=_random_string(), description=_random_string(1000), zipcode=_random_zipcode(),
                            amount=random.random() * 100.0, owner=_random_user(users))
                print>>out, json_util.dumps(l.to_mongo())


def _random_string(max_length=200):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(max_length))


def _random_zipcode():
    return ZIPCODES[int(random.random() * len(ZIPCODES))]


def _random_user(users):
    return users[int(random.random() * 10)]