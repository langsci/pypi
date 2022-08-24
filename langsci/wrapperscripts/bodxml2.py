import  yaml
from datetime import datetime
from PyPDF2 import PdfFileReader
import shutil
import zipfile
import codecs
import sys
from xml.sax.saxutils import escape
from langscipressorg_webcrawler import get_blurb, get_soup,   get_citeinfo, get_ISBNs, get_biosketches, biosketches2names, get_title_subtitle
from catalogmetadata import METALANGUAGE



book_ID = sys.argv[1]
soup = get_soup(book_ID)
citeinfo = get_citeinfo(soup)

title, booksubtitle = get_title_subtitle(citeinfo)
series = citeinfo['series']
seriesnumber = citeinfo['seriesnumber']
try:
    edition = sys.argv[2]
except IndexError:
    edition = 1



role = "author"
if citeinfo['ed']:
  role = "editor"

biosketches = get_biosketches(soup)
creatorlist = biosketches2names(biosketches)

creatortemplate="""
      <Contributor>
        <ContributorRole>{role}</ContributorRole>
        <ContributorName>{lastname}, {firstname}</ContributorName>
        <ContributorShortBio>{sketch}</ContributorShortBio>
      </Contributor>
"""


creators = []
for creator in creatorlist:
    firstname = escape(creator[0])
    lastname = escape(creator[1])
    sketch = escape(creator[2])
    creators.append(creatortemplate.format(**locals()))
creatorstring = "\n".join(creators)

blurb = get_blurb(soup)
date = '{:%Y%m%d}'.format(datetime.now())
time = '{:%H:%M}'.format(datetime.now())

colorpagecount = 0
colorpagesstring = '3'
try:
    with open('colorpages') as colorfile:
        colorpages = colorfile.readline().strip().split(',')
        colorpagecount = len(colorpages)
        colorpagesstring = ','.join(colorpages)
except IOError:
    print("No color pages info, please run make colorpages")
pagecount = PdfFileReader(open('Bookblock.pdf','rb')).getNumPages()

isbns = get_ISBNs(soup)
isbnsoftcover = isbns.get('softcover')
isbnhardcover = isbns.get('hardcover')
#isbnstring = ''
#binding = ''
#back = ''
#europrice = ''
#gbprice = ''
#usdprice = ''
booklanguage = METALANGUAGE.get(book_ID, 'eng')

bisac = "LAN009000"
if series == "Translation and Multilingual Natural Language Processing":
    bisac = "LAN023000"

bod_template = """<?xml version="1.0" encoding="utf-8"?>
<BoD>
  <Header>
    <FromCompany>Language Science Press</FromCompany>
    <FromCompanyNumber>110275446</FromCompanyNumber>
    <SentDate>{date}</SentDate>
    <SentTime>{time}</SentTime>
    <FromPerson>Sebastian Nordhoff</FromPerson>
    <FromEmail>support@langsci-press.org</FromEmail>
  </Header>
  <MasteringOrder>
    <Product>
      <MasteringType>Upload</MasteringType>
      <EAN>{isbnstring}</EAN>
      {creatorstring}
      <Title>{title}{booksubtitle}</Title>
      <Series>{series}  {seriesnumber}</Series>
      <EditionNumber>{edition}</EditionNumber>
      <PublicationDate>{date}</PublicationDate>
      <Blurb>{blurb}</Blurb>
      <Height>240</Height>
      <Width>170</Width>
      <Pages>{pagecount}</Pages>
      <ColouredPages>{colorpagecount}</ColouredPages>
      <ColouredPagesPosition>{colorpagesstring}</ColouredPagesPosition>

      <Paper>white</Paper>
      <Quality>Standard</Quality>
      <Binding>{binding}</Binding>
      {back}
      <Finish>matt</Finish>
      <Language>{booklanguage}</Language>
      <Subject Scheme="BISAC">{bisac}</Subject>
      <InternationalDistribution>Yes</InternationalDistribution>
      <Price>
        <PriceValue>{europrice}</PriceValue>
        <PriceCurrency>EUR</PriceCurrency>
      </Price>
      <Price>
        <PriceValue>{gbprice}</PriceValue>
        <PriceCurrency>GBP</PriceCurrency>
      </Price>
      <Price>
        <PriceValue>{usdprice}</PriceValue>
        <PriceCurrency>USD</PriceCurrency>
      </Price>
    </Product>
  </MasteringOrder>
</BoD>
"""



