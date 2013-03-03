import random
import string
from funkload.FunkLoadTestCase import FunkLoadTestCase


class Basic(FunkLoadTestCase):
    ZIPCODES = ['78701', '78702', '78703', '78704', '78705']

    def setUpCycle(self):
        self.server_url = self.conf_get('main', 'url')

        # reset the db state via a get call
        self.get('%s/setup_test/' % self.server_url)

    def setUp(self):
        self.server_url = self.conf_get('main', 'url')

        # reset the db state via a get call
        # self.get('%s/setup_test' % self.server_url)

    # TODO: add search by zipcode and random zipcode selection
    def test_create_and_list(self):
        # 1. view list anonymously
        self.get('%s/' % self.server_url, description="view list anonymously")

        # 2. search by zipcode
        self.post('%s/' % self.server_url, params=[('zipcode', self._random_zipcode())],
                  description="search by zipcode")

        # 3. choose random user and login
        usernum = int(random.random() * 10) + 1
        username = 'user%d' % usernum
        self.get('%s/login/' % self.server_url, description="view login page")
        self.post('%s/login/' % self.server_url, params=[['username', username], ['password', username]],
                  description='login')

        # 4. view list as user
        self.get('%s/' % self.server_url, description="view list as user")

        # 5. search by zipcode
        self.post('%s/' % self.server_url, params=[('zipcode', self._random_zipcode())],
                  description="search by zipcode")

        # 6. create a listing
        self.get('%s/listing/new/' % self.server_url, description='view new listing page')
        self.post('%s/listing/new/' % self.server_url, params=[['title', self._random_string()],
                                                               ['description', self._random_string()],
                                                               ['amount', random.random() * 100.0],
                                                               ['zipcode', self._random_zipcode()]])

        # 7. view list as user
        self.get('%s/' % self.server_url, description="view list as user")

        # 8. clear the search
        self.post('%s/' % self.server_url, params=[('zipcode', '')], description="search by zipcode")

        # 9. logout
        self.get('%s/logout/' % self.server_url)

        # 10. view list anonymously
        self.get('%s/' % self.server_url, description="view list anonymously")

    def _random_string(self, max_length=200):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(max_length))

    def _random_zipcode(self):
        return self.ZIPCODES[int(random.random() * len(self.ZIPCODES))]