from langsci.catalog.langscipressorg_webcrawler import get_soup, get_citeinfo, get_ISBN_digital, get_download_url, get_blurb
from langsci.catalog.catalogmetadata import (
    METALANGUAGE,
    ONE_LANGUAGE_BOOKS,
    LICENSES,
    SUPERSEDED,
)
# import argparse
import re
import glob
import sys
from collections import defaultdict
from openpyxl import Workbook


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

xlsx_headings = [
"Type of Document (Book or Chapter)",
"Book Title",
"Book Subtitle",
"Chapter Title",
"Authors - separate with ; - ORCID between ()",
"Editors  - separate with ; - ORCID between ()",
"Other Contributors  - separate with ; - ORCID between ()",
"Thema classification - separate with ;",
"Keywords (English)",
"Publisher",
"Year of publication (YYYY format)",
"Place of publication",
"Primary ISBN",
"Other ISBNs - separate with ;",
"DOI",
"Imprint",
"Series title",
"Series number",
"Series ISSN",
"Abstract (English)",
"Language(s) of the publication - separate with ; - based on ISO 639-2B",
"Number of Pages",
"Licence",
"Link to web shop",
"Link to download title",
"Link to cover file",
"Funder name",
"Funding program name",
"Funding project name",
"Funding: project acronym",
"Funding: grant number",
"Funding: jurisdiction",
"Collection name"
]



# fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber creators title year isbn".split()

# fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber book_title year creator institution chapter_author chapter_title".split()
# csvstrings = ["\t".join(fieldnames)]

if __name__ == "__main__":
    ids = sys.argv[1:]
    records = []
    for ID in ids:
        # for ID in [239]:
        soup = get_soup(ID)
        citegroups = get_citeinfo(soup)
        if citegroups is None:
            continue
        print(ID)
        creators = citegroups["creators"]
        ed = citegroups["ed"]
        creatorstring = creators.replace("&nbsp;&nbsp;", ";")
        # creatorstring = second_comma_to_ampersand(creators)
        digital_isbn = get_ISBN_digital(soup)
        fieldvalues = ['' for el in xlsx_headings]
        fieldvalues[0] = 'Book'
        title = citegroups["title"].strip()
        titles = title.split(':')
        fieldvalues[1] = titles[0].strip()
        try:
            fieldvalues[2] = titles[1].strip() #subtitle
        except IndexError:
            pass
        # fieldvalues[3] = chaptertitle
        if ed:
            fieldvalues[5] = creatorstring #editors
        else:
            fieldvalues[4] = creatorstring #authors
        # fieldvalues[6] = other contributors
        fieldvalues[7] = 'CF' #thema classification
        fieldvalues[8] = 'Linguistics' #keywords
        fieldvalues[9] = 'Language Science Press'
        fieldvalues[10] = citegroups["year"]
        fieldvalues[11] = 'Berlin'
        fieldvalues[12] = digital_isbn
        # fieldvalues[13] = other isbns
        fieldvalues[14] = citegroups["doi"]
        fieldvalues[15] = 'Language Science Press'
        fieldvalues[16] = citegroups["series"]
        fieldvalues[17] = citegroups["seriesnumber"]
        # fieldvalues[18] = series_issn
        fieldvalues[19] = get_blurb(soup)
        fieldvalues[20] = METALANGUAGE.get(ID, "eng")
        # fieldvalues[21] = number_of_pages
        fieldvalues[22] = LICENSES.get(ID, "CC-BY  4.0")
        fieldvalues[23] = f"https://langsci-press.org/catalog/book/{ID}"
        fieldvalues[24] = get_download_url(soup)
        fieldvalues[25] = "http://langsci-press.org/$$$call$$$/submission/cover/cover?submissionId={ID}&random=deadbeefdeadbeef"
        # fieldvalues[26] = funder name
        # fieldvalues[27] = fuding program name
        # fieldvalues[28] = funding project name
        # fieldvalues[29] = funding project acronym
        # fieldvalues[30] = funding grant number
        # fieldvalues[31] = funding jurisdiction
        fieldvalues[32] = "Language Science Press 2026"
        records.append(fieldvalues)


wb = Workbook()
ws = wb.active
ws.title = "BookData"
ws.append(xlsx_headings)
for record in records:
    ws.append(record)
wb.save("KU_Language_Science_Press.xlsx")

