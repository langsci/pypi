import yaml
import sys
from datetime import date
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from langsci.catalog.langscipressorg_webcrawler import (
        get_blurb,
        get_soup,
        get_publication_date,
        get_citeinfo,
        get_ISBN_digital,
        get_ISBN_hardcover,
        get_biosketches,
        get_title_subtitle,
        biosketches2names,
    )
from langsci.catalog.catalogmetadata import LICENSES, SERIES, METALANGUAGE


book_ID = sys.argv[1]
soup = get_soup(book_ID)
citegroups = get_citeinfo(soup)
if citegroups is None:
    sys.exit()
print(book_ID)

title, subtitle = get_title_subtitle(citegroups)

series = citegroups["series"]

seriesnumber = citegroups["seriesnumber"]

publication_date = get_publication_date(soup).replace("-", "")
blurb = get_blurb(soup)
try:
  isbn_digital = get_ISBN_digital(soup)
  isbn_print = get_ISBN_hardcover(soup)
except KeyError:
  print(' no ISBN. Skipping')
  sys.exit()
issn = SERIES[citegroups["series"]]
metalanguage = METALANGUAGE.get(book_ID, "eng")

biosketches = get_biosketches(soup)

bisac = "LAN009000"
wgs = "9561"
if series == "Translation and Multilingual Natural Language Processing":
    bisac = "LAN023000"

license = LICENSES.get(book_ID, "CC-BY")
license_url = "https://creativecommons.org/licenses/%s/4.0" % license[3:]
authorrolecode = "A01"
editorrolecode = "B01"

role = authorrolecode
if citegroups["ed"]:
    role = editorrolecode


# FIXME mix of authors and editors


proquest_creator_template = """<Contributor>
        <SequenceNumber>%s</SequenceNumber>
        <ContributorRole>%s</ContributorRole>
        <NamesBeforeKey>%s</NamesBeforeKey>
        <KeyNames>%s</KeyNames>
        <BiographicalNote>%s</BiographicalNote>
</Contributor>"""


creators = []

creatorlist = biosketches2names(biosketches)

for i, creator in enumerate(creatorlist):
    firstname = creator[0]
    lastname = creator[1]
    sketch = creator[2]
    creators.append(
        proquest_creator_template
        % (i + 1, role, escape(firstname), escape(lastname), escape(sketch))
    )
creatorstring = "\n".join(creators)

# creatorstring = authorstring + editorstring
today = date.today().strftime("%Y%m%d")


