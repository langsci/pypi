try:
    from langscipressorg_webcrawler import get_soup, get_citeinfo
    from catalogmetadata import METALANGUAGE, ONE_LANGUAGE_BOOKS, LICENSES, SUPERSEDED
except ImportError:
    from langsci.langscipressorg_webcrawler import get_soup, get_citeinfo
    from langsci.catalogmetadata import METALANGUAGE, ONE_LANGUAGE_BOOKS, LICENSES, SUPERSEDED

fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber creators title year".split()
csvstrings = ["\t".join(fields)]

for ID in range(16,350):
    soup = get_soup(ID)
    citegroups = get_citeinfo(soup)
    if citegroups is None:
        continue
    fields = [str(ID),
                citegroups["doi"] or '',
                citegroups["ed"] or '',
                METALANGUAGE.get(ID, "eng"),
                ONE_LANGUAGE_BOOKS.get(ID,['','',''])[1],
                LICENSES.get(ID, "CC-BY"),
                str(ID in SUPERSEDED),
                '',
                citegroups["series"],
                citegroups["seriesnumber"],
                citegroups["creators"].replace("&nbsp;&nbsp;", "&"),
                citegroups["title"].strip(),
                citegroups["year"].strip()
                ]
    csvstrings.append("\t".join(fields))

with open("catalog.csv", "w") as csvout:
    csvout.write("\n".join(csvstrings))
