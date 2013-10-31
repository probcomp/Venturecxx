import unittest
from venture.exception import VentureException

JSON_EXCEPTION = {
        "exception":"exception_type",
        "message":"everything exploded",
        "data1":1,
        "data2":[1,2,3],
        }

EXCEPTION = 'exception_type'
MESSAGE = 'everything exploded'
DATA = {'data1':1,'data2':[1,2,3]}

class TestVentureException(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor(self):
        e = VentureException(EXCEPTION,
                MESSAGE,**DATA)
        self.assertEqual(e.exception, EXCEPTION)
        self.assertEqual(e.message, MESSAGE)
        self.assertEqual(e.data, DATA)

    def test_to_json_object(self):
        e = VentureException(EXCEPTION,
                MESSAGE,**DATA)
        self.assertEqual(e.to_json_object(),JSON_EXCEPTION)

    def test_from_json_object(self):
        e = VentureException.from_json_object(JSON_EXCEPTION)
        self.assertEqual(e.to_json_object(),JSON_EXCEPTION)


if __name__ == '__main__':
    unittest.main()