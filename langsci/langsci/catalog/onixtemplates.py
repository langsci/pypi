romanistentemplate = """
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


proquest_creator_template = """
        <Contributor>
        <SequenceNumber>%s</SequenceNumber>
        <ContributorRole>%s</ContributorRole>
        <NamesBeforeKey>%s</NamesBeforeKey>
        <KeyNames>%s</KeyNames>
        <BiographicalNote>%s</BiographicalNote>
      </Contributor>

"""


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
    <RecordReference>langsci-press.org/{metadata['bookid']}</RecordReference>
    <NotificationType>03</NotificationType>
    <RecordSourceType>01</RecordSourceType>
    <RecordSourceIdentifier>
      <RecordSourceIDType>05</RecordSourceIDType>
      <IDValue>978-3-98554</IDValue>
    </RecordSourceIdentifier>
    <RecordSourceName>Language Science Press</RecordSourceName>
    <ProductIdentifier>
      <ProductIDType>06</ProductIDType>
      <IDValue>{book_DOI}</IDValue>
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
          <CollectionSequenceNumber>9</CollectionSequenceNumber>
        </CollectionSequence>
      </Collection>
      <TitleDetail>
        <TitleType>01</TitleType>
        <TitleElement>
          <TitleElementLevel>01</TitleElementLevel>
          <TitleText textcase="01">{metadata['title']}</TitleText>
          <Subtitle>{metadata['booksubtitle']}</Subtitle>
        </TitleElement>
        <TitleElement>
          <TitleElementLevel>02</TitleElementLevel>
          <TitleText textcase="02">{metadata['series']}</TitleText>
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
        <SubjectCode>{metadata['scheme'][1]}</SubjectCode>
      </Subject>
      <AudienceCode>06</AudienceCode>
      <EpubLicense>
        <EpubLicenseExpression>
          <EpubLicenseExpressionLink>https://creativecommons.org/licenses/by/4.0</EpubLicenseExpressionLink>
        </EpubLicenseExpression>
      </EpubLicense>
    </DescriptiveDetail>
    <CollateralDetail>
      <TextContent>
        <TextType>03</TextType>
        <ContentAudience>00</ContentAudience>
        <Text textformat="05">
          {metadata['blurb']}
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
          <ResourceLink>https://langsci-press.org/$$$call$$$/submission/cover/cover?submissionId={metadata['bookid']}</ResourceLink>
        </ResourceVersion>
      </SupportingResource>
      <TextContent>
        <TextType>47</TextType>
        <Text>This text is licenced as CC-BY 4.0</Text>
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
    <UnpricedItemType>01</UnpricedItemType>
    <othertext>
            <d102>47</d102>
            <d103>06</d103>
            <d104>Der Titel ist Open Access unter der Creative Commons Lizenz BY 4.0</d104>
  </othertext>
    <othertext>
            <d102>46</d102>
            <d103>01</d103>
            <d104>https://creativecommons.org/licenses/by/4.0/</d104>
  </othertext>
  </Product>
</ONIXMessage>"""