proquest_template = f"""<?xml version="1.0"?>
<ONIXMessage release="3.0">
  <Header>
    <Sender>
      <SenderIdentifier>
        <SenderIDType>05</SenderIDType>
        <IDValue>978-3-98554</IDValue>
      </SenderIdentifier>
      <SenderName>Language Science Press</SenderName>
      <ContactName>Sebastian Nordhoff</ContactName>
      <EmailAddress>support@langsci-press.org</EmailAddress>
    </Sender>
    <Addressee>
      <AddresseeName>ProQuest</AddresseeName>
    </Addressee>
    <SentDateTime>{today}</SentDateTime>
  </Header>
  <Product>
    <RecordReference>langsci-press.org/{book_ID}</RecordReference>
    <NotificationType>03</NotificationType>
    <RecordSourceType>01</RecordSourceType>
    <RecordSourceIdentifier>
      <RecordSourceIDType>05</RecordSourceIDType>
      <IDValue>978-3-98554</IDValue>
    </RecordSourceIdentifier>
    <RecordSourceName>Language Science Press</RecordSourceName>
    <ProductIdentifier>
      <ProductIDType>06</ProductIDType>
      <IDValue>{citegroups["doi"]}</IDValue>
    </ProductIdentifier>
    <ProductIdentifier>
      <ProductIDType>15</ProductIDType>
      <IDValue>{isbn_digital}</IDValue>
    </ProductIdentifier>
    <DescriptiveDetail>
      <!-- P.3 -->
      <ProductComposition>00</ProductComposition>
      <ProductForm>ED</ProductForm>
      <!-- <EpubType>002</EpubType> -->
      <!--
      <Measure>
        <MeasureType>01</MeasureType>
        <Measurement>24.00</Measurement>
        <MeasureUnitCode>cm</MeasureUnitCode>
      </Measure>
      <Measure>
        <MeasureType>02</MeasureType>
        <Measurement>17.00</Measurement>
        <MeasureUnitCode>cm</MeasureUnitCode>
      </Measure>
      -->
      <Collection>
        <CollectionType>10</CollectionType>
        <CollectionIdentifier>
          <CollectionIDType>02</CollectionIDType>
          <IDValue>{issn}</IDValue>
        </CollectionIdentifier>
        <CollectionSequence>
          <CollectionSequenceType>02</CollectionSequenceType>
          <CollectionSequenceNumber>9</CollectionSequenceNumber>
        </CollectionSequence>
        <TitleDetail>
          <TitleType>01</TitleType>
          <TitleElement>
            <TitleElementLevel>02</TitleElementLevel>
            <TitleText textcase="02">{series}</TitleText>
          </TitleElement>
        </TitleDetail>
      </Collection>
      <TitleDetail>
        <TitleType>01</TitleType>
        <TitleElement>
          <TitleElementLevel>01</TitleElementLevel>
          <TitleText textcase="01">{title}</TitleText>
          <Subtitle>{subtitle}</Subtitle>
        </TitleElement>
      </TitleDetail>
      {creatorstring}
      <EditionNumber>1</EditionNumber>
      <Language>
        <LanguageRole>01</LanguageRole>
        <LanguageCode>{metalanguage}</LanguageCode>
      </Language>
      <Subject>
        <MainSubject />
        <SubjectSchemeIdentifier>10</SubjectSchemeIdentifier>
        <SubjectSchemeVersion>2009</SubjectSchemeVersion>
        <SubjectCode>{bisac}</SubjectCode>
      </Subject>
      <Subject>
        <MainSubject />
        <SubjectSchemeIdentifier>26</SubjectSchemeIdentifier>
        <SubjectSchemeVersion>2.0</SubjectSchemeVersion>
        <SubjectCode>{wgs}</SubjectCode>
      </Subject>
      <AudienceCode>06</AudienceCode>
      <EpubLicense>
        <EpubLicenseExpression>
          <EpubLicenseExpressionLink>{license_url.lower()}</EpubLicenseExpressionLink>
        </EpubLicenseExpression>
      </EpubLicense>
    </DescriptiveDetail>
    <CollateralDetail>
      <TextContent>
        <TextType>03</TextType>
        <Text textformat="05">
          {escape(blurb)}
        </Text>
      </TextContent>
      <SupportingResource>
        <ResourceContentType>01</ResourceContentType>
        <ContentAudience>00</ContentAudience>
        <ResourceMode>03</ResourceMode>
        <ResourceVersion>
          <ResourceForm>02</ResourceForm>
          <ResourceVersionFeature>
            <ResourceVersionFeatureType>01</ResourceVersionFeatureType>
            <FeatureValue>D503</FeatureValue>
          </ResourceVersionFeature>
          <ResourceLink>https://langsci-press.org/$$$call$$$/submission/cover/cover?submissionId={book_ID}</ResourceLink>
        </ResourceVersion>
      </SupportingResource>
      <TextContent>
        <TextType>20</TextType>
        <Text>This text is licensed as {license} 4.0</Text>
      </TextContent>
    </CollateralDetail>
    <PublishingDetail>
      <Publisher>
        <PublishingRole>01</PublishingRole>
        <PublisherName>Language Science Press</PublisherName>
        <Website>
          <WebsiteRole>01</WebsiteRole>
          <WebsiteLink>https://www.langsci-press.org</WebsiteLink>
        </Website>
      </Publisher>
      <CityOfPublication>Berlin</CityOfPublication>
      <CountryOfPublication>DE</CountryOfPublication>
      <PublishingStatus>04</PublishingStatus>
      <PublishingDate>
        <PublishingDateRole>01</PublishingDateRole>
        <Date dateformat="00">{publication_date}</Date>
      </PublishingDate>
    </PublishingDetail>
    <ProductSupply>
      <SupplyDetail>
        <UnpricedItemType>01</UnpricedItemType>
      </SupplyDetail>
    </ProductSupply>
    <othertext>
            <d102>20</d102>
            <d103>06</d103>
            <d104>Der Titel ist Open Access unter der Creative Commons Lizenz {license} 4.0</d104>
  </othertext>
    <othertext>
            <d102>46</d102>
            <d103>01</d103>
            <d104>{license_url.lower()}</d104>
  </othertext>
  <OtherText>
    <TextTypeCode>47</TextTypeCode>
    <TextFormat>06</TextFormat>
    <Text>Open access </Text>
  </OtherText>
  </Product>
</ONIXMessage>"""

