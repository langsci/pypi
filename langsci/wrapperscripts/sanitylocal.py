"""Check files in a local directory for compliance with the guidelines

usage: 
    python3 sanitylocal.py chapters 1234 34523
    The first argument is the folder to be checked. All remaining arguments are codes to be ignored for error reporting, e.g. reporting of hyphens instead of dashes for page ranges could be disabled
"""

import sys


from langsci.latex import sanity

try:
    directory = sys.argv[1]
except IndexError:
    directory = '.'
try:
    ignorecodes = sys.argv[2:]
except IndexError:
    pass
sanitydir = sanity.SanityDir(directory, ignorecodes)
print(
    "checking %s with %i files"
    % (
        directory,
        len(
            sanitydir.texfiles
            + sanitydir.bibfiles
            + sanitydir.imgfiles
        ),
    )
)
sanitydir.check()
sanitydir.printErrors()
# print(sanitydir.get_uncommon_chars())
