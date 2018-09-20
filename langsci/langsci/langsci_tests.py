import unittest

import langsci
import indextools
import asciify
import langscibibtex

class TestFixIndex(unittest.TestCase):
    """ Test the adaption of the indexes
    """

    def test_fixindex(self):
        """ Test a full index line
        """
        result = indextools.processline(r"\indexentry {\v{C}{\'{e}}pl\"o, Slavomír@\v{C}{\'{e}}pl\"o, Slavomír|hyperpage}{2}")
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
        bibtests = (("Mufwene, Salikoko. 2001. The Ecology of Language Evolution. Cambridge: Cambridge University Press.",
                        """@book{Mufwene2001,\n\taddress = {Cambridge},\n\tauthor = {Mufwene, Salikoko},\n\tpublisher = {Cambridge University Press},\n\ttitle = {The Ecology of Language Evolution},\n\tyear = {2001}\n}\n"""),
                    ("Alleyne, Mervyn C. 1996. Syntaxe historique créole. Paris, France: Karthala.","""@book{Alleyne1996,\n\taddress = {Paris, France},\n\tauthor = {Alleyne, Mervyn C.},\n\tpublisher = {Karthala},\n\tsortname = {Alleyne, Mervyn C.},\n\ttitle = {Syntaxe historique créole},\n\tyear = {1996}\n}\n"""),
                    ("Allsopp, Richard. (ed.), 2003. Dictionary of Caribbean English usage. Kingston, Jamaica: University of the West Indies Press.","""@book{Allsopp2003,\n\taddress = {Kingston, Jamaica},\n\tbooktitle = {Dictionary of {Caribbean} {English} usage},\n\teditor = {Allsopp, Richard},\n\tpublisher = {University of the West Indies Press},\n\ttitle = {Dictionary of {Caribbean} {English} usage},\n\tyear = {2003}\n}\n"""),
                    #("Ammon, Matthias. 2013. The functions of oath and pledge in Anglo-Saxon legal culture. Historical Research. 86(233), 515-535.",""""""),
                    #("Andriotis, Nikolaos. 1995. History of the Greek Language: Four studies. Thessaloniki, Greece: Ίδρυμα Τριανταφυλλίδη.",""""""),
                    #("Archer, Dawn. 2010. Speech acts. In Andreas H. Jucker & Irma Taavitsainen (eds.), Historical pragmatics, 379-418. Berlin, Germany: Walter de Gruyter GmbH & Co.",""""""),
                    #("Auer, Peter & Hinskens, Frans & Kerswill, Paul. (eds.), 2005.  Dialect change: Convergence and divergence in European languages. Cambridge, England: The Cambridge University Press. ",""""""),
                    #("Awbery, G. M. 1988. Slander and defamation as a source for historical dialectology. In Alan R. Thomas (ed.), Methods in dialectology: Proceedings of the sixth international conference held at the University College of North Wales, 3rd-7th August 1987, 164-174. Clevedon, PA: Multilingual Matters Ltd.",""""""),
                    #("Bailey, Guy & Ross, Garry. 1988. The shape of the superstrate: Morphosyntactic features of Ship English. English World-Wide. 9(2) 193-212.",""""""),
                    #("Baker, Philip & Huber, Magnus. 2001. Atlantic, Pacific, and world-wide features in English-lexicon contact languages. English World-Wide. 22(2), 157-208.",""""""),
                    #("Bassett, Fletcher S. 1885. Legends and superstitions of the sea and of sailors in all lands and at all times. Chicago, IL: Belford, Clarke & Co. ",""""""),
                    #("Behn, Aphra. 1684-1687. Love-letters between a nobleman and his sister. Retrieved from Project Guttenberg at http://www.gutenberg.org/files/8409/8409-h/8409-h.htm.",""""""),
                    #("Bicheno, Hugh. 2012. Elizabeth’s sea dogs: How the English became the scourge of the seas. London, England: Conway, Bloomsbury.",""""""),
                    #("Blake, N. F. 2002. A grammar of Shakespeare’s language. New York, NY: Palgrave Macmillan.",""""""),
                    #("Boukman Barima, Kofi. 2016. Cutting across space and time: Obeah’s service to Afro-Jamaica’s freedom struggle in slavery and emancipation. Africology: The Journal of Pan African Studies. 9(4) 16-31.",""""""),
                    #("Bronner, Simon J. 2006. Crossing the line: Violence, play, and drama in naval equator traditions. Amsterdam, Netherlands: Amsterdam University Press. ",""""""),
                    #("Brown, Kevin. 2011. Poxed & scurvied: The story of sickness and health at sea. Barnsley, England: Seaforth Publishing.",""""""),
                    #("Bruzelius, Lars. 1996. 17th century maritime and naval dictionaries. Retrieved from http://www.bruzelius.info/Nautica/Bibliography/Dictionaries_1600.html  ",""""""),
                    #("Bruzelius, Lars. 1999. 19th century maritime and naval dictionaries. Retrieved from http://www.bruzelius.info/Nautica/Bibliography/Dictionaries_1800.html ",""""""),
                    #("Bruzelius, Lars. 2006. 18th century maritime and naval dictionaries. Retrieved from http://www.bruzelius.info/Nautica/Bibliography/Dictionaries_1700.html ",""""""),
                    #("Burg, Barry R. 1995. Sodomy and the pirate tradition: English sea rovers in the seventeenth-century Caribbean. 2nd edn. New York, NY: New York University Press. ",""""""),
                    #("Burg, Barry R. 2001. The buccaneer community. In C. R. Pennell (ed.), Bandits at sea: A pirate reader, 211-243. New York, NY: New York University Press.",""""""),
                    #("Burg, Barry R. 2007. Boys at sea. New York, NY: Palgrave.",""""""),
                    #("Canagarajah, Suresh. 2013. Negotiating translingual literacy: An enactment. Research in the Teaching of English. 48(1), 40–67.",""""""),
                    #("Carlisle, Rodney P. (ed.), 2009. Handbook to life in America: Postwar America 1950 to 1969. New York, NY: Infobase Publishing. ",""""""),
                    #("Cassidy, Frederic G. & Le Page, Robert B. 2002. Dictionary of Jamaican English. Cambridge, England: Cambridge University Press.",""""""),
                    #("Chambers, J. K. & Trudgill, Peter. 1998. Dialectology. Cambridge, England: Cambridge University Press. ",""""""),
                    #("Cheshire, Jenny. 1994. Standardization and the English irregular verbs. In Deiter Stein & Ingrid Tieken-Boon van Ostade (eds.), Towards a Standard English 1600-1800, 115-134. Berlin, Germany: Mouton de Gruyter. ",""""""),
                    #("Choundas, George. 2007. The pirate primer: Mastering the language of swashbucklers and rogues. Georgetown, Canada: Fraser Direct Publications Inc.",""""""),
                    #("Claridge, Claudia & Arnovick, Leslie. 2010. Pragmaticalisation and discursisation. In Andreas H. Jucker & Irma Taavitsainen (eds.), Historical pragmatics, 165-192. Berlin, Germany: Walter de Gruyter GmbH & Co.",""""""),
                    #("Cleirac, Estienne. 1639. Explication des termes de marine employez dans les édicts, ordonnances et reglemens de l’Admirauté … Paris, France: M. Brunet. ",""""""),
                    #("Cook, Bronwen. 2005. ‘A true, faire and just account’: Charles Huggett and the content of Maldon in the English coastal shipping trade 1679-1684. The Journal of Transport History. 26(1), 1-18.",""""""),
                    #("Creighton, Margaret S. & Norling, Lisa. (eds.), 1996. Iron men, wooden women. London, England: John Hopkins University Press. ",""""""),
                    #("Creswell, John W. & Plano Clark, Vicki L. 2007. Designing and conducting mixed methods research. California, CA: Sage Publications.",""""""),
                    #("Daniels, Jason. 2015. Atlantic contingency: Negotiating the uncertainties of the Atlantic marketplace at the turn of the 18th century.  (Paper presented at the conference The Emergence of a Maritime Nation: Britain in the Tudor and Stuart Age, 1485–1714. Greenwich, England, 24-25 July 2015.)",""""""),
                    #("Darvin, Ron. 2016. Language and identity in the digital age. In Sian Preece (ed.), The Routledge handbook of language and identity, 523-540. London, England: Routledge. ",""""""),
                    #("Déclaration des Noms Propres des Piàces de Bois et Autres pièces nécessaires tant à la construction des Navires de Guerre …1657. Paris, France: Chez Louis Boissevin.",""""""),
                    #("de Haas, Nynke. 2006. The origins of the Northern Subject Rule. In Marina Dossena & Richard Dury & Maurizio Gotti (eds.), English historical linguistics, Vol 3., 111-130. Amsterdam, Netherlands: John Benjamins Publishing Company.",""""""),
                    #("Defoe, Daniel. 1719. The life and strange surprising adventures of Robinson Crusoe, of York, mariner: Who lives eight and twenty years all alone in an uninhabited island on the coast of America… London, England: W. Taylor. ",""""""),
                    #("Delgado, Sally J. 2013. Pirate English of the Caribbean and Atlantic trade routes in the seventeenth and eighteenth centuries: Linguistic hypotheses based on socio-historical data. Acta Linguistica Hafniensia: International Journal of Linguistics, 45(2), 151-169.",""""""),
                    #("Delgado, Sally J. 2015. The reconstructed phonology of seventeenth century sailors’ speech. (Paper presented at the Summer meeting of the Society of Pidgin and Creole Linguistics. Graz, Austria, 7-9 July 2015.)   ",""""""),
                    #("Delgado, Sally. J. & Hancock, Ian. 2017. New routes to creolization: The importance of Ship English.  (Paper presented at the Winter meeting of the Society of Pidgin and Creole Linguistics. Austin, Texas, 5-7 January 2017.)   ",""""""),
                    #("Desroches. 1687. Dictionnaire des termes propres de marine. Paris, France: Amable Auroy, Paris.  ",""""""),
                    #("Dobson, E. J. 1955. Early Modern Standard English. Transactions of the Philological Society. 54(1), 25-54.",""""""),
                    #("Draper, Mary. 2016. Forging and maintaining the maritime hinterlands of Barbados and Jamaica. (Paper presented at 48th Annual Association of Caribbean Historians, Havana, 6-10 June 2016. Available from http://www.associationofcaribbeanhistorians.org/conferencepapers2016/index.htm) (Accessed 2016-08-10.)",""""""),
                    #("Durrell, Martin. 2004. Sociolect. In Ulrich Ammon (ed.), Sociolinguistics: An international handbook of the science of language and society, 200-205. Berlin, Germany: Walter de Gruyter.",""""""),
                    #("Earle, Peter. 1993. English sailors 1570-1775, In Paul C. van Royen & J. R. Bruijn & Jan Lucassen (eds.), ‘Those emblems of hell?’ European sailors and the maritime labour market, 1570-1870, 75-95. St. John’s, Newfoundland: International Maritime Economic History Association.",""""""),
                    #("Earle, Peter. 1998. Sailors: English merchant seamen 1650-1775. London, England: Methuen.",""""""),
                    #("Esquemelin, John. 1678. The buccaneers of America: A true account of the most remarkable assaults committed of late years upon the coasts of the West Indies by the buccaneers of Jamaica and Tortuga (both English and French.) New York, NY: Dover Publications. (Reprinted 1967.)",""""""),
                    #("Eyers, Jonathan. 2011. Don’t shoot the albatross!: Nautical myths and superstitions. London, England: A & C Black.",""""""),
                    #("Faraclas, Nicholas & Corum, Micah & Arrindell, Rhoda & Ourdy Pierre, Jean. 2012. Sociétés de cohabitation and the similarities between the English lexifier Creoles of the Atlantic and the Pacific: The case for diffusion from the Afro-Atlantic to the Pacific. In Nicholas Faraclas (ed.), Agency in the emergence of creole languages: The role of women, renegades, and people of African and indigenous descent in the emergence of the colonial era creoles, 149-184. Amsterdam, Netherlands: John Benjamins Publishing Company.",""""""),
                    #("Faraclas, Nicholas & Lozano-Cosme, Jenny & Mejía, Gabriel & Olmeda Rosario, Roberto & Heffelfinger Nieves, Cristal & Cardona Durán, Mayra & Cortes, Mayra & Rodriguez Iglesias, Carlos & Rivera Cornier, Francis S. & Mulero Claudio, Adriana & DeJesús, Susana & Vergne, Aida & Muñoz, John Paul & LE Compte Zambrana, Pier Angeli & Brock, Sarah & Joseph Haynes, Marisol & Angus Baboun, Melissa & Arus, Javier Enrique. 2016. Recovering African agency: A re-analysis of tense, modality and aspect in Statian and other Afro-Caribbean English lexifier contact varieties. (Paper presented at the 21st Biennial Conference of the Society for Caribbean Linguistics. Kingston, Jamaica 1-6 August 2016.)",""""""),
                    #("Fernández de Gamboa, Sebastián. 1696. Vocabulario de los nombres que usan la gente de mar en todo lo que pertenece a su arte. Sevilla, Spain: Imp. de los Hos. de Tomas López de Haro.",""""""),
                    #("Fleischman, Suzanne. 1990. Tense and narrativity: From medieval performance to modern fiction. Austin, TX: University of Texas Press. ",""""""),
                    #("Fox Smith, Cicely. 1924. Sailor Town Days. 2nd edn. London, England: Methuen. ",""""""),
                    #("Fury, Cheryl. 2015. Rocking the boat: Shipboard disturbances in the early voyages of the English East India Company 1601-1611. Unpublished manuscript. Copy shared by the author via personal email Aug 20 2015.",""""""),
                    #("Fusaro, Maria. 2015. Public service and private trade: Northern seamen in seventeenth-century Venetian courts of justice. The International Journal of Maritime History. 27(1), 3-25.",""""""),
                    #("Gage, Thomas. 1648. New Svrvey of the West-Indies, or The English-American, his travail by sea and land… London, England: R. Cotes. Courtesy of The Merseyside Maritime Museum’s digitized holdings, ref 792.1.8 ",""""""),
                    #("Gehweiler, Elke. 2010. Interjection and expletives. In Andreas H. Jucker & Irma Taavitsainen (eds.), Historical pragmatics, 315-349. Berlin, Germany: Walter de Gruyter GmbH & Co.",""""""),
                    #("Gilje, Paul A. 2016. To swear like a sailor: Maritime culture in America 1750-1850. New York, NY: Cambridge University Press.",""""""),
                    #("Givón, Talmy. 2001. Syntax: An introduction, Vol. II.  Amsterdam, Netherlands: John Benjamins Publishing Company.",""""""),
                    #("Görlach, Manfred. 1999. Regional and social variation. In Roger Lass, (ed.), The Cambridge history of the English language, Vol III 1476-1776, 459-538. Cambridge, England: Cambridge University Press.",""""""),
                    #("Hancock, Ian. 1972. A domestic origin for the English-derived Atlantic Creoles. Florida FL Reporter. 10(1), 1-2, 7-8, 52.",""""""),
                    #("Hancock, Ian. 1976. Nautical sources of Krio vocabulary. International Journal of the Sociology of Language. 7, 26-36.",""""""),
                    #("Hancock, Ian. 1986. The domestic hypothesis, diffusion and componentiality: An account of Atlantic Anglophone creole origin. In Pieter Muysken & Norval Smith (eds.), Substrate versus universals in creole genesis, 71-102. Amsterdam, Netherlands: John Benjamins.",""""""),
                    #("Hancock, Ian. 1988. Componentiality and the origins of Gullah. In James L. Peacock & James C. Sabella (eds.), Sea and land: Cultural and biological adaptation in the Southern Coastal Plain, 13-24. Athens, GA: University of Georgia Press.",""""""),
                    #("Hatfield, April. 2016. ‘English pirates’ Illegal slave trading, as described in Spanish sanctuary records. (Paper presented at 48th Annual Association of Caribbean Historians, Havana, 6-10 June 2016. Available from http://www.associationofcaribbeanhistorians.org/conferencepapers2016/index.htm) (Accessed 2016-08-10.)",""""""),
                    #("Hattendorf, John. J. (ed.), 2007. The Oxford encyclopedia of maritime history. Oxford, England: Oxford University Press. ",""""""),
                    #("Hawkins, John A. (1978.) Definiteness and indefiniteness. London, England: Routledge. ",""""""),
                    #("Hendery, Rachel. 2013. Early documents from Palmerston Island and their implications for the origins of Palmerston English. Journal of Pacific History. 48(3), 309–322. ",""""""),
                    #("Hickey, Raymond. (ed.), 2004. Legacies of colonial English: Studies in transported dialects. Cambridge, England: Cambridge University Press.",""""""),
                    #("Hogendorn, Jan & Johnson, Marion. 2003. The shell money of the slave trade. African Study Series 49. Cambridge, England: Cambridge University Press. ",""""""),
                    #("Holm, John. 1978. The Creole English of Nicaragua’s Miskito Coast.  London: University of London. (Doctoral dissertation.) Retrieved from University Microﬁlms International.",""""""),
                    #("Holm, John. 1981. Sociolinguistic history and the creolist. In Arnold R. Highfield, & Albert Valdman (eds.), Historicity and variation in creole studies, 40-51. Ann Arbour, MI: Karoma Publishers.",""""""),
                    #("Holm, John & Watt Schilling, Alison. 1982. Dictionary of Bahamian English. New York, NY: Lexik House Publications.",""""""),
                    #("Holm, John. 1988. Pidgins and creoles I: Theory and structure. Cambridge, England: Cambridge University Press.",""""""),
                    #("Holm, John. 2009. Quantifying superstrate and substrate influence. Journal of Pidgin and Creole Languages. 24(2), 218-274.",""""""),
                    #("Howel, James. 1645-1650. Epistolae ho-elianae familiar letters domestic and forren: divided into sundry sections, partly historicall, politicall, philosophicall. London, England: D. Nutt.",""""""),
                    #("Hughes, Geoffrey. 1991. Swearing: A social history of foul language, oaths and profanity in English. Oxford, England: Blackwell. ",""""""),
                    #("Hugill, Stan. 1969. Shanties and sailors’ songs. London, Englang: Herbert Jenkins. ",""""""),
                    #("Hymes, Dell. (ed.), 1971. Pidginization and creolization of languages. London, England: Cambridge University Press.",""""""),
                    #("Jarvis, Michael J. 2010. In the eye of all trade: Bermuda, Bermudians, and the maritime Atlantic world 1680-1783. Chapel Hill, NC: University of North Carolina Press.",""""""),
                    #("Jeans, Peter. D. 1993. Ship to shore: A dictionary of everyday words and phrases derived from the sea. California: ABC-CLIO, Inc.",""""""),
                    #("Johnson, Charles. 1713. The successful pyrate. A play. As it is acted at the Theatre-Royal in Drury lane, by Her Majesty’s servants. Written by Mr. Cha. Johnson. The second edition.  London, England: Eighteenth Century Collections Online Print Editions. ",""""""),
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
            record = langscibibtex.Record(s)
            self.assertEqual(record.bibstring, expected)
      
      #TODO add more and different entry types of varying complexity
    
        
if __name__ == '__main__':
    unittest.main()