import sys

from langsci.langscipressorg_webcrawler import get_soup, get_publication_date, get_citeinfo, get_ISBN_digital, get_title_subtitle, get_biosketches, biosketches2names

book_ID = sys.argv[1]
soup = get_soup(book_ID)
citegroups = get_citeinfo(soup)
biosketches = get_biosketches(soup)
if citegroups is None:
  sys.exit()

title, subtitle = get_title_subtitle(citegroups)
series = citegroups["series"]

creatorlist = biosketches2names(biosketches)


creatortype = 'vauthors'
if citegroups['ed']:
    creatortype = 'veditors'

vcreators = ", ".join([u"%s %s"%(creatormetadata[1],
                                ''.join([firstname[0]
                                        for firstname
                                        in creatormetadata[0].split()
                                        ])
                                )
                        for creatormetadata
                        in creatorlist])


creatorstring = f'{creatortype}={vcreators}'

isbn_digital = get_ISBN_digital(soup)
key = vcreators.split()[0] + citegroups['year']
print(f"""<ref name = "{key}">{{{{Cite book
| {creatorstring}
| title = {title} {subtitle}
| place = Berlin
| publisher = Language Science Press
| date = {citegroups['year']}
| format = pdf
| url = http://langsci-press.org/catalog/book/{book_ID}
| doi = {citegroups['doi']}
| doi-access = free
| isbn = {isbn_digital}
}}}}
</ref>
""")

