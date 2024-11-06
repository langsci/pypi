import sys
from langsci import langscipressorg_webcrawler

def refubiumstring(id_):
    soup = langscipressorg_webcrawler.get_soup(id_)
    citegroups = langscipressorg_webcrawler.get_citeinfo(soup)
    title = citegroups['title']
    series = citegroups['series']
    number = citegroups['seriesnumber']
    creators = citegroups['creators']
    doi = citegroups['doi']
    ed = citegroups['ed']
    edstring = ''
    if ed:
        edstring = ed
    url = f"https://langsci-press.org/catalog/book/{id_}"
    return(f"""{title}
({series} {number})
{creators} {edstring}
{doi}
{url}""")

if __name__ == "__main__":
    ids = sys.argv[1:]
    for id_ in ids:
        print(refubiumstring(id_))
        print()




