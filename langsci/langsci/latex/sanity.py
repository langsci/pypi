"""
Check files of various types for conformity to Language Science Press guidelines.
Currently the following file types are checked:

* tex files from folder chapters/
* bib files 
* png/jpg files in forlder figures/

"""

import re
import glob
import fnmatch
import textwrap
import uuid
import unicodedata
import hashlib

from PIL import Image


class SanityError:
    """A record of a potentially problematic passage

    Attributes:
      filename (str): the path to the file where the error is found
      linenr (int): the number of the line where the error is found
      line (str): the full line under consideration
      offendingstring (str): the string which was identified as problematic
      msg (str): information on why this string was found problematic
      pre (str): left context of the offending string
      post (str): right context of the offending string
      ID (str): ID to uniquely refer to a given error in HTML-DOM
      name (str): hexadecimal string used for colour coding based on msg
      color (str): a rgb color string
      bordercolor (str): a rgb color string, which is darker than color
    """

    def __init__(self, filename, linenr, line, offendingstring, msg):
        self.filename = filename.split("/")[-1]
        self.linenr = linenr
        self.line = line
        self.offendingstring = offendingstring
        self.msg = msg
        self.pre = self.line.split(self.offendingstring)[0]
        try:
            self.post = self.line.split(self.offendingstring)[1]
        except IndexError:
            self.post = ""
        self.ID = uuid.uuid1()
        hash_input = msg
        if hash_input.startswith("uncommon character"):
            hash_input = "uncommon character"
        self.name = str(int(hashlib.md5(str.encode(hash_input)).hexdigest(), 16))[-9:]

    def get_colors(self):
        """
        compute rgb colors from msg
        """
        t = textwrap.wrap(self.name, 3)[-3:]
        red = int(t[0]) % 140 + 115
        green = int(t[1]) % 140 + 115
        blue = int(t[2]) % 140 + 115
        color = f"rgb({red},{green},{blue})"
        border_red = red - 15
        border_green = green - 15
        border_blue = blue - 15
        bordercolor = f"rgb({border_red},{border_green},{border_blue})"
        return color, bordercolor

    def __str__(self):
        return "{linenr}: …{offendingstring}… \t{msg}".format(**self.__dict__)


class SanityFile:
    """A file with information about potentially problematic passages

    Attributes:
      filename (str): the path to the file
      content (str): the content of the file
      lines ([]str): the lines of the file
      errors ([]SanityError): the list of found errors

    """

    antipatterns = ()
    posnegpatterns = ()

    def __init__(self, filename):
        def get_name(key):
            try:
                return unicodedata.name(key)
            except ValueError:
                return "Low ASCII Control Character"

        self.filename = filename
        self.errors = []
        try:
            with open(filename, encoding="utf-8") as content:
                self.content = content.read()
        except UnicodeDecodeError:
            print(f"file {filename} is not in proper Unicode encoding")
            self.content = ""
            self.errors = [
                SanityError(
                    filename, 0, " ", " ", "file not in Unicode, no analysis possible"
                )
            ]
        self.lines =  self._removecomments(self.content).split("\n")
        # get a list of all characters outside of low ASCII range, together with their Unicode name
        self.uncommon_characters = sorted(
            [
                (k, get_name(k))
                for k in set(self.content)
                if ord(k) > 255 and k not in "‘’“…−–—””"
            ]
        )

    def _removecomments(self, s):
        """strip comments from file so that errors are not marked in comments"""

        # negative lookbehind
        try:
            result = re.sub("(?<!\\\\)%.*\n", "\n", s)
        except TypeError:
            print(f"{s} could not be regexed")
            return s
        return result

    def check(self):
        """
        check the file for errors
        """

        for i, line in enumerate(self.lines):
            if "\\chk" in line:  # the line is explicitely marked as being correct
                continue
            for antipattern, msg in self.antipatterns:
                # print(antipattern)
                m = re.search(f"({antipattern})", line)
                if m is not None:
                    g = m.group(1)
                    if g != "":
                        self.errors.append(SanityError(self.filename, i, line, g, msg))
            for positivepattern, negativepattern, msg in self.posnegpatterns:
                posmatch = re.search(f"({positivepattern})", line)
                if posmatch is None:
                    continue
                # a potential incorrect behaviour is found, but could be saved
                # by the presence of additional material
                g = posmatch.group(1)
                negmatch = re.search(negativepattern, line)
                if (
                    negmatch is None
                ):  # the match required to make this line correct is not found
                    self.errors.append(SanityError(self.filename, i, line, g, msg))

        for ch in self.uncommon_characters:
            self.errors.append(
                SanityError(self.filename, 0, "", ch[0], f"uncommon character: {ch[1]}")
            )

    def get_uncommon_chars(self):
        """
        return the list of uncommon characters
        """

        for ch in self.uncommon_characters:
            return f"The following uncommon characters were found:\n{ch[0]}:{ch[1]}"


