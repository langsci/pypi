import glob
import sys
import re
import sre_constants
import pprint
import json
import operator
import os
import LaTexAccents as TeX
import requests
import hashlib

from bs4 import BeautifulSoup
from collections import defaultdict
from titlemapping import titlemapping
from lgrlist import LGRLIST


converter = TeX.AccentConverter()


glottonames = json.loads(open('glottonames.json').read())
glottotmp = {}
glotto_iso6393 = {}

NON_CCBY_LIST = [148, 149, 234]


#from rdflib import Namespace, Graph, Literal, RDF, RDFS  # , URIRef, BNode
#from . import lod

#GLL = re.compile(
    #r"\\gll[ \t]*(.*?) *?\\\\\\\\\n[ \t]*(.*?) *?\\\\\\\\\n+[ \t]*\\\\glt[ \t\n]*(.*?)\n"
#)
PRESOURCELINE = r"(?P<presourceline>\\(ili|langinfo){(?P<language_name>.*?)?}.*\\\\ *\n)?"
SOURCELINE = r"\\gll[ \t]*(?P<sourceline>.*?) *?\\\\\n"
IMTLINE1 = r"[ \t]*(?P<imtline1>.*?) *?\\\\\n+" #some authors add multiple newlines before the translation
IMTLINE2 = r"([ \t]*(?P<imtline2>.*?) *?\\\\\n+)?" #some authors add multiple newlines before the translation
TRSLINE = r"[ \t]*\\(glt|trans)[ \t\n]*(?P<translationline>.*?)\n"
LGRPATTERN_UPPER = re.compile(r"\\(%s)({})?" % "|".join(LGRLIST))
LGRPATTERN_LOWER = re.compile(r"(%s)({})?" % "|".join([s.lower() for s in LGRLIST]))
LGRPATTERN_UPPER_LOWER = re.compile(r"(%s)({})?" % "|".join([s[0]+s[1:].lower() for s in LGRLIST]))
BRACESPATTERN = re.compile(r"(?<=.^| ){([^}{ ]+)}")
    #r"\\gll[ \t]*(.*?) *?\\\\\n[ \t]*(.*?) *?\\\\\n+[ \t]*\\glt[ \t\n]*(.*?)\n"
