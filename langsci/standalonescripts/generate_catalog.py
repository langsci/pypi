import requests
import re
from bs4 import BeautifulSoup


ONE_LANGUAGE_BOOKS = {
#   ID  ISO6393 Glottocode   Name
    17: ("sje", "pite1240", "Pite Saami"),
    66: ("ybh", "yakk1236", "Yakkha"),
    67: ("mhl", "mauw1238", "Mauwake"),
    78: ("pmy", "papu1250", "Papuan Malay"),
    82: ("phl", "phal1254", "Palula"),
    85: ("fpe", "fern1234", "Pichi"),
    118: ("mlw", "molo1266", "Moloko"),
    124: ("rap", "rapa1244", "Rapa Nui"),
    212: ("tci", "wara1294", "Komnzo"),
    250: ("dar", "sanz1248", "Sanzhi Dargwa"),  #      (Iso is not precise here)
    298: ("gyi", "gyel1242", "Gyeli"),
    295: ("jya", "japh1234", "Japhug"),  # (Iso is not precise here)
    308: ("roh", "surs1245", "Tuatschin"),  # (Iso is not precise here)
    245: ("dga", "sout2789", "Dagaare"),
    98: ("ikx", "ikkk1242", "Ik"),
    326: ("ruc", "ruul1235", "Ruruuli"),
    287: ("nyy", "nyak1261", "Nyakyusa"),
    109: ("nru", "yong1288", "Yongning Na"),
    225: ("dar", "mege1234", "Mehweb"),
    228: ("aaz", "amar1273", "Amarasi"),
    150: ("rus", "russ1263", "Russian"),
    329: ("swe", "swed1254", "Swedish"),
    16: ("ita", "ital1282", "Italian"),
}

METALANGUAGE = {
    27: "fra",
    77: "fra",
    143: "fra",
    101: "deu",
    234: "deu",
    155: "deu",
    134: "deu",
    116: "deu",
    160: "por",
    200: "por",
    177: "cmn",
    236: "spa"
}

LICENSES = {
    148: "CC-BY-SA",
    149: "CC-BY-NC-ND",
    234: "CC-BY-NC-ND"
    }

SUPERSEDED = [22, 25, 46, 141, 144, 149, 195]
CITEPATTERN = re.compile("(?P<creators>[^(]*)(?P<ed>\(eds?\.\))?\. (?P<year>[0-9]+)\. (?P<title>.*)\. \((?P<series>(.*)) (?P<seriesnumber>[0-9]*)\)\. Berlin: Language Science Press. DOI: (?P<doi>[^ ]*)")

fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber creators title".split()
csvstrings = ["\t".join(fields)]
for ID in range(16,350):
    url = f"https://langsci-press.org/catalog/book/{ID}"
    html = requests.get(url).text
    if len(html) in (18920, 18922):
        continue
    print(f"{ID}", end=" ")
    soup = BeautifulSoup(html, 'html.parser')
    try:
        citeinfo = soup.find("div", "series").findNext('div','label').nextSibling.nextSibling.text.strip()
    except AttributeError:
        print("could not retrieve citeinfo")
        continue
    if "orthcoming" in citeinfo:
        print("not published yet")
        continue
    citegroups = CITEPATTERN.match(citeinfo)
    if citegroups is None:
        print("could not match citeinfo")
        continue
    print("OK")
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
                citegroups["title"].strip()
                ]
    csvstrings.append("\t".join(fields))

with open("catalog.csv", "w") as csvout:
    csvout.write("\n".join(csvstrings))
