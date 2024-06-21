"""
Tools for the conversion of docx/odt into tex
"""

import re
import os
import shutil
import uuid
import codecs
from pathlib import Path
try:
    import bibtools
except ImportError:
    from langsci import bibtools
from converter_helpers import yanks, explicitreplacements

WD = "/home/doc2tex"
WD = "/tmp"
lspskeletond = "/home/doc2tex/skeletonbase"
wwwdir = "/var/www/wlport"

# pylint: disable=anomalous-backslash-in-string,consider-using-f-string
def convert(fn, wd=WD, tmpdir=False):
    """
    Convert a file in docx or odt format to tex
    """

    odtfn = False
    os.chdir(wd)
    if tmpdir is False:
        tmpdir = Path(fn).parent.absolute()
    if fn.endswith("docx"):
        os.chdir(tmpdir)
        syscall = f"""soffice --convert-to odt --outdir "{tmpdir}" "{fn}"   """
        print(syscall)
        os.system(syscall)
        odtfn = fn.replace("docx", "odt")
    elif fn.endswith("doc"):
        os.chdir(tmpdir)
        syscall = f"""soffice --convert-to odt --outdir "{tmpdir}" "{fn}"   """
        os.system(syscall)
        odtfn = fn.replace("doc", "odt")
    elif fn.endswith("odt"):
        odtfn = fn
    else:
        raise ValueError
    if odtfn is False:
        return False
    os.chdir(wd)
    texfn = odtfn.replace("odt", "tex")
    w2loptions = (
        "-clean",
        "-wrap_lines_after=0",
        "-multilingual=false",
        # floats
        "-simple_table_limit=10",
        "-use_supertabular=false",
        "-float_tables=false",
        "-float_figures=false",
        "-use_caption=true",
        '-image_options="width=\\textwidth"',
        # "use_colortbl=true",
        # "original_image_size=true",
        # input
        "-inputencoding=utf8",
        "-use_tipa=false",
        "-use_bibtex=true",
        "-ignore_empty_paragraphs=true",
        "-ignore_double_spaces=false",
        # formatting
        "-formatting=convert_most",
        "-use_color=false",
        "-page_formatting=ignore_all",
        "-use_hyperref=true",
        # "-no_preamble=true"
    )
    syscall = """w2l {} "{}" "{}" """.format(" ".join(w2loptions), odtfn, texfn)
    os.system(syscall)
    with open(texfn, encoding="utf-8") as w2l:
        w2lcontent = w2l.read()
    ipacharcodes = "251 25B 26A 254 28A? 259 268 289".split()
    ipaset = ["\[%s\?\]" % char for char in ipacharcodes]
    IPACHARS = re.compile(f"({'|'.join(ipaset)})")
    found_ipa_chars = set(IPACHARS.findall(w2lcontent))
    warning = ""
    if found_ipa_chars:
        warning = f"% ATTENTION: Diacritics on the following phonetic\
 characters might have been lost during conversion: {found_ipa_chars}\n"
    preamble, text = w2lcontent.split(r"\begin{document}")
    text = warning + text.split(r"\end{document}")[0]
    preamble = preamble.split("\n")
    newcommands = "\n".join(
        [
            l
            for l in preamble
            if l.startswith("\\newcommand")
            and "@" not in l
            and "writerlist" not in l
            and "labellistLi" not in l
            and "textsubscript" not in l
        ]
    )  # or l.startswith('\\renewcommand')])
    # replace all definitions of new environments by {}{}
    newenvironments = "\n".join(
        [
            "%s}{}{}" % l.split("}")[0]
            for l in preamble
            if l.startswith("\\newenvironment") and "listLi" not in l
        ]
    )  # or l.startswith('\\renewcommand')])
    newpackages = "\n".join(
        [
            l
            for l in preamble
            if l.startswith("\\usepackage")
            and "fontenc" not in l
            and "inputenc" not in l
        ]
    )
    newcounters = "\n".join(
        [l for l in preamble if l.startswith("\\newcounter")]
        + ["\\newcounter{itemize}"]
    )
    return Document(newcommands, newenvironments, newpackages, newcounters, text)

