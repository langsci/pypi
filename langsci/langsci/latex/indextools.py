"""
Adapt an index generated by XeLaTeX so that it sorts words containing diacritics correctly

The ways how the *dx files are generated varies between different versions of TexLive
"""

import re, sys
import shutil

from .delatex import dediacriticize
from .asciify import asciify

# the LaTeX index entries consist of the string to be displayed (after the "@")
# and the string used for sorting (before the "@").
p = re.compile(r"\\indexentry \{(.*)\|(\)|\(?hyper)")
#                                   pipe, followed by either a ")" or by "(hyper" or only "hyper"

ignoredic = {}


def processline(s):
    global ignoredic
    """Conform the input string to the index requirements and return the conformed string

  To conform the string, first LaTex diacritics like {\'{e}} are removed. Then, Unicode
  is translated to ASCII

  Args:
    s (str): the input string

  Returns:
    str:  the output string

  Example:
    >>> print(processline("\v{C}{\'{e}}pl\"o, Slavomír")
    Ceplo, Slavomir
  """

    if s.strip() == "":
        return s
    # find the substring used for sorting
    m = p.match(s)
    try:
        items = p.match(s).group(1).split("@")
        sortstring = items[0]
        has_at = False
        if len(items) > 1:
            has_at = True
    except AttributeError:
        print("%s could not be parsed" % repr(s))
        return ""
    processedstring = asciify(dediacriticize(sortstring))
    if sortstring == processedstring:
        return s
    else:
        if sortstring not in ignoredic:
            print("%s => %s" % (sortstring, processedstring))
            ignoredic[sortstring] = True
        if has_at:
            result = s.replace("%s@" % sortstring, "%s@" % processedstring)
            return result
        else:
            result = s.replace(sortstring, "%s@%s" % (processedstring, sortstring))
            return result


def processfile(filename):
    """Read a file and write the fixed output to another file with "mod" appended to its name

    Args:
      filename (str): the path to the file

    Returns:
      None

    """
    print("Reading", filename)
    with open(filename, encoding="utf-8") as indexfile:
        lines = indexfile.readlines()
    print("Found %i lines" % len(lines))
    # read all lines, process them and write them to output file
    processedlines = list(map(processline, lines))
    shutil.copy(filename, f"{filename}.bak")
    with open(filename, "w", encoding="utf-8") as out:
        out.write("".join(processedlines))