#)
#GLL = re.compile(PRESOURCELINE+SOURCELINE+IMTLINE+TRSLINE)
GLL = re.compile(PRESOURCELINE+SOURCELINE+IMTLINE1+IMTLINE2+TRSLINE)
#GLL = re.compile(PRESOURCELINE+SOURCELINE+IMTLINE1+TRSLINE)
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
    (r"\textendash", "-"),
    (r"\footnotesize", "-"),
    (r"\footnotemark", "-"),
    (r"\langle", "<"),
    (r"\rangle", ">"),
    (r"\ldots", "..."),
    (r"\dots", "..."),
    (r"\MakeLowercase", ""),
    (r"\nopagebreak", ""),
    (r"\pagebreak", ""),
    (r"\sout", r"\textstrikeout"),
    (r"\uline", r"\textunderline"),
    (r"\underline", r"\textunderline"),
    (r"\emph", r"\textemph"),
    (r"\textup", ""),
    (r"\url", ""),
    (r"\chapref", "Chapter "),
    (r"\sectref", "Section "),
    (r"\figure", "Figure "),
    (r"\tabref", "Table "),
    (r"\appref", "Appendix "),
    (r"\fnref", "Footnote "),
    (r"\ref", ""),
    (r"\forall", "∀"),
    (r"\exists", "∃"),
    (r"\xspace", ""),
    (r"\bluebold", r"\textbf"),
    (r"\blueboldSmallCaps", r"\textsc"),
    (r"\tsc", r"\textsc"),
    (r"\ili", ""),
    (r"\isi", ""),
    (r"\sc", r"\scshape"),
    (r"\it ", r"\itshape "),
    (r"\bf ", r"\bfseries "),
    (r"\lq", '"'),
    (r"\{", '{'),
    (r"\}", '}'),
    (r"\label", ''),
    (r"\hfill", ' '),
    (r"\vfill", ' '),
    (r"\sqt", ' '),
    (r"\fbox", ' '),
    (r"\spacebr", ''),
    (r"\ule", ''),
    (r"\ulp", ''),
    (r"\oldstylenums", ''),
    (r"\normalfont", ''),
    (r"\NORMALFONT", ''),
    (r"\longrightarrow", '→'),
    (r"\leftrightarrow", '⇔'),
    (r"\emptyset", 'ø'),
    (r"\varnothing", 'ø'),
    (r"\USEmptySet", 'ø'),
    (r"\Tilde", '~'),
    (r"\NORMALFONT", ''),
    (r"\relax", ''),
    (r"\raisebox", ''),
    (r"\quotetrans", ''),
    (r"\qquad", ''),
    (r"\quad", ''),
    (r"\nobreakdash", ''),
    (r"\NOBREAKDASH", ''),
    (r"\newpage", ''),
    (r"\mytrans", '\glt'),
    (r"\minsp", ''),
    (r"\makebox", ''),
    (r"\longrule", '__'),
    (r"\MakeUpperCase", ''),
    (r"\MakeUppercase", ''),
    (r"\linebreak", ''),
    (r"\linewidth", ''),
    (r"\interfootnotelinepenalty", ''),
    (r"\hskip", ''),
    (r"\deff", '\def'),
    (r"\smash", ''),
    (r"\enquote", ''),
    (r"\Emph", ''),
    (r"\sim", '~'),
    (r"\USgreater", '>'),
    (r"\USsmaller", '<'),
    (r"\slash", '/'),
    (r"\OLDSTYLENUMS", '/'),
    (r"\thirdperson", '3'),
    (r"\textglotstop", 'ʔ'),
    (r"\beltl", 'ł'),
    (r"\textltailn", 'ɲ'),
    (r"\textopeno", 'ɔ'),
    (r"\textstrikeout", ''),
    (r"\textunderscore", ''),
    (r"\textstyleEmphasizedVernacularWords", '\emph'),
    (r"\protect", ''),
    (r"\\", ' '),
    (r"\citealt", ''),
    (r"\Highlight", r'\textbf'),
    (r"\sg", r'SG'),
    (r"\rouge", r'\textred'),
    (r"\bleu", r'\textblue'),
    (r"\mbox", r''),
    (r"\ddagger", r'‡'),
    (r"\dagger", r'†'),
    (r"\downstep", r'ꜜ'),
    (r"\emph", r'\textemph'),
    (r"\kern2pt", r''),
    (r"\,", r' '),
    (r"\Rightarrow", r'→'),
    (r"\rm", r""),
    (r"\#", r"#"),
    (r"\Third", r"3"),
    (r"\super", r"\textsuperscript"),
    (r"\expo", r"\textsuperscript"),
    (r"\small", r"\textsmall"),
    (r"\footnotesize", r"\textsmall"),
    (r"\scriptsize", r"\textsmall"),
    (r"\tiny", r"\textsmall"),
    (r"\USGreater", r">"),
    (r"\USSmaller", r"<"),
    (r"\exi", r" "),
    (r"\textitshape", r"\textit"),
    (r"\upshape", r""),
    (r"\@", r"@"),
    (r'\"=', r"-"),
    (r'{\scshape', r"\textsc{"),
    (r'\gsc', r"\textsc"),
    (r'\glemph', r"\textemph"),
    (r"\O", 'ø'),
    (r"{\R}", 'REALIS'),
    (r"\circ", '°'),
    (r"\stem", ''),
    (r"\z", ''),
    (r"\ex ", ' '),
    (r"\ix{", r'\textsubscript{'),
    (r"\textsmallskip", r''),
    (r"\smallskip", r''),
    (r"\medskip", r''),
    (r"\bigskip", r''),
    (r"\extrans", r'\glt '),
    (r"\trad", r'\glt '),
    (r"\op", r'('),
    (r"\cp", r')'),
    (r"\ob", r'['),
    (r"\cb", r']'),
    (r"\db", r' '),
    (r"\llap", r''),
    (r"\textemdash", r'—'),
    (r"\Corpus", r''),
    (r"\flobv{}", r"→3'"),
    (r"\mc{", r"\textsc{"),
    (r"\tkal", r"XaYaZ"),
    (r"\tpie", r"XiY̯eZ"),
    (r"\tpua", r"XuY̯aZ"),
    (r"\mpua", r"meXuY̯aZ"),
    (r"\thif", r"heXYiZ"),
    (r"\thuf", r"huXYaZ"),
    (r"\mhuf", r"muXYaZ"),
    (r"\thit", r"hitXaY̯eZ"),
    (r"\tnif", r"niXYaZ"),
    (r"\gloss{", r"\textsc{"),
    (r"{\LINK}", r"LINK"),
    (r"\mas{}", r"M"),
    (r"\ipa{}", r""),
    (r"\tss", r"\textsubscript"),
    (r"\tsp", r"\textsuperscript"),
    (r"\Tsg{}", r"3.SG"),
    (r"\Tpl{}", r"3.PL"),
    (r"\oneS", r"1.SG"),
    (r"\twoS", r"2.SG"),
    (r"\prs{}", r"PRS"),
    (r"\tld", r"~"),
    (r"\itshape", r"\textit{"),
    (r"\scshape", r"\textsc{"),
    (r"\bf", r"\bfseries"),
    (r"\bfseries", r"\textbf{"),
    (r"\nom", r"NOM"),
    (r"\acc", r"ACC"),
    (r"{\pl}", r"PL"),
    (r"{\pst}", r"PST"),
    (r"{\prs}", r"PRS"),
    (r"\lptcp", r"l-PTCP"),