onix2_template = f"""<?xml version="1.0"?>
<ONIXMessage xmlns="http://www.editeur.org/onix/2.1">
  <Header>
    <Sender>
      <SenderIdentifier>
        <SenderIDType>05</SenderIDType>
        <IDValue>978-3-98554</IDValue>
      </SenderIdentifier>
      <SenderName>Language Science Press</SenderName>
      <ContactName>Sebastian Nordhoff</ContactName>
      <EmailAddress>support@langsci-press.org</EmailAddress>
    </Sender>
    <Addressee>
      <AddresseeName>ProQuest</AddresseeName>
    </Addressee>
    <SentDateTime>{today}</SentDateTime>
  </Header>
  <Product>
    <RecordReference>langsci-press.org/{book_ID}</RecordReference>
    <NotificationType>03</NotificationType>
    <RecordSourceType>01</RecordSourceType>
    <RecordSourceIdentifier>
      <RecordSourceIDType>05</RecordSourceIDType>
      <IDValue>978-3-98554</IDValue>
    </RecordSourceIdentifier>
    <RecordSourceName>Language Science Press</RecordSourceName>
    <ProductIdentifier>
      <ProductIDType>06</ProductIDType>
      <IDValue>{citegroups["doi"]}</IDValue>
    </ProductIdentifier>
    <ProductIdentifier>
      <ProductIDType>15</ProductIDType>
      <IDValue>{isbn_digital}</IDValue>
    </ProductIdentifier>
    <DescriptiveDetail>
      <!-- P.3 -->
      <ProductComposition>00</ProductComposition>
      <ProductForm>ED</ProductForm>
      <Collection>
        <CollectionType>10</CollectionType>
        <CollectionIdentifier>
          <CollectionIDType>02</CollectionIDType>
          <IDValue>{issn}</IDValue>
        </CollectionIdentifier>
        <CollectionSequence>
          <CollectionSequenceType>02</CollectionSequenceType>
          <CollectionSequenceNumber>9</CollectionSequenceNumber>
        </CollectionSequence>
        <TitleDetail>
          <TitleType>01</TitleType>
          <TitleElement>
            <TitleElementLevel>02</TitleElementLevel>
            <TitleText>{series}</TitleText>
          </TitleElement>
        </TitleDetail>
      </Collection>
      <TitleDetail>
        <TitleType>01</TitleType>
        <TitleElement>
          <TitleElementLevel>01</TitleElementLevel>
          <TitleText>{title}</TitleText>
          <Subtitle>{subtitle}</Subtitle>
        </TitleElement>
      </TitleDetail>
      {creatorstring}
      <EditionNumber>1</EditionNumber>
      <Language>
        <LanguageRole>01</LanguageRole>
        <LanguageCode>{metalanguage}</LanguageCode>
      </Language>
      <Subject>
        <MainSubject />
        <SubjectSchemeIdentifier>10</SubjectSchemeIdentifier>
        <SubjectSchemeVersion>2009</SubjectSchemeVersion>
        <SubjectCode>{bisac}</SubjectCode>
      </Subject>
      <Subject>
        <MainSubject />
        <SubjectSchemeIdentifier>26</SubjectSchemeIdentifier>
        <SubjectSchemeVersion>2.0</SubjectSchemeVersion>
        <SubjectCode>{wgs}</SubjectCode>
      </Subject>
      <AudienceCode>06</AudienceCode>
      <EpubLicense>
        <EpubLicenseExpression>
          <EpubLicenseExpressionLink>{license_url.lower()}</EpubLicenseExpressionLink>
        </EpubLicenseExpression>
      </EpubLicense>
    </DescriptiveDetail>
    <CollateralDetail>
      <TextContent>
        <TextType>03</TextType>
        <Text textformat="05">
          {escape(blurb)}
        </Text>
      </TextContent>
      <SupportingResource>
        <ResourceContentType>01</ResourceContentType>
        <ContentAudience>00</ContentAudience>
        <ResourceMode>03</ResourceMode>
        <ResourceVersion>
          <ResourceForm>02</ResourceForm>
          <ResourceVersionFeature>
            <ResourceVersionFeatureType>01</ResourceVersionFeatureType>
            <FeatureValue>D503</FeatureValue>
          </ResourceVersionFeature>
          <ResourceLink>https://langsci-press.org/$$$call$$$/submission/cover/cover?submissionId={book_ID}</ResourceLink>
        </ResourceVersion>
      </SupportingResource>
      <TextContent>
        <TextType>20</TextType>
        <Text>This text is licensed as {license} 4.0</Text>
      </TextContent>
    </CollateralDetail>
    <PublishingDetail>
      <Publisher>
        <PublishingRole>01</PublishingRole>
        <PublisherName>Language Science Press</PublisherName>
        <Website>
          <WebsiteRole>01</WebsiteRole>
          <WebsiteLink>https://www.langsci-press.org</WebsiteLink>
        </Website>
      </Publisher>
      <CityOfPublication>Berlin</CityOfPublication>
      <CountryOfPublication>DE</CountryOfPublication>
      <PublishingStatus>04</PublishingStatus>
      <PublishingDate>
        <PublishingDateRole>01</PublishingDateRole>
        <Date>{publication_date}</Date>
      </PublishingDate>
    </PublishingDetail>
    <ProductSupply>
      <SupplyDetail>
        <UnpricedItemType>01</UnpricedItemType>
      </SupplyDetail>
    </ProductSupply>
    <OtherText>
      <TextTypeCode>47</TextTypeCode>
      <TextFormat>06</TextFormat>
      <Text>Open access </Text>
    </OtherText>
  </Product>
</ONIXMessage>
"""


