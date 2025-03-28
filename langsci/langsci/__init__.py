name = "langsci"

from .latex.asciify import (
    FRENCH_REPLACEMENTS,
    GERMAN_REPLACEMENTS,
    ICELANDIC_REPLACEMENTS,
    ASCIITRANS,
    asciify,
    is_ascii,
)

from .latex.delatex import dediacriticize

from .bib.bibnouns import (
    LANGUAGENAMES,
    OCEANNAMES,
    COUNTRIES,
    CONTINENTNAMES,
    CITIES,
    OCCURREDREPLACEMENTS,
)

from .bib.bibtools import keys, excludefields, FIELDS, Record, normalize


__all__ = [
    # asciify
    "FRENCH_REPLACEMENTS",
    "GERMAN_REPLACEMENTS",
    "ICELANDIC_REPLACEMENTS",
    "ASCIITRANS",
    "asciify",
    "is_ascii",
    # bibnouns
    "LANGUAGENAMES",
    "OCEANNAMES",
    "COUNTRIES",
    "CONTINENTNAMES",
    "CITIES",
    "OCCURREDREPLACEMENTS",
    # bibtools
    "keys, excludefields, FIELDS, Record, normalize",
    # delatex
    "dediacriticize"
    #'asciify', 'assignproofreaders', 'autoindex', 'bibnouns',
    #'delatex', 'doc2tex', 'extractaw','fixindex','langscibibtex','normalizebib','sanitycheck','sanitygit','zenodo'
]
