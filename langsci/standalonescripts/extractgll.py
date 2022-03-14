import glob
import sys
import re
import sre_constants
import pprint
import json
import operator
import os
from collections import defaultdict

glottonames = json.loads(open('glottonames.json').read())


#from rdflib import Namespace, Graph, Literal, RDF, RDFS  # , URIRef, BNode
#from . import lod

#GLL = re.compile(
    #r"\\gll[ \t]*(.*?) *?\\\\\\\\\n[ \t]*(.*?) *?\\\\\\\\\n+[ \t]*\\\\glt[ \t\n]*(.*?)\n"
#)
PRESOURCELINE = r"(\\langinfo{(.*?)?}.*\\\\ *\n)?"
SOURCELINE = r"\\gll[ \t]*(.*?) *?\\\\\n"
IMTLINE = r"[ \t]*(.*?) *?\\\\\n+" #some authors add multiple newlines before the translation
TRSLINE = r"\\glt[ \t\n]*(.*?)\n"

#GLL = re.compile(
    #r"\\gll[ \t]*(.*?) *?\\\\\n[ \t]*(.*?) *?\\\\\n+[ \t]*\\glt[ \t\n]*(.*?)\n"
#)
GLL = re.compile(PRESOURCELINE+SOURCELINE+IMTLINE+TRSLINE)
TEXTEXT = re.compile(r"\\text(.*?)\{(.*?)\}")

TEXSTYLEENVIRONMENT =  re.compile(r"\\\\textstyle[A-Z][A-Za-z].*?{(.*?)}")
INDEXCOMMANDS =  re.compile(r"\\\\i[sl]{(.*?)}")
LABELCOMMANDS =  re.compile(r"\\\\label{(.*?)}")
CITATION = re.compile(r"\\cite[altpv]*(\[.*?\])?\{(.*?)\}")

STARTINGQUOTE = "`‘"
ENDINGQUOTE = "'’"
TEXREPLACEMENTS = [
    (r"\_", "_"),
    (r"\texttimes", "×"),
    (r"\textquotesingle", "'"),
    (r"\textquotedbl", '"'),
    (r"\textprimstress", "ˈ"),
    (r"\textbackslash", r"\\"),
    (r"\textbar", "|"),
    (r"\textasciitilde", "~"),
    (r"\textless", "<"),
    (r"\textgreater", ">"),
    (r"\textrightarrow", "→"),
    (r"\textalpha", "α"),
    (r"\textbeta", "β"),
    (r"\textgamma", "γ"),
    (r"\textdelta", "δ"),
    (r"\textepsilon", "ε"),
    (r"\textphi", "φ"),
    (r"\textupsilon", "υ"),
    (r"\newline", " "),
    (r"{\ꞌ}", "ꞌ"),
    (r"{\ob}", "["),
    (r"{\cb}", "]"),
    (r"{\db}", " "),
    (r"\nobreakdash", ""),
    (r"\textendash", "-")
]


class gll:
    def __init__(self, presource, lg, src, imt, trs, filename=None, booklanguage=None):
        self.presource = presource
        self.src = src
        self.imt = imt
        if booklanguage:
            self.language_iso6393 = booklanguage[0]
            self.language_glottocode = booklanguage[1]
            self.language_name = booklanguage[2]
        else:
            self.language_iso6393 = None
            self.language_name = None
            self.language_glottocode = glottonames.get(lg, ["und", None])[0]
            if self.language_glottocode != "und":
                self.language_name = lg
        self.trs = trs.replace("\\\\"," ").strip()
        if self.trs[0] in STARTINGQUOTE:
            self.trs = self.trs[1:]
        if self.trs[-1] in ENDINGQUOTE:
            self.trs = self.trs[:-1]
        self.trs = self.striptex(self.trs)
        self.srcwordstex = self.src.split()
        self.imtwordstex = self.imt.split()
        self.citation = None
        match = CITATION.search(presource) or CITATION.search(trs)
        if match:
            self.citation = match.group(2)
        #try:
        assert len(self.srcwordstex) == len(self.imtwordstex)
        #except AssertionError:
        #pass
        #print(len(self.srcwordstex), len(self.imtwordstex))
        #print(self.srcwordstex, self.imtwordstex)
        self.categories = self.tex2categories(imt)
        #self.srcwordshtml = [self.tex2html(w) for w in self.srcwordstex]
        #self.imtwordshtml = [self.tex2html(w) for w in self.imtwordstex]
        imt_html = '\n'.join(['\t<div class="imtblock">\n\t\t<div class="srcblock">' + self.tex2html(t[0]) + '</div>\n\t\t<div class="glossblock">' + self.tex2html(t[1]) + '</div>\n\t</div>'
                    for t
                    in zip(self.srcwordstex, self.imtwordstex)
                    ])
        self.html = f'<div class="imtblocks">\n{imt_html}\n</div>\n'
        self.srcwordsbare = [self.striptex(w) for w in self.srcwordstex]
        self.imtwordsbare = [self.striptex(w, sc2upper=True) for w in self.imtwordstex]
        self.clength = len(self.src)
        self.wlength = len(self.srcwordsbare)
        self.ID = "%s-%s" % (
            filename.replace(".tex", "").split("/")[-1],
            str(hash(self.src))[:6],
        )
        self.bookID = filename.split('/')[-2]
        self.analyze()

    def tex2html(self, s):
        result = re.sub(TEXTEXT, '<span class="\\1">\\2</span>', s)
        for r in TEXREPLACEMENTS:
            result = result.replace(*r)
        return result

    def striptex(self, s, sc2upper=False):
        if sc2upper:
            for m in re.findall("\\\\textsc{(.*?)}",  s):
                s = s.replace("\\textsc{%s}" % m , m.upper())
        result = re.sub(TEXTEXT, "\\2", s)

        result = re.sub(INDEXCOMMANDS, "", result)
        result = re.sub(LABELCOMMANDS, "", result)
        result = re.sub(TEXSTYLEENVIRONMENT,r"\1", result)

        for r in TEXREPLACEMENTS:
            result = result.replace(*r)
        return result

    def tex2categories(self, s):
        d = {}
        scs = re.findall("\\\\textsc\{(.*?)\}", s)
        for sc in scs:
            cats = re.split("[-=.:]", sc)
            for cat in cats:
                d[cat] = True
        return sorted(list(d.keys()))

    def json(self):
        print(json.dumps(self.__dict__, sort_keys=True, indent=4))

    def __str__(self):
        return "%s\n%s\n%s\n" % (self.srcwordshtml, self.imtwordshtml, self.trs)

    def analyze(self):
        if " and " in self.trs:
            self.coordination = "and"
        if " or " in self.trs:
            self.coordination = "or"
        if " yesterday " in self.trs.lower():
            self.time = "past"
        if " tomorrow " in self.trs.lower():
            self.time = "future"
        if " now " in self.trs.lower():
            self.time = "present"
        if " want" in self.trs.lower():
            self.modality = "volitive"
        if " not " in self.trs.lower():
            self.polarity = "negative"