onix3_template = f"""<?xml version="1.0"?>
<ONIXmessage release="3.0">

<Header>
  <sender>
    <SenderName>Language Science Press</SenderName>
    <ContactName>Sebastian Nordhoff</ContactName>
    <EmailAddress>support@langsci-press.org</EmailAddress>
  </sender>
    <SentDateTime>{today}</SentDateTime>
</Header>

<Product>
  <RecordReference>langsci-press.org/{book_ID}</RecordReference>
  <NotificationType>03</NotificationType>
  <RecordSourceType>01</RecordSourceType>
  <RecordSourceIdentifier>
    <RecordSourceIDType>05</RecordSourceIDType>
    <IDValue>978-3-98554</IDValue>
  </RecordSourceIdentifier>
  <RecordSourceName>Language Science Press</RecordSourceName>

  <ProductIdentifier>
    <ProductIDType>15</ProductIDType>
    <IDTypeName>{isbn_digital}</IDTypeName>
    <ProductForm> EA </ProductForm>
    <ProductFormDetail> E107 </ProductFormDetail>
  </ProductIdentifier>

  <PrimaryContentType> 10 </PrimaryContentType>

  <ProductFormfeature>
    <ProductFormFeatureType> 09  </ProductFormFeatureType>
    <ProductFormFeatureValue> 11 </ProductFormFeatureValue>
  </ProductFormfeature>

  <ProductFormfeature>
    <ProductFormFeatureType> 09  </ProductFormFeatureType>
    <ProductFormFeatureValue> 12 </ProductFormFeatureValue>
  </ProductFormfeature>

  <ProductFormfeature>
    <ProductFormFeatureType> 09  </ProductFormFeatureType>
    <ProductFormFeatureValue> 25 </ProductFormFeatureValue>
  </ProductFormfeature>

  <ProductFormfeature>
    <ProductFormFeatureType> 12</ProductFormFeatureType>
    <ProductFormFeatureValue> 00</ProductFormFeatureValue>
  </ProductFormfeature>

  <DescriptiveDetail>
    <ProductComposition>00</ProductComposition>
    <ProductForm>ED</ProductForm>
    <!-- <EpubType>002</EpubType> -->
    <Measure>
      <MeasureType>01</MeasureType>
      <Measurement>24.00</Measurement>
      <MeasureUnitCode>cm</MeasureUnitCode>
    </Measure>
    <Measure>
      <MeasureType>02</MeasureType>
      <Measurement>17.00</Measurement>
      <MeasureUnitCode>cm</MeasureUnitCode>
    </Measure>

    <Collection>
      <CollectionType>10</CollectionType>
      <CollectionIdentifier>
        <CollectionIDType>02</CollectionIDType>
        <IDValue>{issn}</IDValue>
      </CollectionIdentifier>
      <CollectionSequence>
        <CollectionSequenceType>02</CollectionSequenceType>
      <CollectionSequenceNumber>{seriesnumber}</CollectionSequenceNumber>
      </CollectionSequence>
      <TitleDetail>
        <TitleType>01</TitleType>
        <TitleElement>
          <TitleElementLevel>02</TitleElementLevel>
          <TitleText textcase="02">{series}</TitleText>
        </TitleElement>
      </TitleDetail>
    </Collection>

    <TitleDetail>
      <TitleType>01</TitleType>
      <TitleElement>
        <TitleElementLevel>01</TitleElementLevel>
        <TitleText textcase="01">{title}</TitleText>
        <Subtitle>{subtitle}</Subtitle>
      </TitleElement>
    </TitleDetail>

    {creatorstring}

    <EditionNumber>1</EditionNumber>

    <Language>
      <LanguageRole>01</LanguageRole>
      <LanguageCode>{metalanguage}</LanguageCode>
    </Language>

    <Subject>
      <MainSubject />
      <SubjectSchemeIdentifier>10</SubjectSchemeIdentifier>
      <SubjectSchemeVersion>2009</SubjectSchemeVersion>
      <SubjectCode>{bisac}</SubjectCode>
    </Subject>

    <Subject>
      <MainSubject />
      <SubjectSchemeIdentifier>26</SubjectSchemeIdentifier>
      <SubjectSchemeVersion>2.0</SubjectSchemeVersion>
      <SubjectCode>{wgs}</SubjectCode>
    </Subject>

    <AudienceCode>06</AudienceCode>

    <EpubLicense>
      <EpubLicenseExpression>
        <EpubLicenseExpressionLink>{license_url.lower()}</EpubLicenseExpressionLink>
      </EpubLicenseExpression>
    </EpubLicense>
  </DescriptiveDetail>
   <CollateralDetail>
      <TextContent>
        <TextType>03</TextType>
        <ContentAudience> 00  </ContentAudience>
        <Text textformat="05">
          {escape(blurb)}
        </Text>
      </TextContent>
      <Imprint>
        <ImprintName> Language Science Press</ImprintName>
      </Imprint>
      <SupportingResource>
        <ResourceContentType>01</ResourceContentType>
        <ContentAudience>00</ContentAudience>
        <ResourceMode>03</ResourceMode>
        <ResourceVersion>
          <ResourceForm>02</ResourceForm>
          <ResourceVersionFeature>
            <ResourceVersionFeatureType>01</ResourceVersionFeatureType>
            <FeatureValue>D503</FeatureValue>
          </ResourceVersionFeature>
          <ResourceLink>https://langsci-press.org/$$$call$$$/submission/cover/cover?submissionId={book_ID}</ResourceLink>
        </ResourceVersion>
      </SupportingResource>
      <TextContent>
        <TextType>20</TextType>
        <Text>This text is licensed as {license} 4.0</Text>
      </TextContent>
    </CollateralDetail>
    <PublishingDetail>
      <Publisher>
        <PublishingRole>01</PublishingRole>
        <PublisherName>Language Science Press</PublisherName>
        <PublisherIdentifier>
          <PublisherIDType> 05 </PublisherIDType>
          <IDValue> 978-3-98554</IDValue>
        </PublisherIdentifier>
        <Website>
          <WebsiteRole>01</WebsiteRole>
          <WebsiteLink>https://www.langsci-press.org</WebsiteLink>
        </Website>
        <PublishingStatus>04</PublishingStatus>
        <CityOfPublication>Berlin</CityOfPublication>
        <CountryOfPublication>DE</CountryOfPublication>
      </Publisher>
      <PublishingDate>
        <PublishingDateRole>01</PublishingDateRole>
        <Date dateformat="00">{publication_date}</Date>
      </PublishingDate>
    </PublishingDetail>
    <ProductSupply>
      <SupplyDetail>
        <UnpricedItemType>01</UnpricedItemType>
      </SupplyDetail>
    </ProductSupply>
    <othertext>
            <d102>20</d102>
            <d103>06</d103>
            <d104>Der Titel ist Open Access unter der Creative Commons Lizenz {license} 4.0</d104>
    </othertext>
    <othertext>
            <d102>46</d102>
            <d103>01</d103>
            <d104>{license_url.lower()}</d104>
    </othertext>
    <OtherText>
      <TextTypeCode>47</TextTypeCode>
      <TextFormat>06</TextFormat>
      <Text>Open access </Text>
    </OtherText>
    <copyrightstatement>
      <CopyrightType> C </CopyrightType>
      <CopyrightYear> {publication_date[:4]} </CopyrightYear>
    </copyrightstatement>
    <RelatedProduct>
      <RelationCode> 13 </RelationCode>
      <ProductIdentifier>
        <ProductIDType> 15</ProductIDType>
        <IDValue> {isbn_print} </IDValue>
        <ProductForm> BB </ProductForm>
      </ProductIdentifier>
    </RelatedProduct>
  </Product>
</ONIXmessage>

"""

