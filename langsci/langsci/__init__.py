name = "langsci"

from .asciify import (FRENCH_REPLACEMENTS, GERMAN_REPLACEMENTS,
                      ICELANDIC_REPLACEMENTS, ASCIITRANS,
                      asciify, is_ascii)

from .bibnouns import (LANGUAGENAMES, OCEANNAMES, COUNTRIES, CONTINENTNAMES,
                       CITIES, OCCURREDREPLACEMENTS)

from .bibtools import (keys, excludefields, FIELDS, Record, normalize)

from .delatex import dediacriticize

__all__ = [
            #asciify
           'FRENCH_REPLACEMENTS', 'GERMAN_REPLACEMENTS', 'ICELANDIC_REPLACEMENTS', 'ASCIITRANS',
           'asciify', 'is_ascii',
            #bibnouns
            'LANGUAGENAMES', 'OCEANNAMES', 'COUNTRIES', 'CONTINENTNAMES',
            'CITIES', 'OCCURREDREPLACEMENTS',
            # bibtools
            'keys, excludefields, FIELDS, Record, normalize',
            # delatex
            'dediacriticize'
            
           #'asciify', 'assignproofreaders', 'autoindex', 'bibnouns',
           #'delatex', 'doc2tex', 'extractaw','fixindex','langscibibtex','normalizebib','sanitycheck','sanitygit','zenodo'
           ]
           
 
