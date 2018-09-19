import unittest
import langsci
import fixindex
import asciify
import langscibibtex

class TestFixIndex(unittest.TestCase):
    """ Test the adaption of the indexes
    """

    def test_fixindex(self):
        """ Test a full index line
        """
        result = fixindex.processline(r"\indexentry {\v{C}{\'{e}}pl\"o, Slavomír@\v{C}{\'{e}}pl\"o, Slavomír|hyperpage}{2}")
        self.assertEqual(result, r"\indexentry {Ceplo, Slavomir@\v{C}{\'{e}}pl\"o, Slavomír|hyperpage}{2}")
        
        
    def test_asciify(self):
        """ Test an isolated string
        """
        result = asciify.asciify("Nædéßoþ")
        self.assertEqual(result, "Naedessoth")
        
class TestBibConversion(unittest.TestCase):
    """ Test the conversion of inline literature references to BibTex
    """
    
    def test_record(self):
      s = "Mufwene, Salikoko. 2001. The Ecology of Language Evolution. Cambridge: Cambridge University Press."
      expected = """@book{Mufwene2001,\n\taddress = {Cambridge},\n\tauthor = {Mufwene, Salikoko},\n\tpublisher = {Cambridge University Press},\n\ttitle = {The Ecology of Language Evolution},\n\tyear = {2001}\n}\n"""
      record = langscibibtex.Record(s)
      self.assertEqual(record.bibstring, expected)
      
      #TODO add more and different entry types of varying complexity
    
        
if __name__ == '__main__':
    unittest.main()