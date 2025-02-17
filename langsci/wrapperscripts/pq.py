import sys
from langsci import langscipressorg_webcrawler


def li_string(id_):
    soup = langscipressorg_webcrawler.get_soup(id_)
    citegroups = langscipressorg_webcrawler.get_citeinfo(soup)
    title = citegroups['title']
    creators = citegroups['creators']
    ed = citegroups['ed']
    edstring = ''
    if ed:
        edstring = 'edited'
    url = f"https://langsci-press.org/catalog/book/{id_}"
    return(f"""<li class="show"><a href="/catalog/book/{id_}"><img style="width: 200px !important;" src="/$$$call$$$/submission/cover/cover?submissionId={id_}" alt="" /><br />{title} {edstring} by {creators} </a></li>""")



if __name__ == "__main__":
    ids = sys.argv[1:]
    for id_ in ids:
        print(li_string(id_))
        print()




