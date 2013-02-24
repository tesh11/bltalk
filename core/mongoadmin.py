from mongonaut.sites import MongoAdmin
from core.models import Listing

Listing.mongoadmin = MongoAdmin()