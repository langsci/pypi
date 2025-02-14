import sys

try:
    from langscipressorg_webcrawler import (
        get_blurb,
        get_soup,
        get_publication_date,
        get_citeinfo,
        get_ISBN_digital,
        get_biosketches,
        get_title_subtitle,
        biosketches2names,
    )
except ImportError:
    from langsci.langscipressorg_webcrawler import (
        get_blurb,
        get_soup,
        get_publication_date,
        get_citeinfo,
        get_ISBN_digital,
        get_biosketches,
        get_title_subtitle,
        biosketches2names,
    )


IDs = sys.argv[1:]
for ID in IDs:
    soup = get_soup(ID)
    citeinfo = get_citeinfo(soup)
    title = citeinfo["title"].strip()
    edited = citeinfo["ed"] or ""
    creators = citeinfo["creators"]
    edited_by = ""
    if edited:
        edited_by = "edited "
    template = f"""<li class="show"><a href="/catalog/book/{ID}"><img style="width: 200px !important;" src="/$$$call$$$/submission/cover/cover?submissionId={ID}" alt="cover for {title}" /><br />{title} {edited_by} by {creators} </a></li>"""
    print(template)