class TexFile(SanityFile):
    """
    A tex file to be checked

    Attributes:
      antipatterns (str[]): a list of 2-tuples consisting of a string
                            to match and a message to deliver if the string is found
      posnegpatterns (str[]): a list of 3-tuples consisting a pattern to match,
                            a pattern NOT to match, and a message
      filechecks: currently unused #TODO
    """

    antipatterns = (
        (
            r" et al.",
            "Please use the citation commands \\citet and \\citep",
        ),
        (r"setfont", "You should not set fonts explicitely"),  # no font definitions
        (
            r"\\(small|scriptsize|footnotesize)",
            "Please consider whether changing font sizes manually is really a good idea here",
        ),
        (
            r"([Tt]able|[Ff]igure|[Ss]ection|[Pp]art|[Cc]hapter\() *\\ref",
            "It is often advisable to use the more specialized commands \\tabref,\
\\figref, \\sectref, and \\REF for examples",
        ),  # no \ref
        # ("",""),      #\ea\label
        # ("",""),      #\section\label
        (" \\footnote", "Footnotes should not be preceded by a space"),
        # ("",""),      #footnotes end with .
        (
            r"\[[0-9]+,[0-9]+\]",
            "Please use a space after the comma in lists of numbers ",
        ),  # no 12,34 without spacing
        (
            r"\([^)]+\\cite[pt][^)]+\)",
            "In order to avoid double parentheses, it can be a good idea\
 to use \\citealt instead of \\citet or \\citep",
        ),
        ("([0-9]+-[0-9]+)", "Please use -- for ranges instead of -"),
        (r"[0-9]+ *ff", "Do not use ff. Give full page ranges"),
        (r"[^-]---[^-]", "Use -- with spaces rather than ---"),
        (r"tabular.*\|", "Vertical lines in tables should be avoided"),
        (r"\\hline", "Use \\midrule rather than \\hline in tables"),
        (
            r"\\gl[lt] *[a-z].*[\.?!] *\\\\ *$",
            "Complete sentences should be capitalized in examples",
        ),
        (r"\\glt * ``", "Use single quotes for translations."),
        (r"\\section.*[A-Z].*[A-Z].*", "Only capitalize this if it is a proper noun"),
        (
            r"\\s[ubs]+ection.*[A-Z].*[A-Z].*",
            "Only capitalize this if it is a proper noun",
        ),
        (
            r"[ (][12][8901][0-9][0-9][^0-9]",
            "Please check whether this should be part of a bibliographic reference",
        ),
        (
            r"(?<!\\)[A-Z]{3,}",
            "It is often a good idea to use \\textsc{smallcaps} instead of ALLCAPS",
        ),
        (
            r"(?<![0-9])[?!;\.,][A-Z]",
            # negative lookbehind for numbers because of lists of citation keys
            "Please use a space after punctuation (or use smallcaps in abbreviations)",
        ),
        (
            r"\\textsuperscript\{w\}",
            "Please use Unicode ʷ for labialization instead of superscript w",
        ),
        (
            r"\\textsuperscript\{j\}",
            "Please use Unicode ʲ for palatalization instead of superscript j",
        ),
        (
            r"\\textsuperscript\{h\}",
            "Please use Unicode ʰ for aspiration instead of superscript h",
        ),
        (
            r"\\texttipa",
            "Do not use the tipa package. Use Unicode or the package langsci-textipa",
        ),
        (
            r"\\(underline|uline|ul)\{",
            "Please do not use underlining. Consult with support if you really need it",
        ),
        (
            r"""quote}[\s]*['’’'‘’'‘'′ʼ´ʹʻˈʹ՚＇‛"“”]""",
            "Please do not use quotation marks for indented quotes",
        ),
        (
            r"\\begin\{tabular\}[c]\{l\}",
            "Please do not use nested tables. Get in touch with support",
        ),
        (
            r"\\begin\{minipage\}",
            "Please do not use minipages. Get in touch with support",
        ),
        (
            r"\\vspace",
            "Please do not manually adjust vertical spacing.\
            This will be done during final typesetting by the LangSci office",
        ),
        (
            r"\\hspace",
            "Please do not manually adjust horizontal spacing.\
            This will be done during final typesetting by the LangSci office",
        ),
        (
            r"\\(newpage|pagebreak|clearpage|FloatBarrier)",
            "Please do not manually adjust page breaks.\
            This will be done during final typesetting by the LangSci office",
        ),
        (
            r"{table}\[[hH!]+\]",
            "All table positioning will be done during final typesetting. [h] and [H] will be removed then. There is no way to make sure that this table will be positioned exactly here."
        ),
        (
            r"{figure}\[[hH!]+\]",
            "All figure positioning will be done during final typesetting. [h] and [H] will be removed then. There is no way to make sure that this figure will be positioned exactly here."
        ),
        (
            r"\[hbtp\]",
            "[hbtp] is meaningless. It is entered by some automatic conversion programs and can be removed"
        ),
        (
            r"\[htbp\]",
            "[htbp] is meaningless. It is entered by some automatic conversion programs and can be removed"
        ),
        (
            r"\\centering",
            "Floats are automatically centered in LangSci books, so this command is probably redundant"
        ),
    )

    posnegpatterns = (
        (
            r"\[sub]*section\{",
            r"\label",
            "All sections should have a \\label. This is not necessary for subexamples.",
        ),
        # (r"\\ea.*",r"\label","All examples should have a \\label"),
        (
            r"\\gll\W+[A-Z]",
            r"[\.?!][ }]*\\\\ *$",
            "All vernacular sentences should end with punctuation",
        ),
        (
            r"\\glt\W+[A-Z]",
            r"[\.?!][}\\]*['’”ʼ]",
            "All translated sentences should end with punctuation",
        ),
    )

    filechecks = (
        # ("",""),    #src matches #imt
        # ("",""),     #words
        # ("",""),     #hyphens
        # ("",""),    #tabulars have lsptoprule
        # ("",""),    #US/UK
    )


