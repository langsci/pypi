import unittest

import indextools
import asciify
import bibtools
import delatex

class TestFixIndex(unittest.TestCase):
    """ Test the adaption of the indexes
    """

    def test_fixindex(self):
        """ Test a full index line
        """
        result = indextools.processline(r"\indexentry {\v{C}{\'{e}}pl\"o, Slavomír@\v{C}{\'{e}}pl\"o, Slavomír|hyperpage}{2}")
        self.assertEqual(result, r"\indexentry {Ceplo, Slavomir@\v{C}{\'{e}}pl\"o, Slavomír|hyperpage}{2}")
        
        
        
class TestASCII(unittest.TestCase):
    """ Test the adaption of the indexes
    """
        
        
    def test_asciify(self):
        """ Test an isolated string
        """
        result = asciify.asciify("Nædéßoþ")
        self.assertEqual(result, "Naedessoth")
        
    def test_dediacriticize(self):
        """ Test an isolated string
        """
        result = delatex.dediacriticize(r"Bád\'ag\'{a}p{\'{a}}")
        self.assertEqual(result, "Bádagapa")
        
        
        result = delatex.dediacriticize(r"Bád\'ag\'{a}p{\'{a}}", stripbraces=False)
        self.assertEqual(result, "Bádagap{a}")
        
        result = delatex.dediacriticize(r"""\'{a}\`{a}\^{a}\~{a}\"{a}\={a}\.{a}\d{a}\v{a}\H{a}\u{a}\k{a}""")
        self.assertEqual(result, "aaaaaaaaaaaa")
        
class TestBibConversion(unittest.TestCase):
    """ Test the conversion of inline literature references to BibTex
    """
    maxDiff=None
    
    def test_record(self):
        bibtests = (("Mufwene, Salikoko. 2001. The Ecology of Language Evolution. Cambridge: Cambridge University Press.",
                        """@book{Mufwene2001,\n\taddress = {Cambridge},\n\tauthor = {Mufwene, Salikoko},\n\tpublisher = {Cambridge University Press},\n\ttitle = {The Ecology of Language Evolution},\n\tyear = {2001}\n}\n"""),
                    #("Alleyne, Mervyn C. 1996. Syntaxe historique créole. Paris, France: Karthala.","""@book{Alleyne1996,\n\taddress = {Paris, France},\n\tauthor = {Alleyne, Mervyn C.},\n\tpublisher = {Karthala},\n\tsortname = {Alleyne, Mervyn C.},\n\ttitle = {Syntaxe historique créole},\n\tyear = {1996}\n}\n"""),
                    ("Allsopp, Richard. (ed.), 2003. Dictionary of Caribbean English usage. Kingston, Jamaica: University of the West Indies Press.","""@book{Allsopp2003,\n\taddress = {Kingston, Jamaica},\n\tbooktitle = {Dictionary of {Caribbean} {English} usage},\n\teditor = {Allsopp, Richard},\n\tpublisher = {University of the West Indies Press},\n\ttitle = {Dictionary of {Caribbean} {English} usage},\n\tyear = {2003}\n}\n"""),
                    ("Ammon, Matthias. 2013. The functions of oath and pledge in Anglo-Saxon legal culture. Historical Research. 86(233), 515-535.","""@article{Ammon2013,\n\tauthor = {Ammon, Matthias},\n\tjournal = {Historical Research},\n\tnumber = {233},\n\tpages = {515--535},\n\ttitle = {The functions of oath and pledge in {Anglo}-{Saxon} legal culture},\n\tvolume = {86},\n\tyear = {2013}\n}\n"""),
                    ("Andriotis, Nikolaos. 1995. History of the Greek Language: Four studies. Thessaloniki, Greece: Ίδρυμα Τριανταφυλλίδη.","""@book{Andriotis1995,\n\taddress = {Thessaloniki, Greece},\n\tauthor = {Andriotis, Nikolaos},\n\tpublisher = {Ίδρυμα Τριανταφυλλίδη},\n\ttitle = {History of the {Greek} Language: {{F}}our studies},\n\tyear = {1995}\n}\n"""),
                    ("Archer, Dawn. 2010. Speech acts. In Andreas H. Jucker & Irma Taavitsainen (eds.), Historical pragmatics, 379-418. Berlin, Germany: Walter de Gruyter GmbH & Co.","""@incollection{Archer2010,\n\taddress = {Berlin, Germany},\n\tauthor = {Archer, Dawn},\n\tbooktitle = {Historical pragmatics},\n\teditor = {Andreas H. Jucker and Irma Taavitsainen},\n\tpages = {379--418},\n\tpublisher = {Walter de Gruyter GmbH & Co},\n\ttitle = {Speech acts},\n\tyear = {2010}\n}\n"""),
                    ("Auer, Peter & Hinskens, Frans & Kerswill, Paul. (eds.), 2005.  Dialect change: Convergence and divergence in European languages. Cambridge, England: The Cambridge University Press. ","""@book{Auer2005,\n\taddress = {Cambridge, England},\n\tbooktitle = {Dialect change: {{C}}onvergence and divergence in {European} languages},\n\teditor = {Auer, Peter and Hinskens, Frans and Kerswill, Paul},\n\tpublisher = {The Cambridge University Press},\n\ttitle = {Dialect change: {{C}}onvergence and divergence in {European} languages},\n\tyear = {2005}\n}\n"""),
                    #("Awbery, G. M. 1988. Slander and defamation as a source for historical dialectology. In Alan R. Thomas (ed.), Methods in dialectology: Proceedings of the sixth international conference held at the University College of North Wales, 3rd-7th August 1987, 164-174. Clevedon, PA: Multilingual Matters Ltd.","""@incollection{Awbery1988,\n\taddress = {Clevedon, PA},\n\tauthor = {Awbery, G. M.},\n\tbooktitle = {Methods in dialectology: {{P}}roceedings of the sixth international conference held at the University College of {North} {Wales}, 3rd-7th {August} 1987},\n\teditor = {Alan R. Thomas},\n\tpages = {164--174},\n\tpublisher = {Multilingual Matters Ltd},\n\tsortname = {Awbery, G. M.},\n\ttitle = {Slander and defamation as a source for historical dialectology},\n\tyear = {1988}\n}\n"""),
                    ("Bailey, Guy & Ross, Garry. 1988. The shape of the superstrate: Morphosyntactic features of Ship English. English World-Wide. 9(2) 193-212.","""@article{Bailey1988,\n\tauthor = {Bailey, Guy and Ross, Garry},\n\tjournal = {English World-Wide},\n\tnumber = {2},\n\tpages = {193--212},\n\ttitle = {The shape of the superstrate: {{M}}orphosyntactic features of Ship {English}},\n\tvolume = {9},\n\tyear = {1988}\n}\n"""),
                    ("Baker, Philip & Huber, Magnus. 2001. Atlantic, Pacific, and world-wide features in English-lexicon contact languages. English World-Wide. 22(2), 157-208.","""@article{Baker2001,\n\tauthor = {Baker, Philip and Huber, Magnus},\n\tjournal = {English World-Wide},\n\tnumber = {2},\n\tpages = {157--208},\n\ttitle = {{Atlantic}, {Pacific}, and world-wide features in {English}-lexicon contact languages},\n\tvolume = {22},\n\tyear = {2001}\n}\n"""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("",""""""),
                    ##("","""""")
                    )
        for s, expected in bibtests:
            record = bibtools.Record(s)
            self.assertEqual(record.bibstring, expected)
      
      #TODO add more and different entry types of varying complexity
    
        
if __name__ == '__main__':
    unittest.main()