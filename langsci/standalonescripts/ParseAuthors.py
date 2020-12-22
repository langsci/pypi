#!/usr/bin/python

import sys
import os.path
import shutil
import requests
import re
import json
import pandas


startid = int(sys.argv[1])
endid = int(sys.argv[2])
masterurl1 = 'https://raw.githubusercontent.com/langsci/'
masterurl2 = '/master/'
langscigiturl = 'https://github.com/langsci/'
owd = os.getcwd()
warnings = []



def append_authors_old(line):
    authors_dict = {}
    line = line[line.find('\\author')+8:line.rfind('}')]
    line = re.sub(r'\\orcid{.*}','',line)
    authors_dict[line[:line.find("\\affiliation")]] = line[line.find("\\affiliation")+13:line.find("}")]
    while "\\and" in line:
        line = line[line.find("\\and")+5:]
        authors_dict[line[:line.find("\\affiliation")]] = line[line.find("\\affiliation")+13:line.find("}")]
    while "\\lastand" in line:
        line = line[line.find("\\lastand")+9:]
        authors_dict[line[:line.find("\\affiliation")]] = line[line.find("\\affiliation")+13:line.find("}")]
    return(authors_dict)

def append_bookauthors(line):
    line = line[line.find('\\author')+8:line.rfind('}')]
    authors_list = (re.split("\\\\and\s|\\\\lastand", line))
    return(authors_list)

# work in progress. probably doesn't work yet
def append_authors(line):
    line = line[line.find('\\author')+8:line.rfind('}')]
    line = re.sub(r'\\orcid{.*}','',line)
    authors_list = (re.split("\\\\and\s|\\\\lastand", line))
    authors_temp = []
    for item in authors_list:
        if "\\affiliation" in item:
            splititem = (re.split("\\\\affiliation{", item))
            newitem = {"name" : splititem[0], "affiliation":re.sub('}', '', splititem[1])}
            authors_temp.append(newitem)
    if authors_temp:
        authors_list = authors_temp[:]
    return(authors_list)



def create_database(id):
    metadata_dict = {"bookid": id}
    chapternames = []
    chapterdict_list = []
    print("Reading metadata for book number %s"% (str(id)))
    mainmetadata = requests.get('%s%s%slocalmetadata.tex' % (masterurl1, str(id), masterurl2)).text
    print("Reading main.tex for book number %s"%(str(id)))
    mainfile = requests.get('%s%s%smain.tex' % (masterurl1, str(id), masterurl2)).text
    for line in mainmetadata.splitlines():
        if "ISBNdigital" in line and not "%" in line[0: line.find("ISBNdigital")]:
            ISBNdigital = line[line.rfind('{')+1:line.rfind('}')]
            metadata_dict["ISBNdigital"] = ISBNdigital
        elif "ISBNhardcover" in line and not "%" in line[0: line.find("ISBNhardcover")]:
            ISBNhardcover = line[line.rfind('{')+1:line.rfind('}')]
            metadata_dict["ISBNhardcover"] = ISBNhardcover
        elif "ISBNsoftcover" in line and not "%" in line[0: line.find("ISBNsoftcover")]:
            ISBNsoftcover = line[line.rfind('{')+1:line.rfind('}')]
            metadata_dict["ISBNsoftcover"] = ISBNsoftcover
        elif "\\title" in line and not "%" in line[0: line.find("\\title")]:
            line = re.sub(r'{\\newlineCover*}','',line)
            booktitle = line[line.rfind('{')+1:line.rfind('}')]
            metadata_dict["booktitle"] = booktitle
        elif "\\author" in line and not "%" in line[0: line.find("\\author")]:
             metadata_dict["bookauthor"] = append_bookauthors(line)
    for line in mainfile.splitlines():
        if "\\include{chapters/" in line and not "%" in line[0: line.find("\\include")]:
            chapternames.append(line[line.find('\\include{chapters/')+18:line.find('}')])
        elif "\\includepaper{" in line and not "%" in line[0: line.find("\\include")]:
             chapternames.append(line[line.find('\\includepaper{chapters')+23:line.find('}')])
    for chaptername in chapternames:
        chapterdict = {"chapterfilename":chaptername}
        chapterauthor= {}
        chapterauthors_list = []
        chapterfile = requests.get('%s%s%schapters/%s.tex' % (masterurl1, str(id), masterurl2, chaptername)).text
        print("Reading chapter %s" % chaptername)
        for line in chapterfile.splitlines():
            if "\\chapter" in line and not "%" in line[0: line.find("chapter")]:
                chaptertitle = (line[line.find('\\chapter{')+9:line.find('}')])
                chapterdict["chaptername"] = chaptertitle
            elif "\\title" in line and not "%" in line[0: line.find("chapter")]:
                line = re.sub(r'{\\newlineCover*}','',line)
                line = re.sub(r'\\newlineCover*','',line)
                chaptertitle = (line[line.find('\\title{')+7:line.find('}')])
                chapterdict["chaptername"] = chaptertitle
            elif "\\author" in line and not "%" in line[0: line.find("chapter")]:
                chapterdict["authors"] = append_authors(line)

        chapterdict_list.append(chapterdict)

        #basic logging:
        if "\\{" in chapterdict:
            logfile.write("WARNING: \\{ detected in chapter %s. This will likely break the parsing of that line.")
            print("WARNING: \\{ detected in chapter %s. This will likely break the parsing of that line.")
    metadata_dict["chapter"] = chapterdict_list
    return(metadata_dict)

def make_jsons(id):
    print("Dumping JSON file for Book %s" % str(id))
    with open("%s.json" % str(id), "w") as outputfile:
        json.dump(create_database(id), outputfile, indent=4)
    outputfile.close()

  
  
def full_table(startid,endid):
    for id in range(startid,endid+1):
        print("Processing book %s" % str(id))
        if os.path.exists("%s.log" % str(id)):
            os.remove("%s.log" % str(id))
        print("Logging in %s.log" % str(id))
        logfile = open("%s.log" % str(id), "a")
        make_jsons(id)
        logfile.close()

def chapterauthors_table(startid,endid):
        for id in range(startid,endid+1):
            print("Processing book %s" % str(id))
            if os.path.exists("%s.log" % str(id)):
                os.remove("%s.log")
            print("Logging in %s.log" % str(id))
            logfile = open("%s.log" % str(id), "a")
            


full_table(startid,endid)