#greekletters
]

#remove these together with their argument
TEXTARGYANKS = ["ConnectHead", "ConnectTail", "hphantom", "japhdoi", "phantom", "vspace", "vspace\*", "begin", "end", "is", "il", "hspaceThis", "hspace", "hspace\*", "ilt", "ist"]

def get_iso(glottocode):
    global glotto_iso6393
    if glottocode == None:
        return "und"
    try:
        return glotto_iso6393[glottocode]
    except KeyError:
        request_url = f"https://glottolog.org/resource/languoid/id/{glottocode}"
        html = requests.get(request_url).text
        soup = BeautifulSoup(html, 'html.parser')
        try:
            iso = soup.find('span', class_="iso639-3").a['title']
        except AttributeError:
            return "und"
        glotto_iso6393[glottocode] = iso
        print(glottocode, iso)
        return iso



class gll:
    def __init__(self, presource, lg, src, imt, trs, filename=None, booklanguage=None, book_metalanguage="eng", abbrkey=None):
        #self.presource = presource
        #print(presource, lg, src, imt, trs)
        basename = filename.split('/')[-1]
        self.license = "https://creativecommons.org/licenses/by/4.0"
        self.book_ID = int(filename.split('/')[-2])
        self.book_URL =  f"https://langsci-press.org/catalog/book/{self.book_ID}"
        self.book_title = titlemapping.get(self.book_ID)
        if booklanguage:
            self.language_iso6393 = booklanguage[0]
            self.language_glottocode = booklanguage[1]
            self.language_name = booklanguage[2]
        else:
            self.language_iso6393 = None
            self.language_name = None
            if lg not in ('', None):
                self.language_name = lg
                try:
                    self.language_glottocode = glottonames[lg][0]
                    glottonames[lg] = [self.language_glottocode,None]
                    self.language_iso6393 = get_iso(self.language_glottocode)
                except KeyError:
                    if glottotmp.get(lg):
                        self.language_glottocode = None
                    else:
                        request_url = f"https://glottolog.org/glottolog?name={lg}&namequerytype=part"
                        print(lg, request_url)
                        html = requests.get(request_url).text
                        soup = BeautifulSoup(html, 'html.parser')
                        languoids = soup.find_all('a', class_="Language")
                        if len(languoids) == 3: #exactly one languoid
                            self.language_glottocode = languoids[0]["title"] #FIXME add ISO
                            self.language_family = languoids[2]["title"]
                            self.language_name = lg
                            print(" "+self.language_glottocode)
                            glottonames[lg] = [self.language_glottocode, None]
                        elif len(languoids) == 0: #no languoids. We store this in persistent storage
                            print(len(languoids))
                            glottonames[lg] = [None , None]
                        else: #more than one languoid. We store this only temporarily and hope for future improvements in the code.
                            print(len(languoids))
                            languoids2 = soup.find_all('td', class_="level-language")
                            print(len(languoids2))
                            if len(languoids2) == 1:
                                self.language_glottocode = languoids2[0].find("a", class_="Language")["href"].split('/')[-1]
                                self.language_name = lg
                                glottonames[lg] = [self.language_glottocode, None]
                                print(" "+self.language_glottocode)
                                #self.language_family = FIXME
                            else:
                                self.language_glottocode = None
                                glottotmp[lg] = True
        self.book_metalanguage = book_metalanguage
        self.abbrkey = abbrkey
        self.trs = trs.replace("\\\\"," ").strip()
        try:
            if self.trs[0] in STARTINGQUOTE:
                self.trs = self.trs[1:]
            if self.trs[-1] in ENDINGQUOTE:
                self.trs = self.trs[:-1]
            self.trs = self.strip_tex_comment(self.trs)
            self.trs = self.striptex(self.trs)
            self.trs = self.trs.replace("()", "")
        except IndexError: #s is  ''
            pass
        m = CITATION.search(self.trs)
        if m is not None:
            if m.group(2) != '':
                self.trs = re.sub(CITATION, r'(\2: \1)', self.trs).replace('[', '').replace(']', '')
            else:
                self.trs = re.sub(CITATION, r'(\2)', self.trs)
        srcwordstex = self.strip_tex_comment(src).split()
        imtwordstex = [self.resolve_lgr(i) for i in self.strip_tex_comment(imt).split()]
        self.citation = None
        match = CITATION.search(presource) or CITATION.search(trs)
        if match:
            self.citation = match.group(2)
        #try:
        assert len(srcwordstex) == len(imtwordstex)
        self.categories = self.tex2categories(imt)
        imt_html = '\n'.join(['\t<div class="imtblock">\n\t\t<div class="srcblock">' + self.tex2html(t[0]) + '</div>\n\t\t<div class="glossblock">' + self.tex2html(t[1]) + '</div>\n\t</div>'
                    for t
                    in zip(srcwordstex, imtwordstex)
                    ])
        self.html = f'<div class="imtblocks">\n{imt_html}\n</div>\n'
        self.srcwordsbare = [self.striptex(w) for w in srcwordstex]
        self.ID = "%s-%s" % (
            basename.replace(".tex", "").split("/")[-1],
            hashlib.sha256(" ".join(self.srcwordsbare).encode('utf-8')).hexdigest()[:10]
        )
        self.imtwordsbare = [self.striptex(w, sc2upper=True) for w in imtwordstex]
        self.clength = len(src)
        self.wlength = len(self.srcwordsbare)
        self.analyze()

    def strip_tex_comment(self, s):
        return re.split(r"(?<!\\)%", s)[0].replace(r"\%","%")

    def resolve_lgr(self, s):
        s = re.sub(LGRPATTERN_UPPER, r"\1", s)
        for m in LGRPATTERN_LOWER.findall(s):
            g = m[0]
            s = re.sub(r"\\%s(?![a-zA-Z])"%g, g.upper(), s)
        for m in LGRPATTERN_UPPER_LOWER.findall(s):
            g = m[0]
            s = re.sub(r"\\%s(?![a-zA-Z])"%g, g.upper(), s)
        return s




    def tex2html(self, s):
        result = self.striptex(s, html=True)
        result = TEXTEXT.sub('<span class="\\1">\\2</span>', result)
        result = TEXTEXT.sub('<span class="\\1">\\2</span>', result)
        result = TEXTEXT.sub('<span class="\\1">\\2</span>', result)#for nested  \textsomething{\textsomethingelse{}}
        return result

    def striptex(self, s, sc2upper=False, html=False):
        result = converter.decode_Tex_Accents(s, utf8_or_ascii=1)
        if sc2upper:
            for m in re.findall("\\\\textsc{([-\.:=<> a-zA-Z0-9]*?)}",  result):
                result = result.replace("\\textsc{%s}" % m , m.upper())
        result = re.sub(INDEXCOMMANDS, "", result)
        result = re.sub(LABELCOMMANDS, "", result)
        result = re.sub(TEXSTYLEENVIRONMENT,r"\1", result)
        for r in TEXREPLACEMENTS:
            result = result.replace(*r)
        for r in TEXTARGYANKS:
            result = re.sub(r"\\%s{.*?}"%r, '', result)
        result = re.sub(BRACESPATTERN, r"\1", " "+result)[1:]  #add " " in front of string so that lookbehind matches if at beginning of line
        result = re.sub(r"(?<!\\)\\ ", " ", result) #strip "\ " (latex protected space)
        if html: #keep \textbf, \texit for the time being, to be included in <span>s
            return result
        else:
            result =  re.sub(TEXTEXT, "\\2", result)
            result =  re.sub(TEXTEXT, "\\2", result)
            result = re.sub(BRACESPATTERN, r"\1", " "+result)[1:]
            return  re.sub(TEXTEXT, "\\2", result)#for nested  \textsomething{\textsomethingelse{}}

    def tex2categories(self, s):
        d = {}
        scs = re.findall("\\\\textsc\{([a-zA-Z]*?)\}", s)
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

