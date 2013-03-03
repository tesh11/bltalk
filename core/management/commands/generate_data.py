import random
import string
import sys

from django.contrib.auth.models import User
from django.core.management import BaseCommand


ZIPCODES = ['78701', '78702', '78703', '78704', '78705']


class Command(BaseCommand):
    args = '<num rows> <filename>'

    def handle(self, *args, **options):
        with open(args[1], 'w') as out:
            num_rows = int(args[0])

            users = User.objects.exclude(username='admin')

            for i in xrange(0, num_rows):
                if i % 1000 == 0:
                    sys.stdout.write(".")
                    sys.stdout.flush()

                # title, description, zipcode, amount, owner
                print>>out, "\t".join((_random_string(), _random_string(1000), _random_zipcode(),
                                       str(random.random() * 100.0), _random_user(users)))


def _random_string(max_length=200):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(max_length))


def _random_zipcode():
    return ZIPCODES[int(random.random() * len(ZIPCODES))]


def _random_user(users):
    return str(users[int(random.random() * 10)].id)