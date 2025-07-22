from langsci.catalog.langscipressorg_webcrawler import get_soup, get_citeinfo, get_ISBN_digital
from langsci.catalog.catalogmetadata import (
    METALANGUAGE,
    ONE_LANGUAGE_BOOKS,
    LICENSES,
    SUPERSEDED,
)
import argparse
import re
import glob
from collections import defaultdict

parser = argparse.ArgumentParser(
    description="Generate tabular data for the langsci catalog"
)
# parser.add_argument("texdir", type=str, help="The directory where the tex sources for the books are stored")
parser.add_argument(
    "--chapters",
    action="store_true",
    help="Generate catalog entries for chapters as well",
)
args = parser.parse_args()

AUTHOR_AFFILIATION_PATTERN = re.compile(
    r"(.*?) *(\\orcid\{.*\})?\\affiliation\{(.*?)\} *(\\orcid\{.*\})?"
)
AND_PATTERN = re.compile(r"(\\lastand |\\and |lastand | and | with )")
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
        author = AND_PATTERN.split(aa[0])[-1].strip().replace("and ", "").strip()
        affiliation = aa[2]
        d[affiliation].append(author)
    return d


fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber creators title year isbn".split()

# fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber book_title year creator institution chapter_author chapter_title".split()
csvstrings = ["\t".join(fields)]

for ID in range(16, 550):
    # for ID in [239]:
    soup = get_soup(ID)
    citegroups = get_citeinfo(soup)
    if citegroups is None:
        continue
    print(ID)
    creators = citegroups["creators"]
    creatorstring = creators.replace("&nbsp;&nbsp;", "&")
    creatorstring = second_comma_to_ampersand(creators)
    try:
        digital_isbn = get_ISBN_digital(soup)
    except KeyError:
        digital_isbn = ''
    fields = [
        str(ID),
        citegroups["doi"] or "",
        citegroups["ed"] or "",
        METALANGUAGE.get(ID, "eng"),
        ONE_LANGUAGE_BOOKS.get(ID, ["", "", ""])[1],
        LICENSES.get(ID, "CC-BY  4.0"),
        str(ID in SUPERSEDED),
        "",
        citegroups["series"],
        citegroups["seriesnumber"],
        creatorstring,
        citegroups["title"].strip(),
        citegroups["year"].strip(),
        digital_isbn
    ]
    if args.chapters and citegroups["ed"]:
        fields[2] = "chapter"
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
            # print()
            # print(chapter)
            chapter_title = get_title(filecontent)
            chapter_author_affiliation = get_chapter_author_affiliations(filecontent)
            for affiliation in chapter_author_affiliation:
                for author in chapter_author_affiliation[affiliation]:
                    string = "\t".join(fields + [affiliation, author, chapter_title])
                    # print(string)
                    csvstrings.append(string)
    split_creators = False  # should each editor have their own line?
    if split_creators:
        for creator in creatorstring.split(" & "):
            # add all book creators in their own line
            fields[12] = creator
            if fields[2]:
                fields[2] = "editor"
            else:
                fields[2] = "author"
            csvstrings.append("\t".join(fields))
    else:
        # fields[12] = creatorstring
        if fields[2]:
            fields[2] = "editor"
        else:
            fields[2] = "author"
        csvstrings.append("\t".join(fields))


catalog_name = "catalog.csv"
if args.chapters:
    catalog_name = "catalog_chapters.csv"
with open(catalog_name, "w") as csvout:
    csvout.write("\n".join(csvstrings))