if isbnsoftcover is not None:
    isbnstring = isbnsoftcover
    #price is 3 EUR base + 3ct per page + 30ct extra per colorpage, rounded up to multiples of 5
    europrice = "%i.%s" %(((300+pagecount*7+colorpagecount*20)//500+1)*5,"00")
    usdprice = "%i.%s" %(((500+pagecount*7*1.5+colorpagecount*20)//500+1)*5,"00")
    if series == 'Textbooks in Language Sciences':
        europrice = "25.00"
        usdprice = "35.00"
    gbprice = europrice
    binding = 'PB'
    back = ''
    outputSC = bod_template.format(**locals())
    print ("Creating xml file for softcover", isbnsoftcover)
    scxml = codecs.open("bod/%s_MasteringOrder.xml"%isbnsoftcover, mode='w',encoding="utf-8")
    scxml.write(outputSC)
    scxml.close()
    print("renaming pdf files according to ISBNs")
    shutil.copy('Bookblock.pdf','bod/%s_Bookblock.pdf'%isbnsoftcover)
    try:
        shutil.copy('coverSC.pdf','bod/%s_cover.pdf'%isbnsoftcover)
    except FileNotFoundError:
        print("File coverSC.pdf not found. Did you run the Ghostview script?\n gs -dPDFX -dBATCH -dNOPAUSE -dUseCIEColor -sProcessColorModel=DeviceCMYK -sDEVICE=pdfwrite -sPDFACompatibilityPolicy=1 -sOutputFile=coverSC.pdf bodcoverSC.pdf")
    print("Creating zip file for softcover", isbnsoftcover)
    zfsc = zipfile.ZipFile('%s_MasteringOrder.zip'%isbnsoftcover, mode='w')
    zfsc.write('bod/%s_MasteringOrder.xml'%isbnsoftcover)
    zfsc.write('bod/%s_Bookblock.pdf'%isbnsoftcover)
    zfsc.write('bod/%s_cover.pdf'%isbnsoftcover)
    zfsc.close()
    print("Softcover files created. Files are in /bod")
else:
    print("Skipping softcover, because no softcover ISBN was provided.")

if isbnhardcover is not None:
    isbnstring = isbnhardcover
    #Hardcover is always 10 EUR more than softcover
    europrice = "%i.%s" %(((1300+pagecount*7+colorpagecount*12)//500+1)*5,"00")
    usdprice = "%i.%s" %(((1800+pagecount*7*1.3+colorpagecount*12)//500+1)*5,"00")
    #europrice = "35.00"
    if series == 'Textbooks in Language Sciences':
        europrice = "35.00"
        usdprice = "45.00"
    gbprice = europrice
    #usdprice = europrice
    binding = 'HC'
    back = '<Back>rounded</Back>'
    outputHC = bod_template.format(**locals())
    print("Creating xml file for hardcover", isbnhardcover)
    hcxml = codecs.open("bod/%s_MasteringOrder.xml"%isbnhardcover ,mode='w',encoding="utf-8")
    hcxml.write(outputHC)
    hcxml.close()
    print("renaming pdf files according to ISBNs")
    shutil.copy('Bookblock.pdf','bod/%s_Bookblock.pdf'%isbnhardcover)
    try:
        shutil.copy('coverHC.pdf','bod/%s_coverHC.pdf'%isbnhardcover)
    except FileNotFoundError:
        print("File coverSC.pdf not found. Did you run the Ghostview script?\n gs -dPDFX -dBATCH -dNOPAUSE -dUseCIEColor -sProcessColorModel=DeviceCMYK -sDEVICE=pdfwrite -sPDFACompatibilityPolicy=1 -sOutputFile=coverHC.pdf bodcoverHC.pdf")
    print("Creating zip file for hardcover", isbnhardcover)
    zfhc = zipfile.ZipFile('bod/%s_MasteringOrder.zip'%isbnhardcover, mode='w')
    zfhc.write('bod/%s_MasteringOrder.xml'%isbnhardcover)
    zfhc.write('bod/%s_Bookblock.pdf'%isbnhardcover)
    zfhc.write('bod/%s_coverHC.pdf'%isbnhardcover)
    zfhc.close()
    print("Hardcover files created. Files are in /bod")
else:
    print("Skipping hardcover, because no hardcover ISBN was provided.")