langsci_d = {17: ('sje', "pite1240","Pite Saami"),
             66: ('ybh', "yakk1236", "Yakkha"),
             67: ('mhl', "mauw1238","Mauwake"),
             78: ('pmy', "papu1250","Papuan Malay"),
             82: ('phl', "phal1254","Palula"),
             85: ('fpe', "fern1234","Pichi"),
             118: ('mlw',"molo1266", "Moloko"),
             124: ('rap',"rapa1244", "Rapa Nui"),
             212: ('tci',"wara1294", "Komnzo"),
             250: ('dar', "sanz1248", "Sanzhi Dargwa"), #      (Iso is not precise here)
             298: ('gyi', "gyel1242", "Gyeli"),
             295: ('jya', "japh1234", "Japhug"),            # (Iso is not precise here)
             308: ('roh', "surs1245", "Tuatschin"),          # (Iso is not precise here)
             245: ('dga', "sout2789", "Dagaare"),
             98: ('ikx', "ikkk1242", "Ik"),
             326: ('ruc', "ruul1235", "Ruruuli"),
             287: ('nyy', "nyak1261", "Nyakyusa"),
             109: ('nru', "yong1288", "Yongning Na"),
             225: ('dar', "mege1234", "Mehweb"),
             228: ('aaz', "amar1273", "Amarasi"),
             150: ('rus', "russ1263", "Russian"),
             329: ('swe', "swed1254", "Swedish"),
             16: ('ita', "ital1282", "Italian"),
             }

