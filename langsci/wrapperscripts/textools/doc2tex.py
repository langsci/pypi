import sys
import os
import codecs
import re

from langsci.conversion.convertertools import convert

filename = sys.argv[1]
currentworkingdirectory = os.getcwd()
doc = convert(filename, tmpdir=currentworkingdirectory, wd=currentworkingdirectory)

out1 = codecs.open("temporig.tex", "w", "utf-8")
out1.write(doc.text)
out1.close()

out2 = codecs.open("temp.tex", "w", "utf-8")

try:
    out2.write(doc.modtext)
    out2.close()
except UnicodeEncodeError as e:
    # print(repr(doc.modtext[49230:49350]))
    # print("Start:", e.start)
    # print("End:", e.end)
    # m = re.search("position ([0-9])-44819: surrogates", e)
    print(f"Unicode problem in position {e.start}: {repr(doc.modtext[e.start-30:e.start+30])}")
    print("Please fix this in the input file")
    sys.exit()

out3 = codecs.open("chapter.tex", "w", "utf-8")
out3.write(doc.papertext)
out3.close()
