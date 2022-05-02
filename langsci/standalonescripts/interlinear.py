#import glob
#import sys
import re
#import sre_constants
#import pprint
import json
#import operator
import os
import LaTexAccents
import hashlib

from collections import defaultdict
from titlemapping import titlemapping
from named_entities import get_entities, get_parent_entities
#from lgrlist import LGRLIST

from imtvaultconstants import *
from langsci.webglottolog import string2glottocode, glottocode2iso
converter = LaTexAccents.AccentConverter()

try:
    glottonames = json.loads(open("glottonames.json").read())
except FileNotFoundError:
    glottonames = {}

#try:
    #glotto_iso6393 = json.loads(open("glottoiso.json").read())
#except FileNotFoundError:
    #glotto_iso6393 = {}

glottotmp = {}

class gll:
    def __init__(
        self,
        presource,
        lg,
        src,
        imt,
        trs,
        filename=None,
        book_language=None,
        book_metalanguage="eng",
        abbrkey=None,
        glottolog=False,
        analyze=False,
        extract_entities=False,
        parent_entities=False,
        nercache = {}
    ):
        basename = filename.split("/")[-1]
        self.license = "https://creativecommons.org/licenses/by/4.0"
        self.book_ID = int(filename.split("/")[-2])
        self.book_URL = f"https://langsci-press.org/catalog/book/{self.book_ID}"
        self.book_title = titlemapping.get(self.book_ID)
        self.book_metalanguage = book_metalanguage
        self.abbrkey = abbrkey
        self.categories = self.tex2categories(imt)
        srcwordstex = self.strip_tex_comment(src).split()
        imtwordstex = [self.resolve_lgr(i) for i in self.strip_tex_comment(imt).split()]
        assert len(srcwordstex) == len(imtwordstex)
        imt_html = "\n".join(
            [
                '\t<div class="imtblock">\n\t\t<div class="srcblock">'
                + self.tex2html(t[0])
                + '</div>\n\t\t<div class="glossblock">'
                + self.tex2html(t[1])
                + "</div>\n\t</div>"
                for t in zip(srcwordstex, imtwordstex)
            ]
        )
        self.html = f'<div class="imtblocks">\n{imt_html}\n</div>\n'
        self.srcwordsbare = [self.striptex(w) for w in srcwordstex]
        self.ID = "%s-%s" % (
            basename.replace(".tex", "").split("/")[-1],
            hashlib.sha256(" ".join(self.srcwordsbare).encode("utf-8")).hexdigest()[
                :10
            ],
        )
        self.imtwordsbare = [self.striptex(w, sc2upper=True) for w in imtwordstex]
        self.clength = len(src)
        self.wlength = len(self.srcwordsbare)

        self.citation = None
        match = CITATION.search(presource) or CITATION.search(trs)
        if match:
            self.citation = match.group(2)

        self.trs = trs.replace("\\\\", " ").strip()
        try:
            if self.trs[0] in STARTINGQUOTE:
                self.trs = self.trs[1:]
            if self.trs[-1] in ENDINGQUOTE:
                self.trs = self.trs[:-1]
            self.trs = self.strip_tex_comment(self.trs)
            self.trs = self.striptex(self.trs)
            self.trs = self.trs.replace("()", "")
        except IndexError:  # s is  ''
            pass
        m = CITATION.search(self.trs)
        if m is not None:
            if m.group(2) != "":
                self.trs = (
                    re.sub(CITATION, r"(\2: \1)", self.trs)
                    .replace("[", "")
                    .replace("]", "")
                )
            else:
                self.trs = re.sub(CITATION, r"(\2)", self.trs)

        if book_language:
            self.language_iso6393 = book_language[0]
            self.language_glottocode = book_language[1]
            self.language_name = book_language[2]
        elif glottolog:
            self.language_iso6393 = None
            self.language_name = None
            if lg not in ("", None):
                self.language_name = lg
                try:
                    self.language_glottocode = glottonames[lg]
                    glottonames[lg] = self.language_glottocode
                    self.language_iso6393 = glottocode2iso(self.language_glottocode)
                except KeyError:
                    if glottotmp.get(lg):
                        self.language_glottocode = None
                    else:
                        glottocode = string2glottocode(lg)
                        if glottocode is None:
                            #we have no information but might get some in the future
                            pass
                        elif glottocode is False:
                            #we have positive information that we cannot resolve this
                            glottotmp[lg] = False
                        else:
                            self.language_glottocode = glottocode
        if analyze:
            self.analyze()
        self.entities = None
        if extract_entities:
            self.entities = get_entities(self.trs,cache=True)
        if parent_entities:
            self.parent_entities = get_parent_entities(self.entities)


    def strip_tex_comment(self, s):
        return re.split(r"(?<!\\)%", s)[0].replace(r"\%", "%")

    def resolve_lgr(self, s):
        s = re.sub(LGRPATTERN_UPPER, r"\1", s)
        for m in LGRPATTERN_LOWER.findall(s):
            g = m[0]
            s = re.sub(r"\\%s(?![a-zA-Z])" % g, g.upper(), s)
        for m in LGRPATTERN_UPPER_LOWER.findall(s):
            g = m[0]
            s = re.sub(r"\\%s(?![a-zA-Z])" % g, g.upper(), s)
        return s

    def tex2html(self, s):
        result = self.striptex(s, html=True)
        # repeated for nested  \textsomething{\textsomethingelse{}}
        result = TEXTEXT.sub('<span class="\\1">\\2</span>', result)
        result = TEXTEXT.sub('<span class="\\1">\\2</span>', result)
        result = TEXTEXT.sub('<span class="\\1">\\2</span>', result)
        return result

    def striptex(self, s, sc2upper=False, html=False):
        result = converter.decode_Tex_Accents(s, utf8_or_ascii=1)
        if sc2upper:
            for m in re.findall("\\\\textsc{([-\.:=<> a-zA-Z0-9]*?)}", result):
                result = result.replace("\\textsc{%s}" % m, m.upper())
        result = re.sub(INDEXCOMMANDS, "", result)
        result = re.sub(LABELCOMMANDS, "", result)
        result = re.sub(TEXSTYLEENVIRONMENT, r"\1", result)
        for r in TEXREPLACEMENTS:
            result = result.replace(*r)
        for r in TEXTARGYANKS:
            result = re.sub(r"\\%s{.*?}" % r, "", result)
        result = re.sub(r"\footnote{[^}{]*}", "", result)
        # add " " in front of string so that lookbehind matches if at beginning of line
        result = re.sub(BRACESPATTERN, r"\1", " " + result)[1:]
        # strip "\ " (latex protected space)
        result = re.sub(r"(?<!\\)\\ ", " ", result)
        if html:  # keep \textbf, \texit for the time being, to be included in <span>s
            return result
        else:
            #repeat  for nested  \textsomething{\textsomethingelse{}}
            result = re.sub(TEXTEXT, "\\2", result)
            result = re.sub(TEXTEXT, "\\2", result)
            result = re.sub(BRACESPATTERN, r"\1", " " + result)[1:]
            return re.sub(TEXTEXT, "\\2", result)

    def tex2categories(self, s):
        d = {}
        smallcaps = re.findall("\\\\textsc\{([-=.:a-zA-Z0-9)(/\[\]]*?)\}", s)
        for sc in smallcaps:
            cats = re.split("[-=.:0-9)(/\[\]]", sc)
            for cat in cats:
                d[cat] = True
        return sorted(list(d.keys()))

    #def json(self):
        #print(json.dumps(self.__dict__, sort_keys=True, indent=4))

    #def __str__(self):
        #return "%s\n%s\n%s\n" % (self.srcwordshtml, self.imtwordshtml, self.trs)

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