def get_abbreviations(lines):
    result = {}
    for line in lines:
        if line.strip().startswith("%"):
            continue
        cells = line.split("&")
        if len(cells) == 2:
            abbreviation = gll.resolve_lgr(None, gll.striptex(None,cells[0]).strip())
            if abbreviation ==  "...":
                continue
            expansion = gll.striptex(None,cells[1]).replace(r"\\", "").strip().replace(r"\citep", "")
            result[abbreviation] = expansion
    return result



def langsciextract(directory):
    superseded = [22,25,46,141,144,149,195]
    french = [27,143]
    german = [101,234,155,134,116]
    portuguese= [160,200]
    chinese = [177]
    spanish = [236]
    books = glob.glob(f"{directory}/*")
    #books = glob.glob(f"{directory}/16")
    for book in books:
        book_ID = int(book.split("/")[-1])
        if book_ID in superseded:
            continue
        book_metalanguage = "eng"
        if book_ID in portuguese:
            book_metalanguage = "por"
        if book_ID in german:
            book_metalanguage = "deu"
        if book_ID in french:
            book_metalanguage = "fra"
        if book_ID in spanish:
            book_metalanguage = "spa"
        if book_ID in chinese:
            book_metalanguage = "cmn"
        booklanguage = langsci_d.get(int(book_ID), False)
        glossesd = defaultdict(int)
        excludechars = ".\\}{=~:/"
        abbrkey = {}
        try:
            with open(f"{directory}/{book_ID}/abbreviations.tex") as abbrin:
                abbrkey = get_abbreviations(abbrin.readlines())
        except FileNotFoundError:
            pass
        files = glob.glob(f"{directory}/{book_ID}/chapters/*tex")
        files = glob.glob(f"{directory}/{book_ID}/*tex")
        #print(" found %i tex files for %s" % (len(files), book_ID))
        for filename in files:
            try:
                s = open(filename).read()
            except UnicodeDecodeError:
                print("Unicode problem in %s"% filename)
            s = s.replace(r"{\bfseries ", r"\textbf{")
            s = s.replace(r"{\itshape ", r"\textit{")
            s = s.replace(r"{\scshape ", r"\textsc{")
            if abbrkey == {}:
                try:
                    abbr1 = s.split("section*{Abbreviations}")[1]
                    abbr2 = abbr1.split(r"\section")[0]
                    abbrkey = get_abbreviations(abbr2.split("\n"))
                except IndexError:
                    pass
            examples = []
            #glls = GLL.findall(s)
            #gllls = GLLL.findall(s)
            for g in [m.groupdict() for m in GLL.finditer(s)]:
                presource = g['presourceline'] or ''
                lg = g['language_name']
                if g['imtline2'] in (None,''): #standard \gll example¨
                    src = g['sourceline']
                    imt = g['imtline1']
                else:
                    src = g['imtline1'] #we ignore the first line of \glll examples as the second line typically contains the morpheme breaks
                    imt = g['imtline2']
                trs = g['translationline']
                try:
                    thisgll = gll(presource, lg, src, imt, trs, filename=filename, booklanguage=booklanguage, book_metalanguage=book_metalanguage, abbrkey=abbrkey)
                    if thisgll.book_ID in NON_CCBY_LIST:
                        continue
                except AssertionError:
                    continue
                examples.append(thisgll)
            if examples != []:
                jsons = json.dumps([ex.__dict__ for ex in examples], sort_keys=True, indent=4, ensure_ascii=False)
                jsonname = 'langscijson/%sexamples.json'%filename[:-4].replace('/','-').replace('eldpy-langscitex--','').replace('-chapters', '')
                #print(filename)
                print("   ", jsonname)
                with open(jsonname, 'w', encoding='utf8') as jsonout:
                    jsonout.write(jsons)
    with open('glottonames.json', "w") as namesout:
        namesout.write(json.dumps(glottonames, sort_keys=True, indent=4, ensure_ascii=False))
    with open('glottoiso.json', "w") as glottoisoout:
        glottoisoout.write(json.dumps(glotto_iso6393, sort_keys=True, indent=4, ensure_ascii=False))

if __name__ == "__main__" :
    langsciextract(sys.argv[1])