# year not in order in multicite


class BibFile(SanityFile):
    """
    A bib file to be checked

    Attributes:
      antipatterns (str[]): a list of 2-tuples consisting of a string to
                        match and a message to deliver if the string is found
    """

    antipatterns = (
        (
            "[Aa]ddress *=.*[,/].*[^ ]",
            "No more than one place of publication.\
 No indications of countries or provinces",
        ),
        ("[Aa]ddress *=.* and .*", "No more than one place of publication."),
        (
            "[Tt]itle * =.*: +(?<!{)[a-zA-Z]+",
            "Subtitles should be capitalized. In order to protect the capital\
 letter, enclose it in braces {} ",
        ),
        (
            r"[Aa]uthor *=.*(?<=(and|AND|..[,{])) *[A-Z]\..*",
            "Full author names should be given. Only use abbreviated names if\
 the author is known to prefer this. It is OK to use middle initials",
        ),
        (
            r"[Ee]ditor *=.*(?<=(and|AND|..[,{])) *[A-Z]\..*",
            "Full editor names should be given. Only use abbreviated names if\
 the editor is known to prefer this. It is OK to use middle initials",
        ),
        (
            "[Aa]uthor *=.* et al",
            "Do not use et al. in the bib file. Give a full list of authors",
        ),
        ("[Aa]uthor *=.*&.*", "Use 'and' rather than & in the bib file"),
        (
            r"[Tt]itle *=(.* )?[IVXLCDM]*[IVX]+[IVXLCDM]*[\.,\) ]",
            "In order to keep the Roman numbers in capitals, enclose them in\
 braces {}",
        ),
        (r"\.[A-Z]", "Please use a space after a period or an abbreviated name"),
    )

    posnegpatterns = []


