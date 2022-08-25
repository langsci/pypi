"""
Find occurrences of terms listed in *txt files and add indexing markup in corresponding *tex files
"""

import glob
import re
import os
import sys
import concurrent.futures

IGNORECASE = False

def process_file(filename):
    print("indexing %s" % filename)
    #strip preamble of edited volume chapters to avoid indexing there
    parts  =  open(filename).read().split(r"\begin{document}")
    content  =  parts[-1]
    preamble  =  ''
    joiner  =  ''
    if len(parts)  ==  2:
        #prepare material to correctly reassemble the file after indexing
        preamble  =  parts[0]
        joiner  =  r"\begin{document}"
    oldlines  =  content.split('\n')
    newlines  =  []
    for line in oldlines:
        included  =  True
        for excluder in excluders:
            if "%s{"%excluder in line:
                included  =  False
                print("Found excluder keyword %s:%s"%(excluder, line))
        if included:
            for lg in lgs:
                lg  =  lg.strip()
                if lg  ==  '':
                    continue
                #substitute "lg" with "\ili{lg}"
                line  =  re.sub('(?<!ili{)%s(?![\w}])'%lg, r'\\ili{%s}'%lg, line)
            for term in terms:
                term  =  term.strip()
                if term  ==  '':
                    continue
                #substitute "term" with "\isi{term}"
                if IGNORECASE:
                    line  =  re.sub('(?<!isi{|...[A-Za-z])(%s)(?![-_\w}])'%term, r'\\isi{\1}', line, flags=re.IGNORECASE)
                else:
                    line  =  re.sub('(?<!isi{|...[A-Za-z])(%s)(?![-_\w}])'%term, r'\\isi{\1}', line)

        newlines.append(line)
    #reassemble body
    content  =  "\n".join(newlines)
    #compute stats
    numberoflanguages  =  len(re.findall(r'\\ili{',content))
    numberofterms  =  len(re.findall(r'\\isi{',content))
    #make sure directory indexed/ exists
    try:
        os.mkdir('./indexed')
    except OSError:
        pass
    outfile  =  open(filename.replace('chapters','indexed'), 'w')

    #write output
    outfile.write(preamble)
    outfile.write(joiner)
    outfile.write(content)
    outfile.close()

    #print stats
    print(" %s now contains %i indexed languages and %i indexed subject terms"%(filename.split('/')[-1],numberoflanguages,numberofterms))



if __name__  ==  "__main__":
    #no indexing will take place in lines with the following keywords and {. section also matches subsection.
    excluders  =  ("section","caption","chapter","addplot","subfigure","node")
    
    lgs = open("locallanguages.txt").read().split('\n')
    for lg in lgs:
            if "(" in lg:
                print(f"{lg} contains parentheses. Parentheses are not allowed in indexed language names. Exiting.")
                sys.exit()
    terms = open("localsubjectterms.txt").read().split('\n')[::-1]#reverse to avoid double indexing
    for term in terms:
            if "(" in term:
                print(f"{term} contains parentheses. Parentheses are not allowed in indexed language names. Exiting.")
                sys.exit()
    print("found %i language names for autoindexing" % len(lgs))
    print("found %i subject terms for autoindexing" % len(terms))

    files  =  glob.glob('chapters/*tex')

    for f in files:
        process_file(f)
    #multithreading code below. More threads make the indexing slower rather than faster
    #with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        #executor.map(process_file, files)
    print("indexed files are in the folder 'indexed/'")