class Document:
    """A document which contains the text and all definitions of styles, counters
    and required packages
    """

    def __init__(self, commands, environments, packages, counters, text):
        self.commands = commands
        self.environments = environments
        self.packages = packages
        self.counters = counters
        self.text = text
        self.modtext = self.getModtext()
        paperpreamble = r"""\documentclass[output=paper]{langscibook}
\author{Authorname\orcid{}\affiliation{}}
\title{Title}
\abstract{Abstract}
\IfFileExists{../localcommands.tex}{
  \addbibresource{../localbibliography.bib}
  \input{../localpackages}
  \input{../localcommands} 
  \input{../localhyphenation} 
  \togglepaper[1]%%chapternumber
}{}

\begin{document}
\maketitle 
%\shorttitlerunninghead{}%%use this for an abridged title in the page headers
"""
        paperpostamble = """
\\sloppy\\printbibliography[heading=subbibliography,notkeyword=this]
\\end{document}"""
        self.papertext = paperpreamble + self.modtext + paperpostamble

    def ziptex(self):
        """prepare a zip archive which includes all the necessary files to compile the project"""
        localskeletond = os.path.join(WD, "skeleton")
        try:
            shutil.rmtree(localskeletond)
        except OSError:
            pass
        shutil.copytree(lspskeletond, localskeletond)
        os.chdir(localskeletond)
        try:
            os.mkdir("./chapters")
        except OSError:
            pass
        with codecs.open("localcommands.tex", "a", encoding="utf-8") as localcommands:
            localcommands.write(self.commands)
            localcommands.write(self.environments)
        with codecs.open("localpackages.tex", "a", encoding="utf-8") as localpackages:
            localpackages.write(self.packages)
        with codecs.open("localcounters.tex", "a", encoding="utf-8") as localcounters:
            localcounters.write(self.counters)
        with codecs.open("chapters/filename.tex", "w", encoding="utf-8") as content:
            content.write(self.modtext)
        with codecs.open(
            "chapters/filenameorig.tex", "w", encoding="utf-8"
        ) as contentorig:
            contentorig.write(self.text)
        os.chdir(WD)
        zipfn = str(uuid.uuid4())
        shutil.make_archive(zipfn, "zip", localskeletond)
        shutil.move(zipfn + ".zip", wwwdir)

    def getModtext(self):
        """postprocess the raw output from the w2l converter"""

        modtext = self.text

        for old, new in explicitreplacements:
            modtext = modtext.replace(old, new)

        for y in yanks:
            modtext = modtext.replace(y, "")
        # unescape w2l unicode
        w2lunicodep3 = re.compile(r"(\[[0-9A-Fa-f]{3}\?\])")
        w2lunicodep4 = re.compile(
            r"(\[[0-9A-Da-d][0-9A-Fa-f]{3}\?\])"
        )  # intentionally leaving out PUA
        byteprefix3 = b"\u0" # pylint: disable=anomalous-unicode-escape-in-string
        byteprefix4 = b"\u"  # pylint: disable=anomalous-unicode-escape-in-string
        for m in w2lunicodep3.findall(modtext):
            modtext = modtext.replace(
                m, (byteprefix3 + m[1:-2].encode("utf-8")).decode("unicode_escape")
            )
        for m in w2lunicodep4.findall(modtext):
            modtext = modtext.replace(
                m, (byteprefix4 + m[1:-2].encode("utf-8")).decode("unicode_escape")
            )
        # remove marked up white space and punctuation
        modtext = re.sub("\\text(it|bf|sc)\{([ \.,]*)\}", "\2", modtext)

        # remove explicit table widths
        modtext = re.sub("m\{-?[0-9.]+(in|cm)\}", "X", modtext)
        modtext = re.sub("X\|", "X", modtext)
        modtext = re.sub("\|X", "X", modtext)
        modtext = re.sub(r"\\fontsize\{.*?\}\\selectfont", "", modtext)
        # remove stupid multicolumns and center multicolumns
        modtext = modtext.replace("\\multicolumn{1}{l}{}", "")
        modtext = modtext.replace("\\multicolumn{1}{l}", "")
        modtext = modtext.replace("}{X}{", "}{c}{")
        # remove stupid Open Office styles
        modtext = re.sub(
            "\\\\begin\\{styleLangSciSectioni\\}\n+(.*?)\n+\\\\end\\{styleLangSciSectioni\\}",
            r"\\section{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\\{styleLangSciSectionii\\}\n+(.*?)\n+\\\\end\\{styleLangSciSectionii\\}",
            r"\\subsection{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\\{styleLangSciSectioniii\\}\n+(.*?)\n+\\\\end\\{styleLangSciSectioniii\\}",
            r"\\subsubsection{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\\{styleLangSciSectioniv\\}\n+(.*?)\n+\\\\end\\{styleLangSciSectioniv\\}",
            r"\\subsubsubsection{\1}",
            modtext,
        )

        modtext = re.sub(
            "\\\\begin\\{stylelsSectioni\\}\n+(.*?)\n+\\\\end\\{stylelsSectioni\\}",
            r"\\section{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\\{stylelsSectionii\\}\n+(.*?)\n+\\\\end\\{stylelsSectionii\\}",
            r"\\subsection{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\\{stylelsSectioniii\\}\n+(.*?)\n+\\\\end\\{stylelsSectioniii\\}",
            r"\\subsubsection{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\\{stylelsSectioniv\\}\n+(.*?)\n+\\\\end\\{stylelsSectioniv\\}",
            r"\\subsubsubsection{\1}",
            modtext,
        )

        modtext = re.sub(
            r"\\begin\{styleHeadingi}\n+(.*?)\n+\\end\{styleHeadingi\}",
            r"\\chapter{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\\{styleHeadingii\\}\n+(.*?)\n+\\\\end\\{styleHeadingii\\}",
            r"\\section{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\{styleHeadingiii\}\n+(.*?)\n+\\\\end\{styleHeadingiii}",
            r"\\subsubsection{\1}",
            modtext,
        )
        modtext = re.sub(
            "\\\\begin\{styleHeadingiv\}\n+(.*?)\n+\\\\end\{styleHeadingiv}",
            r"\\subsubsection{\1}",
            modtext,
        )

        # remove explicit shorttitle for sections
        modtext = re.sub(
            "\\\\(sub)*section(\[.*?\])\{(\\text[bfmd][bfmd])\?(.*)\}",
            "\\\1section{\\4}",
            modtext,
        )
        # move explict section number to end of line and comment out
        modtext = re.sub("section\{([0-9\.]+ )(.*)", r"section{\2 %\1/", modtext)
        modtext = re.sub("section\[.*?\]", "section", modtext)
        # table cells in one row
        modtext = re.sub("[\n ]*&[ \n]*", " & ", modtext)
        modtext = modtext.replace(r"\ &", "\&")
        # collapse newlines
        modtext = re.sub("\n*\\\\\\\\\n*", "\\\\\\\\\n", modtext)
        # bib
        authorchars_firstletter = "[A-ZÅÁÉÍÓÚÄËÏÖÜÀÈÌÒÙÂÊÎÔÛŐŰĆĆÇČÐĐŘŚŠŞŌǪØŽ]"
        authorchars_furtherletters = "[-a-záéíóúaèìòùâeîôûäëïöüőűðĺłŁøæœåćĆçÇčČĐđǧñńŘřŚśŠšŞşŽžA-Z]+"
        authorchars = authorchars_firstletter+authorchars_furtherletters
        yearchars = "[12][0-9]{3}[a-z]?"
        modtext = re.sub(
            f"\(({authorchars}) +et al\.?  +({yearchars}): *([0-9,-]+)\)",
            r"\\citep[\3]{\1EtAl\2}",
            modtext,
        )
        modtext = re.sub(
            f"\(({authorchars}) +({yearchars}): *([0-9,-]+)\)",
            r"\\citep[\3]{\1\2}",
            modtext,
        )
        modtext = re.sub(
            f"\(({authorchars}) +et al\.? +({yearchars})\)",
            r"\\citep{\1EtAl\2}",
            modtext,
        )
        modtext = re.sub(
            f"\(({authorchars}) +({yearchars})\)", r"\\citep{\1\2}", modtext
        )
        # citet
        modtext = re.sub(
            f"({authorchars}) +et al.? +\(({yearchars}): *([0-9,-]+)\)",
            r"\\citet[\3]{\1EtAl\2}",
            modtext,
        )
        modtext = re.sub(
            f"({authorchars}) +\(({yearchars}): *([0-9,-]+)\)",
            r"\\citet[\3]{\1\2}",
            modtext,
        )
        modtext = re.sub(
            f"({authorchars}) +et al.? +\(({yearchars})\)",
            r"\\citet{\1EtAl\2}",
            modtext,
        )
        modtext = re.sub(
            f"({authorchars}) +\(({yearchars})\)", r"\\citet{\1\2}", modtext
        )
        # citegen
        modtext = re.sub(
            f"({authorchars}) +et al\.?]['’]s +\(({yearchars})\)",
            r"\\citegen{\1EtAl\2}",
            modtext,
        )
        modtext = re.sub(
            f"({authorchars})['’]s +\(({yearchars})\)",
            r"\\citegen{\1\2}",
            modtext,
        )
        # citeapo
        modtext = re.sub(
            f"({authorchars}) +et al\.?]['’] +\(({yearchars})\)",
            r"\\citeapo{\1EtAl\2}",
            modtext,
        )
        modtext = re.sub(
            f"({authorchars})['’] +\(({yearchars})\)", r"\\citeapo{\1\2}", modtext
        )
        # catch all citealt
        modtext = re.sub(f"({authorchars}) +({yearchars})", r"\\citealt{\1\2}", modtext)
        modtext = re.sub(
            f"({authorchars}) et al\.? +({yearchars})",
            r"\\citealt{\1EtAl\2}",
            modtext,
        )
        # integrate ampersands
        modtext = re.sub(r"(%s) \\& \\citet{" % authorchars, r"\\citet{\1", modtext)
        modtext = re.sub(r"(%s) and \\citet{" % authorchars, r"\\citet{\1", modtext)
        modtext = re.sub(r"(%s) \\& \\citealt{" % authorchars, r"\\citealt{\1", modtext)
        modtext = re.sub(r"(%s) and \\citealt{" % authorchars, r"\\citealt{\1", modtext)
        # Smith (2000, 2001)
        modtext = re.sub(
            rf"({authorchars})\(({yearchars}), *({yearchars})\)",
            r"\\citet{\1\2,\1\3}",
            modtext,
        )
        # Smith 2000, 2001
        modtext = re.sub(
            r"\\citealt{(%s)(%s)}[,;] (%s)" % (authorchars, yearchars, yearchars),
            r"\\citealt{\1\2,\1\3}",
            modtext,
        )
        # condense chains of citations
        modtext = re.sub(
            r"(\\citealt{%s)\}[,;] \\citealt{" % authorchars, "\1,", modtext
        )
        modtext = re.sub(r"(\\citet{%s)\}[,;] \\citealt{" % authorchars, "\1,", modtext)
        # examples
        modtext = modtext.replace(
            "\n()", "\n\\ea \n \\gll \\\\\n   \\\\\n \\glt\n\\z\n\n"
        )
        # only up to number (1999)
        modtext = re.sub(
            "\n\((1?[0-9]?[0-9]?[0-9])\)",
            r"""\n\\ea%\1
    \\label{ex:key:\1}
    \\gll \\\\
         \\\\
    \\glt
    \\z

        """,
            modtext,
        )
        modtext = re.sub(
            r"\\label\{(bkm:Ref[0-9]+)\}\(\)",
            r"""ea%\1
    \\label{\1}
    \\\\gll \\\\newline
        \\\\newline
    \\\\glt
    \\z

    """,
            modtext,
        )

        # subexamples
        modtext = modtext.replace("\n *a. ", "\n% \\ea\n%\\gll \n%    \n%\\glt \n")
        modtext = modtext.replace(
            "\n *b. ", "%\\ex\n%\\gll \\\\\n%    \\\\\n%\\glt \n%\\z\n"
        )
        modtext = modtext.replace(
            "\n *c. ", "%\\ex\n%\\gll \\\\\n%    \\\\\n%\\glt \n%\\z\n"
        )
        modtext = modtext.replace(
            "\n *d. ", "%\\ex\n%\\gll \\\\\n%    \\\\\n%\\glt \n%\\z\n"
        )
        modtext = modtext.replace(r"\newline", r"\\")

        modtext = re.sub(
            "\n\\\\textit{Table ([0-9]+)[\.:] *(.*?)}\n",
            r"%%please move \\begin{table} just above \\\\begin{tabular . \n\
\\begin{table}\n\\caption{\2}\n\\label{tab:key:\1}\n\\end{table}",
            modtext,
        )
        modtext = re.sub(
            "\nTable ([0-9]+)[\.:] *(.*?) *\n",
            r"%%please move \\begin{table} just above \\begin{tabular\n\\begin{table}\n\
\\caption{\2}\n\\label{tab:key:\1}\n\\end{table}",
            modtext,
        )  # do not add } after tabular
        modtext = re.sub("Table ([0-9]+)", "\\\\tabref{tab:key:\\1}", modtext)
        modtext = re.sub(
            "\nFigure ([0-9]+)[\.:] *(.*?)\n",
            r"\\begin{figure}\n\\caption{\2}\n\\label{fig:key:\1}\n\\end{figure}",
            modtext,
        )
        modtext = re.sub("Figure ([0-9]+)", "\\\\figref{fig:key:\\1}", modtext)
        modtext = re.sub("Section ([0-9\.]*[0-9])", "\\\\sectref{sec:key:\\1}", modtext)
        modtext = re.sub("§ *([0-9\.]*[0-9])", "\\\\sectref{sec:key:\\1}", modtext)
        modtext = re.sub(
            " \(([0-9][0-9]?[0-9]?[a-h]?)\)", " \\\\REF{ex:key:\\1}", modtext
        )
        modtext = re.sub("\\\\(begin|end){minipage}.*?\n", "", modtext)
        modtext = re.sub("\\\\begin{figure}\[h\]", "\\\\begin{figure}", modtext)

        modtext = re.sub(
            "(begin\{tabular\}[^\n]*)",
            r"""\1\n
\\lsptoprule""",
            modtext,
        )
        modtext = re.sub(
            r"\\end{tabular}\n*",
            r"""\\lspbottomrule
\\end{tabular}\n""",
            modtext,
        )

        modtext = modtext.replace("begin{tabular}", "begin{tabularx}{\\textwidth}")
        modtext = modtext.replace("end{tabular}", "end{tabularx}")
        modtext = modtext.replace("\\hhline", "%\\hhline%%replace by cmidrule")

        modtext = re.sub(r"\\setcounter{[^}]+\}\{0\}", "", modtext)

        modtext = re.sub("""listWWNum[ivxlc]+level[ivxlc]+""", "itemize", modtext)
        modtext = modtext.replace("\\begin{listLFOiileveli}\n\\item", "")
        modtext = modtext.replace("\\begin{listLFOiilevelii}\n\\item", "")
        modtext = modtext.replace("\\begin{listLFOiileveliii}\n\\item", "")
        modtext = modtext.replace("\\end{listLFOiileveli}", "")
        modtext = modtext.replace("\\end{listLFOiilevelii}", "")
        modtext = modtext.replace("\\end{listLFOiileveliii}", "")
        modtext = re.sub("""listL[FO]*[ivxlc]+level[ivxlc]+""", "itemize", modtext)

        modtext = modtext.replace(
            "& \\begin{itemize}\n\\item", "& \n%%\\begin{itemize}\\item\n"
        )
        modtext = modtext.replace("\\end{itemize}\\\\\n", "\\\\\n%%\\end{itemize}\n")
        modtext = modtext.replace("& \\end{itemize}", "& %%\\end{itemize}\n")

        modtext = re.sub(r"""\n+\\z""", r"\n\\z", modtext)
        modtext = re.sub("""\n\n+""", r"\n\n", modtext)

        # merge useless chains of formatting
        modtext = re.sub("(\\\\textbf\{[^}]+)\}\\\\textbf\{", "\\1", modtext)
        modtext = re.sub("(\\\\textit\{[^}]+)\}\\\\textit\{", "\\1", modtext)
        modtext = re.sub("(\\\\texttt\{[^}]+)\}\\\\texttt\{", "\\1", modtext)
        modtext = re.sub("(\\\\emph\{[^}]+)\}\\\\emph\{", "\\1", modtext)

        # remove all textits from sourcelines
        i = 1
        while i != 0:
            modtext, i = re.subn(r"(\\gll.*)\\textit", r"\1", modtext)

        # bold and smallcaps are used in example environments, so we want them to
        # enclose only minimal words
        for s in ("textbf", "textsc"):
            i = 1
            while i != 0:
                modtext, i = re.subn(
                    r"\\%s\{([^\}]+) " % s, r"\\%s{\1} \\%s{" % (s, s), modtext
                )

        modtext = re.sub(
            "\\\\includegraphics\[.*?width=\\\\textwidth\]\{",
            r"%please move the includegraphics inside the {figure} environment\n\
%%\\includegraphics[width=\\textwidth]{figures/",
            modtext,
        )

        modtext = re.sub("\\\\item *\n+", r"\\item ", modtext)

        modtext = re.sub(
            r"\\begin{itemize}\n\\item *(\\section{.*?})\n\\end{itemize}",
            r"\1",
            modtext,
        )

        modtext = re.sub(
            r"\\begin{itemize}\n\\item \\begin{itemize}\n\\item (\\subsection{.*?})\n\
\\end{itemize}\n\\end{itemize}",
            r"\1",
            modtext,
        )

        modtext = re.sub(
            r"\\begin{itemize}\n\\item *(\\section{.*?})\n\n\\begin{itemize}\n\
\\item (\\subsection{.*?})\n\\end{itemize}\n\\end{itemize}",
            r"\1\n\2",
            modtext,
        )

        modtext = re.sub("\\\\footnote\{ +", "\\\\footnote{", modtext)
        # put spaces on right side of formatting
        # right
        modtext = re.sub(" +\\}", "} ", modtext)
        # left
        modtext = re.sub("\\\\text(it|bf|sc|tt|up|rm)\\{ +", " \\\\text\\1{", modtext)
        modtext = re.sub(
            "\\\\text(it|bf|sc|tt|up|rm)\\{([!?\(\)\[\]\.\,\>]*)\\}", "\\2", modtext
        )
        modtext = re.sub(
            r"\\tablefirsthead\{\}\n\n\\tabletail\{\}\n\\tablelasttail\{\}", "", modtext
        )

        # duplicated section names
        modtext = re.sub(
            "(chapter|section|paragraph)\[.*?\](\{.*\}.*)", r"\1\2", modtext
        )

        bogus_styles = """styleStandard
        styleDefault
        styleBlockText
        styleTextbody
        styleTextbodyindent
        styleParagrapheArticle
        styleNormalWeb
        styleNormali
        styleNone
        styleNessuno
        styleHTMLPreformatted
        styleFootnoteSymbol
        styleDefault
        styleBodyTexti
        styleBodyTextii
        styleBodyTextiii
        styleBodyTextIndent
        styleBodyTextIndentii
        styleBodyTextIndentiii
        """.split()

        modtext = re.sub(f"\\\\(begin|end){('|'.join(bogus_styles))}", "", modtext)

        modtext = modtext.replace(
            "\\begin{itemize}\n\\item \\begin{styleLangSciEnumerated}\n",
            "\\begin{enumerate}\n\\item ",
        )
        modtext = modtext.replace(
            "\\end{styleLangSciEnumerated}\n\\end{itemize}", "\\end{enumerate}"
        )
        modtext = modtext.replace("\\begin{styleLangSciEnumerated}", "")
        modtext = modtext.replace("\\end{styleLangSciEnumerated}", "")

        modtext = modtext.replace("\n\n\\item", "\n\\item")
        modtext = modtext.replace("\n\n\\end", "\n\\end")
        modtext = modtext.replace("\n\n\\gll", "\n\\gll")
        modtext = modtext.replace("\n\n\\lsptoprule", "\n\\lsptoprule")
        modtext = modtext.replace("\n\n\n\\ea", "\n\n\\ea")
        modtext = modtext.replace(r"\section{ ", "\section{")
        modtext = modtext.replace(r"\section{}", "")
        modtext = modtext.replace(
            r"\z",
            "\z % you might need an extra \z if this is the last of several subexamples",
        )

        modtext = modtext.replace("XX}", "XX}\n")  # extra line after table start

        bibliography = ""
        modtext = modtext.replace(r"\textbf{References}", "References")
        modtext = modtext.replace(r"\section{References}", "References")
        modtext = modtext.replace(r"\chapter{References}", "References")
        a = re.compile("\n\s*References\s*\n").split(modtext)
        if len(a) == 2:
            modtext = a[0]
            refs = a[1].split("\n")
            bibliography = "\n".join([bibtools.Record(r).bibstring for r in refs])

        return (
            modtext
            + "\n\\begin{verbatim}%%move bib entries to  localbibliography.bib\n"
            + bibliography
            + "\\end{verbatim}"
        )
