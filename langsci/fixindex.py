# -*- coding: utf-8 -*-
import re
from asciify import ASCIITRANS, FRENCH_REPLACEMENTS, GERMAN_REPLACEMENTS, ICELANDIC_REPLACEMENTS
  
p = re.compile(r"\\indexentry \{(.*)\|(\(?hyperpage|\)|infn)")
   
def setposition(s): 
  if s.strip()=='':
    return s
  m = p.match(s) 
  entry = '' 
  try:
    entry = m.groups(1)[0]
  except AttributeError:
    print("could not analyze", repr(s))
    return s
  translatedentry = entry.translate(ASCIITRANS)  
  for r in FRENCH_REPLACEMENTS+GERMAN_REPLACEMENTS+ICELANDIC_REPLACEMENTS:
    translatedentry = translatedentry.replace(*r)
  if translatedentry == entry:
    return s
  else:
    return s.replace(entry,"%s@%s"%(translatedentry,entry))

if __name__ == '__main__':
  infilename = 'main.adx'
  outfilename = 'mainmod.adx'
  lines = open(infilename).readlines()
  print(len(lines))
  linesnew = list(map(setposition, lines))
  out = open(outfilename,'w')
  out.write(''.join(linesnew))
  out.close()
  