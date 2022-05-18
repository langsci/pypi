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

ROMANCE = [236,308,165,27,286,258,16,183,143,200,160]

onixtemplate = """
<?xml version="1.0" encoding="UTF-8"?>
<ONIXmessage release="2.1" xmlns="http://www.editeur.org/onix/2.1/short"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.editeur.org/onix/2.1/short http://www.editeur.org/onix/2.1/short/ONIX_BookProduct_Release2.1_short.xsd">
    <header>
        <senderidentifier>
            <m379>01</m379>
            <b244>123</b244>
        </senderidentifier>
        <m174>Deutsche Nationalbibliothek</m174>
        <m182>20101213</m182>
        <m183>Updates Deutsche Nationalbibliothek 14.03.2011</m183>
        <m184>ger</m184>
    </header>
    <product>
        <a001>V615</a001>
        <a002>03</a002>
        <productidentifier>
            <b221>15</b221>
            <b244>9783123567890</b244>
        </productidentifier>
        <b012>DG</b012>
        <b211>002</b211>
        <b214>02</b214>
        <title>
            <b202>01</b202>
            <b203>
                Spezifikation von Transferpaketen und deren Übertragung an die Deutsche Nationalbibliothek mittels eines Hotfolders
            </b203>
        </title>
        <contributor>
            <b034>1</b034>
            <b035>A01</b035>
            <b039>Stefan</b039>
            <b040>Hein</b040>
        </contributor>
        <contributor>
            <b034>2</b034>
            <b035>A01</b035>
            <b039>Matthias</b039>
            <b040>Neubauer</b040>
        </contributor>
        <mainsubject>
            <b191>26</b191>
            <b068>2.0</b068>
            <b069>9631</b069>
        </mainsubject>
        <subject>
            <b067>20</b067>
            <b070>
                Hotfolder, Netzpublikationen, Transferpaket, Übertragung
            </b070>
        </subject>
        <productwebsite>
            <b367>02</b367>
            <f123>
                http://www.d-nb.de/netzpub/ablief/pdf/Spezifikation_Hotfolder.pdf
            </f123>
        </productwebsite>
        <publisher>
            <b291>01</b291>
            <b081>Deutsche Nationalbibliothek</b081>
            <website>
                <!--Publisher's corporate website-->
                <b367>01</b367>
                <b295>http://www.dnb.de/</b295>
            </website>
        </publisher>
        <b209>Frankfurt</b209>
        <b083>DE</b083>
        <b394>04</b394>
        <b003>20110314</b003>
    </product>
</ONIXmessage>
"""

SUPERSEDED = [22, 25, 46, 101, 141, 144, 149, 195]
CITEPATTERN = re.compile("(?P<creators>[^(]*)(?P<ed>\(eds?\.\))?\. (?P<year>[0-9]+)\. (?P<title>.*)\. \((?P<series>(.*)) (?P<seriesnumber>[0-9]*)\)\. Berlin: Language Science Press. DOI: (?P<doi>[^ ]*)")

fields = "ID DOI edited metalanguage objectlanguage license superseded pages series seriesnumber creators title year".split()
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
                citegroups["title"].strip(),
                citegroups["year"].strip()
                ]
    csvstrings.append("\t".join(fields))

with open("catalog.csv", "w") as csvout:
    csvout.write("\n".join(csvstrings))