onix_vlb_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<ONIXmessage release="3.1"><header><sender><x298>Language Science Press</x298><x299>Sebastian Nordhoff</x299><j272>sebastian.nordhoff@langsci-press.org</j272></sender><x307>{senddate}</x307></header>
<product datestamp="{senddate}">
    <a001>{bookid}</a001>
    <a002>03</a002> <!-->notification type</!-->
    <productidentifier>
        <b221>03</b221>
        <b244>{isbndigital}</b244>
    </productidentifier>
    <productidentifier>
        <b221>06</b221>
        <b244>{doi}</b244>
    </productidentifier>
    <productidentifier>
        <b221>15</b221>
        <b244>{isbndigital}</b244>
    </productidentifier>
    <descriptivedetail>
        <x314>00</x314> <!--> einteiliges produkt <?!-->
        <b012>BB</b012>
        <measure>
            <x315>01</x315>
            <c094>18</c094>
            <c095>cm</c095>
        </measure>
        <measure>
            <x315>02</x315>
            <c094>24.5</c094>
            <c095>cm</c095>
        </measure>
        <collection>
            <x329>10</x329> <!-->ist Reihe</!-->
            <titledetail>
                <b202>01</b202>
                <titleelement>
                    <x409>02</x409>
                    <b203>{seriesname}</b203>
                </titleelement>
                <titleelement>
                    <x409>01</x409>
                    <x410>{seriesnumber}</x410>
                </titleelement>
            </titledetail>
        </collection>
        <titledetail>
            <b202>01</b202>
            <titleelement>
                <x409>01</x409>
                <b203>{booktitle}</b203>
            </titleelement>
        </titledetail>
        <contributor>
            <b034>1</b034>
            <b035>B01</b035> <!-->A:author B:editor</!-->
            <b036>{lastname} {firstname}</b036>
            <b037>{firstname}, {lastname}</b037>
            <b039>{lastname}</b039>
            <b040>{firstname}</b040>
            <b044>{biosketch}</b044>
        </contributor>
        <b057>{editionnumber}</b057>
        <language>
            <b253>01</b253>
            <b252>{bookmetalanguagecode}</b252>
        </language>
        <extent>
            <b218>11</b218>
            <b219>{numberofpages}</b219>
            <b220>03</b220>
        </extent>
        <subject>
            <x425/>
            <b067>26</b067>
            <b068>2.0</b068>
            <b069>1560</b069>
            <b070>Hardcover, Softcover / Sprachwissenschaft, Literaturwissenschaft</b070>
        </subject>
        <subject sourcename="Publisher">
            <x425/>
            <b067>93</b067>
            <b068>1.6</b068>
            <b069>CF</b069>
            <b070>Sprachwissenschaft, Linguistik</b070>
        </subject>
        <subject>
            <b067>20</b067>
            <b070>{keyword}</b070>
        </subject>
        <b207>Wissenschaft</b207>
        <EpubLicense>
            <EpubLicenseExpression>
                <EpubLicenseExpressionLink>{license_url.lower()}</EpubLicenseExpressionLink>
            </EpubLicenseExpression>
        </EpubLicense>
    </descriptivedetail>
    <collateraldetail>
        <textcontent>
            <x426>03</x426>
            <x427>00</x427>
            <d104 textformat="06" language="eng">{blurb}</d104>
        </textcontent>
        <textcontent>
            <x426>20</x426> <!-->Open access statement </!-->
            <d103>06</d103>
            <d104>Der Titel ist Open Access unter der Creative Commons Lizenz {license} 4.0</d104>
        </textcontent>
    </collateraldetail>
    <publishingdetail>
        <publisher>
            <b291>01</b291>
            <publisheridentifier>
                <x447>05</x447>
                <b244>5295526</b244>
            </publisheridentifier>
            <b081>Language Science Press</b081>
        </publisher>
        <b209>Berlin</b209>
        <b083>DE</b083>
        <productcontact>
            <x482>10</x482>
            <x484>LangSci Press gUG</x484>
            <x299>Sebastian Nordhoff</x299>
            <j272>sebastian.nordhoff@langsci-press.org</j272>
            <x552>Bänschstr. 29</x552>
            <j349>Berlin</j349>
            <x590>10247</x590>
            <b251>DE</b251>
        </productcontact>
        <b394>04</b394>
        <publishingdate>
            <x448>01</x448>
            <b306 dateformat="00">{publishingdateyymmdd}</b306>
        </publishingdate>
    </publishingdetail>
    <productsupply>
        <supplydetail>
            <supplier>
                <j292>01</j292>
                <supplieridentifier>
                    <j345>05</j345>
                    <b244>5295526</b244>
                </supplieridentifier>
                <j137>Language Science Press</j137>
            </supplier>
            <j396>20</j396> <!--availability-->
            <UnpricedItemType>01</UnpricedItemType>
        </supplydetail>
    </productsupply>
</product>
</ONIXmessage>
"""
with open(f"proquest_onix3/{isbn_digital}.xml", "w") as xmlout:
    # validate XML
    # ET.fromstring(proquest_template)
    # xmlout.write(proquest_template)
    # print(onix3_template)
    # ET.fromstring(onix3_template)
    # xmlout.write(onix3_template)
    ET.fromstring(onix_vlb_template)
    xmlout.write(onix_vlb_template)
