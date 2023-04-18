try:
    from langscipressorg_webcrawler import get_soup, get_citeinfo
    from catalogmetadata import METALANGUAGE, ONE_LANGUAGE_BOOKS, LICENSES, SUPERSEDED
except ImportError:
    from langsci.langscipressorg_webcrawler import get_soup, get_citeinfo
    from langsci.catalogmetadata import METALANGUAGE, ONE_LANGUAGE_BOOKS, LICENSES, SUPERSEDED

import argparse
import re
import glob
from collections import defaultdict

parser = argparse.ArgumentParser(
description="Generate tabular data for the langsci catalog"
)
#parser.add_argument("texdir", type=str, help="The directory where the tex sources for the books are stored")
parser.add_argument(
    "--chapters",
    action="store_true",
    help="Generate catalog entries for chapters as well",
)
args = parser.parse_args()

AUTHOR_AFFILIATION_PATTERN = re.compile(r"(.*?) *(\\orcid\{.*\})?\\affiliation\{(.*?)\} *(\\orcid\{.*\})?")
AND_PATTERN = re.compile(r"(\\lastand |\\and |lastand | and | with)")
TITLE_PATTERN = re.compile(r"\\(markup)?title(\[.*?\] *)?\{(.*)\}")
AUTHOR_PATTERN = re.compile(r"\\author\{(.*)\}")




texdir = "langscitex"
outfilename = "sorted.bib"



def second_comma_to_ampersand(s):
    if not " & " in s:
        return s
    non_last_creator_string, last_creator = s.split(" & ")
    non_last_creator_list = non_last_creator_string.split(", ")
    result = ""
    comma_flag = True
    for creator_name_part in non_last_creator_list:
        result += creator_name_part
        if comma_flag:
            result += ", "
            comma_flag = False
        else:
            result += " & "
            comma_flag = True
    result += last_creator
    return result

def get_title(filecontent):
    title = TITLE_PATTERN.search(filecontent).group(3)
    return title


def get_chapter_author_affiliations(filecontent):
    d = defaultdict(list)
    tex_author_string = AUTHOR_PATTERN.search(filecontent).group(1)
    authors_and_affiliations = AUTHOR_AFFILIATION_PATTERN.findall(tex_author_string)
    for aa in authors_and_affiliations:
        print(aa)
        author = AND_PATTERN.split(aa[0])[-1].strip()
        affiliation = aa[2]
        d[affiliation].append(author)
    print(d)
    return d






fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber creators book_title year institution chapter_author chapter_title".split()
csvstrings = ["\t".join(fields)]

for ID in range(16,400):
#for ID in [239]:
    soup = get_soup(ID)
    citegroups = get_citeinfo(soup)
    if citegroups is None:
        continue
    creators = citegroups["creators"].replace("&nbsp;&nbsp;", "&")
    creators = second_comma_to_ampersand(creators)
    fields = [str(ID),
                citegroups["doi"] or '',
                citegroups["ed"] or '',
                METALANGUAGE.get(ID, "eng"),
                ONE_LANGUAGE_BOOKS.get(ID,['','',''])[1],
                LICENSES.get(ID, "CC-BY  4.0"),
                str(ID in SUPERSEDED),
                '',
                citegroups["series"],
                citegroups["seriesnumber"],
                creators,
                citegroups["title"].strip(),
                citegroups["year"].strip()
                ]
    csvstrings.append("\t".join(fields))
    if args.chapters and citegroups["ed"]:
        chapters = glob.glob(f"langscitex/{ID}/chapters/*tex")
        for chapter in chapters:
            with open(chapter) as infile:
                filecontent = infile.read()
            if "documentclass" not in filecontent:
                continue
            if chapter.endswith("acknowledgments.tex"):
                continue
            if chapter.endswith("preface.tex"):
                continue
            if chapter.endswith("prefaceEd.tex"):
                continue
            if chapter.endswith("abbreviations.tex"):
                continue
            if chapter.endswith("204/chapters/Savary.tex"):
                continue
            print()
            print(chapter)
            chapter_title = get_title(filecontent)
            chapter_author_affiliation = get_chapter_author_affiliations(filecontent)
            for affiliation in chapter_author_affiliation:
                for author in chapter_author_affiliation[affiliation]:
                    string = "\t".join(fields+[affiliation,author,chapter_title])
                    print(string)
                    csvstrings.append(string)

catalog_name = "catalog.csv"
if args.chapters:
    catalog_name = "catalog_chapters.csv"
with open(catalog_name, "w") as csvout:
    csvout.write("\n".join(csvstrings))
