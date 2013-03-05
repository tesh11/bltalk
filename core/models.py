import datetime
from uuid import uuid4
from django.contrib.auth.hashers import make_password, check_password
import fdb.tuple
import fdb


@fdb.transactional
def table_set_cell(tr, table, row, column, value):
    tr[fdb.tuple.pack((table, row, column))] = str(value)


@fdb.transactional
def table_get_cell(tr, table, row, column):
    return tr[fdb.tuple.pack((table, row, column))]


@fdb.transactional
def table_set_row(tr, table, row, cols):
    del tr[fdb.tuple.range((table, row, ))]
    for c, v in cols.iteritems():
        table_set_cell(tr, table, row, c, v)


@fdb.transactional
def table_get_row(tr, table, row):
    cols = {}
    for k, v in tr[fdb.tuple.range((table, row, ))]:
        t, r, c = fdb.tuple.unpack(k)
        cols[c] = v
    return cols


@fdb.transactional
def set_session_data(tr, user, session_id, zipcode=None, set_zipcode=True):
    if user:
        tr[fdb.tuple.pack(('session_data', user.id, 'session_id'))] = session_id
        if set_zipcode:
            if zipcode:
                tr[fdb.tuple.pack(('session_data', user.id, 'zipcode'))] = str(zipcode)
            else:
                del tr[fdb.tuple.pack(('session_data', user.id, 'zipcode'))]
        tr[fdb.tuple.pack(('session_data', user.id, 'last_update_timestamp'))] = datetime.datetime.now().strftime('%s')
    else:
        if set_zipcode:
            if zipcode:
                tr[fdb.tuple.pack(('session_data_anon', session_id, 'zipcode'))] = str(zipcode)
            else:
                del tr[fdb.tuple.pack(('session_data_anon', session_id, 'zipcode'))]
        tr[fdb.tuple.pack(('session_data_anon', session_id, 'last_update_timestamp'))] = \
            datetime.datetime.now().strftime('%s')


@fdb.transactional
def get_session_data_by_user(tr, user):
    retval = {}
    session_id = tr[fdb.tuple.pack(('session_data', user.id, 'session_id'))]
    if session_id:
        retval['session_id'] = session_id
        retval['zipcode'] = tr[fdb.tuple.pack(('session_data', user.id, 'zipcode'))]
        retval['last_update_timestamp'] = tr[fdb.tuple.pack(('session_data', user.id, 'last_update_timestamp'))]

    return retval


@fdb.transactional
def get_session_data_by_session_id(tr, session_id):
    retval = {}
    last_update_timestamp = tr[fdb.tuple.pack(('session_data_anon', session_id, 'last_update_timestamp'))]
    if last_update_timestamp:
        retval['zipcode'] = tr[fdb.tuple.pack(('session_data_anon', session_id, 'zipcode'))]
        retval['last_update_timestamp'] = last_update_timestamp

    return retval


def set_user(db, username, password):
    table_set_cell(db, 'user', username, 'password', make_password(password))


def get_user(db, username):
    if table_get_cell(db, 'user', username, 'password'):
        return {'username': username}


def check_password_match(db, username, password):
    return check_password(password, table_get_cell(db, 'user', username, 'password'))


@fdb.transactional
def set_listing(tr, owner, title, description, amount, zipcode):
    listing_id = str(uuid4())
    table_set_row(tr, 'listing', listing_id, {'owner': owner.id,
                                              'title': title,
                                              'description': description,
                                              'amount': str(amount),
                                              'zipcode': zipcode,
                                              })
    padded_amount = '%010d' % (amount * 10000000)
    tr[fdb.tuple.pack(('listing_idx', padded_amount, listing_id))] = ''
    tr[fdb.tuple.pack(('listing_zipcode_idx', zipcode, padded_amount, listing_id))] = ''


@fdb.transactional
def get_all_listings_sorted_by_amount(tr, limit=0):
    key_slice = fdb.tuple.range(('listing_idx', ))
    items = tr.get_range(key_slice.start, key_slice.stop, limit)
    return [table_get_row(tr, 'listing', fdb.tuple.unpack(k)[-1]) for k, v in items]


@fdb.transactional
def get_listing_by_zipcode_sorted_by_amount(tr, zipcode, limit=0):
    key_slice = fdb.tuple.range(('listing_zipcode_idx', unicode(zipcode)))
    items = tr.get_range(key_slice.start, key_slice.stop, limit)
    return [table_get_row(tr, 'listing', fdb.tuple.unpack(k)[-1]) for k, v in items]


@fdb.transactional
def clear_data(tr):
    del tr['':'\xFF']


# class SessionData(models.Model):
#     user = models.ForeignKey(User, blank=True, null=True)
#     session_id = models.CharField(max_length=255, unique=True)
#     last_update_timestamp = models.DateTimeField(auto_now=True)
#
#     zipcode = models.CharField(max_length=5, blank=True, null=True)
#
#
# class Listing(models.Model):
#     owner = models.ForeignKey(User)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     amount = models.FloatField()
#     zipcode = models.CharField(max_length=5, db_index=True)