langsci_d = {17: ('sje', "pite1240","Pite Saami"), # pite1240
             66: ('ybh', "yakk1236", "Yakkha"),#yakk1236
             67: ('mhl', "mauw1238","Mauwake"),# mauw1238
             78: ('pmy', "papu1250","Papuan Malay"),# papu1250
             82: ('phl', "phal1254","Palula"),# phal1254
             85: ('fpe', "fern1234","Pichi"),  #fern1234 (Pichi)
             118: ('mlw',"molo1266", "Moloko"),# Molo1266
             124: ('rap',"rapa1244", "Rapa Nui"), #  rapa1244
             212: ('tci',"wara1294", "Komnzo"), # wara1294 (Komnzo)
             250: ('dar', "sanz1248", "Sanzhi Dargwa"), #sanz1248          (Iso is not precise here)
             }

def langsciextract(directory):

    books = glob.glob(f"{directory}/*")
    for book in books:
        book_ID = int(book.split("/")[-1])
        booklanguage = langsci_d.get(int(book_ID), False)
        glossesd = defaultdict(int)
        excludechars = ".\\}{=~:/"
        files = glob.glob(f"{directory}/{book_ID}/chapters/*tex")
        files = glob.glob(f"{directory}/{book_ID}/*tex")
        print(" found %i tex files for %s" % (len(files), book_ID))
        for filename in files:
            try:
                s = open(filename).read()
            except UnicodeDecodeError:
                print("Unicode problem in %s"% filename)
            examples = []
            glls = GLL.findall(s)
            #print(filename, end=": ")
            #print(f"  {len(glls)}")
            for g in glls:
                try:
                    thisgll = gll(*g, filename=filename, booklanguage=booklanguage)
                except AssertionError:
                    continue
                examples.append(thisgll)
                #example_block_ID = f"{book_lod_ID}_{thisgll.ID}"
                #sentence_word_tier_lod_ID = f"{example_block_ID}_wt"
                #sentence_morph_tier_lod_ID = f"{example_block_ID}_mt"
                wordstring =  " ".join(thisgll.srcwordsbare)
                glossstring =  " ".join(thisgll.imtwordsbare)
                example_block_nif_label = wordstring
                words_nif_label =  wordstring
                gloss_language_id = "eng"
                vernacular_language_id = booklanguage
                words = thisgll.srcwordsbare
                wordglosses = thisgll.imtwordsbare

                for i in range(len(words)):
                    word = words[i]
                    #word_id = f"{sentence_word_tier_lod_ID}_{i}"
                    wordgloss = wordglosses[i]
                    try:
                        wordgloss = wordgloss.strip()
                    except TypeError:
                        wordgloss = ""
                    #add items to tier
                    morphs = re.split("[-=]", word)
                    morphglosses = re.split("[-=]", wordgloss)
                    try:
                        assert len(morphs) == len(morphglosses)
                    except AssertionError:
                        #print(len(morphs), len(morphglosses), morphs, morphglosses)
                        continue

                    for j in range(len(morphs)):
                        morph = morphs[j]
                        #morph_id = f"{sentence_morph_tier_lod_ID}_{i}_{j}"
                        morphgloss = morphglosses[j]
                        for subgloss in re.split("[-=.:]", morphgloss):
                            subgloss = (
                                subgloss.replace("1", "")
                                .replace("2", "")
                                .replace("3", "")
                            )

                #count root occurrences (could probably go to separte module
                for imtgloss in thisgll.imtwordsbare:
                    for imtmorph in re.split("[-=]", imtgloss):
                        if  imtmorph.isupper():
                            continue
                        glossesd[imtmorph] += 1

            if examples != []:
                jsons = json.dumps([ex.__dict__ for ex in examples], sort_keys=True, indent=4, ensure_ascii=False)
                jsonname = 'langscijson/%sexamples.json'%filename[:-4].replace('/','-').replace('eldpy-langscitex--','').replace('-chapters', '')
                #print(filename)
                print("   ", jsonname)
                with open(jsonname, 'w', encoding='utf8') as jsonout:
                    jsonout.write(jsons)

if __name__ == "__main__" :
    langsciextract(sys.argv[1])
