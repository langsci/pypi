import unittest
import fixindex

# fixindex

class TestFixIndex(unittest.TestCase):
    """
    Our basic test class
    """

    def test_fixindex(self):
        """
        The actual test.
        Any method which starts with ``test_`` will considered as a test case.
        """
        result = fixindex.processline(r"\indexentry {\v{C}{\'{e}}pl\"o, Slavomír@\v{C}{\'{e}}pl\"o, Slavomír|hyperpage}{2}")
        self.assertEqual(result, r"\indexentry {Ceplo, Slavomir@\v{C}{\'{e}}pl\"o, Slavomír|hyperpage}{2}")
        
if __name__ == '__main__':
    unittest.main()