class ImgFile():
    """
    An image file to be checked
    """

    def __init__(self, filename):
        self.filename = filename
        self.errors = []
        self.spellerrors = []
        self.latexterms = []

    def check(self):
        """
        retrieve the resolution of the image and output an error
        message if it is too low
        """

        try:
            with Image.open(self.filename) as img:
                pass
        except IOError:
            print("could not open", self.filename)
            return
        try:
            x, y = img.info["dpi"]
            if x < 72 or y < 72:
                print("low res for", self.filename.split)
                self.errors.append(
                    SanityError(
                        self.filename,
                        "",
                        "",
                        "low resolution",
                        f"{x}x{y}dpi, required 300",
                    )
                )
        except KeyError:
            x, y = img.size
            if x < 1500:
                estimatedresolution = x / 5
                print(
                    f"resolution of {self.filename.split('/')[-1]} when \
printed full with: {estimatedresolution}. Required: 300"
                )
                self.errors.append(
                    SanityError(
                        self.filename,
                        "low resolution",
                        " ",
                        " ",
                        f"estimated {estimatedresolution}dpi, required 300",
                    )
                )


class SanityDir:
    """
    A directory with various files to be checked
    """

    def __init__(self, dirname, ignorecodes):
        self.dirname = dirname
        self.ignorecodes = ignorecodes
        self.texfiles = self.findallfiles("tex")
        self.bibfiles = self.findallfiles("bib")
        self.imgfiles = self.findallfiles("png") + self.findallfiles("jpg")
        self.texterrors = {}
        self.imgerrors = {}

    def findallfiles(self, extension):
        """
        find all files in or below the current directory with a given extension

        args:
          extension (str):  the extension to be looked for

        returns:
          a list of paths for the retrieved filescd -
        """

        matches = []
        localfiles = glob.glob(f"{self.dirname}/local*") + glob.glob(
            f"{self.dirname}/main.tex"
        )
        chapterfiles = glob.glob(f"{self.dirname}/chapters/*tex")
        imgfiles = glob.glob(f"{self.dirname}/figures/*")
        for filename in fnmatch.filter(
            localfiles + chapterfiles + imgfiles, f"*.{extension}"
        ):
            matches.append(filename)
        print(matches)
        return sorted(matches)

    def printErrors(self):
        """
        Print all identified possible errors with metadata (filename, line number, reason
        """
        for filename in sorted(self.texterrors):
            fileerrors = self.texterrors[filename]
            print(
                f"""
{70 * '='}
{filename}, {len(fileerrors)}possible errors found.
Suppressing {len(self.ignorecodes)} error codes: {','.join(self.ignorecodes)}
{70 * '='}"""
            )
            for e in fileerrors:
                if e.name not in self.ignorecodes:
                    print("    ", e.name, e)
        for filename, fileerrors in self.imgerrors.items():
            for e in fileerrors:
                print(filename)
                print("    ", e)

    def check(self):
        """
        Check all files in the directory
        """

        for tfilename in self.texfiles:
            try:
                t = TexFile(tfilename)
            except AttributeError:
                print(tfilename)
                continue
            t.check()
            self.texterrors[tfilename] = t.errors
        for bfilename in self.bibfiles:
            b = BibFile(bfilename)
            b.check()
            self.texterrors[bfilename] = b.errors
        for ifilename in self.imgfiles:
            imgf = ImgFile(ifilename)
            imgf.check()
            self.imgerrors[ifilename] = imgf.errors
