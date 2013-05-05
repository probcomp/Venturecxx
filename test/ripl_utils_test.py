import unittest
from venture.ripl import utils
from venture.exception import VentureException


class DummyParser():
    def value_to_string(self, v):
        return str(v)[::-1]

class TestRiplUtils(unittest.TestCase):

    def test_substitute_params_list(self):
        p = DummyParser()
        output = utils.substitute_params('abc',[],p)
        self.assertEquals(output, 'abc')
        output = utils.substitute_params('abc%%',[],p)
        self.assertEquals(output, 'abc%')
        output = utils.substitute_params('abc%s',['d'],p)
        self.assertEquals(output, 'abcd')
        output = utils.substitute_params('abc%v',['de'],p)
        self.assertEquals(output, 'abced')
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%s',[],p)
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%',[],p)
        with self.assertRaises(VentureException):
            utils.substitute_params('abc',['d'],p)

    def test_substitute_params_dict(self):
        p = DummyParser()
        output = utils.substitute_params('abc',{},p)
        self.assertEquals(output, 'abc')
        output = utils.substitute_params('abc%%',{},p)
        self.assertEquals(output, 'abc%')
        output = utils.substitute_params('abc%(x)s',{'x':'d'},p)
        self.assertEquals(output, 'abcd')
        output = utils.substitute_params('abc%(%)v',{'%':'de'},p)
        self.assertEquals(output, 'abced')
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%()s',{},p)
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%(s)',{},p)
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%s',{},p)




if __name__ == '__main__':
    unittest.main()
