# -*- coding: utf-8 -*-
import glob
import re 
import os
import BeautifulSoup
import sys
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mplcolors
import pprint

class Book():
  def __init__(self, ID, title, colors, shapes, category):
    seed = hash(str(ID)+'a')+14
    self.ID = int(ID)
    self.title = title 
    self.category = category  
    self.downloads = {}
    self.color = colors[seed%len(colors)]
    self.shape = shapes[seed%len(shapes)]    
  

  def computeYAggregates(self,labels,threshold):    
    basis = [self.downloads.get(label,0) for label in labels]
    aggregate = [sum(basis[0:i+1]) for i,el in enumerate(basis)]
    #aggregate = [(a if a>threshold else 0) for a in aggregate]    
    aggregate = self.zeros2nones(aggregate)
    self.yaggregates =  aggregate
    #print self.ID, self.yaggregates
  
  def zeros2nones(self,a):
    result = []
    for i,e in enumerate(a):
      try:
        if a[i+1]==0:
          result.append(None)
        else:
          result.append(e)
      except IndexError:
          result.append(e)
    return result
          
          
      
  
class Catalog():
  def __init__(self):
    #read ID and title of books from file
    #print "reading", booksfile
    #lines = open(booksfile).read().decode('utf8').split('\n') 
    #self.booksfile = booksfile 
    #setup colors and shapes to select from
    colors = plt.cm.Set1(np.linspace(0, 1, 45))  
    shapes = 'v^osp*D'  
    self.booklist = {
      #(ID,title)
      '10000':{
                22:      u"The Alor-Pantar languages¹",
                25:      u"Grammatical theory¹",
                46:      u"Einführung in die grammatische Beschreibung¹",
                76:      u"New directions in corpus-based translation studies",
                81:      u"The future of dialects",
                101:     u"Einführung in die grammatische Beschreibung²",
                121:     u"Diversity in African languages",
                151:     u"On looking into words",
                157:     u"The Alor_Pantar languages²",
                160:     u"A aquisição de língua materna e não materna",
                195:     u"Grammatical theory²",
                25195:   u"Grammatical theory",
                46101:   u"Einführung in die grammatische Beschreibung",
                46101224:   u"Einführung in die grammatische Beschreibung",
                22157:   u"The Alor-Pantar languages",
                },
      '4000':{
                144231: u"Analyzing meaning",
                17:  u"A grammar of Pite Saami",
                48:  u"Natural causes",
                49:  u"The Talking Heads experiment",
                66:  u"A grammar of Yakkha",
                75:  u"Linguistic variation, identity construction and cognition",
                88:  u"Thoughts on grammaticalization",
                89:  u"The empirical base of linguistics",
                91:  u"Roots of language",
                94:  u"Advances in the study of Siouan",
                96:  u"Dependencies in language",
                107: u"New perspectives on cohesion and coherence: Implications for translation",
                108: u"Eyetracking and Applied Linguistics",
                115: u"Order and structure in syntax II",
                120: u"African linguistics on the prairie",
                132: u"Empirical modelling of translation and interpreting",
                144: u"Analyzing meaning",
                156: u"Further investigations into the nature of phrasal compounds",
                159: u"Order and structure in syntax I",
                173: u"Diachrony of differential argument marking",
                181: u"Quality aspects in institutional translation",
                224: u"Einführung in die grammatische Beschreibung³"
                },
      '1000monographs':{
                16:  u"Prosodic Detail in Neapolitan Italian",
                18:  u"A typology of marked-S languages",
                20:  u"Syntax und Valenz",
                67:  u"A grammar of Mauwake",
                73:  u"Grammaticalization in the North",
                78:  u"A grammar of Papuan Malay",
                82:  u"A grammar of Palula",
                83:  u"A grammar of Yauyos Quechua",
                50:  u"How mobile robots can self-organize a vocabulary",
                52:  u"The evolution of case grammar",
                53:  u"The evolution of grounded spatial language",
                97:  u"Die Sprachwissenschaft",
                98:  u"The Ik Language",
                109: u"Tone in Yongning Na",
                141: u"The Verb in Nyakyusa",
                153: u"The semantic transparency of English compound nouns",
                124: u"A grammar of Rapa Nui",
                19:  u"Adjective attribution",
                51:  u"Language strategies for the domain of colour",
                27:  u"Grammaire des constructions elliptiques ",
                74:  u"A dictionary and grammatical outline of Chakali",
                143: u"Sémantique formelle: Volume 1",
                176: u"The Unicode cookbook",
               },
      'editedvolumes': {
                102: u"Crossroads between contrastive linguistics, translation studies and machine translation",
                103: u"Annotation, exploitation and evaluation of parallel corpora",
                106: u"Language technologies for a multilingual Europe",
                152: u"Unity and diversity in grammaticalization scenarios",
                157: u"The Alor-Pantar languages²",
                165: u"The lexeme in descriptive and theoretical morphology ",
                167: u"On this and other worlds",
                180: u"Learning context effects",
                182: u"The languages of Malta",
                183: u"Methods in prosody: A Romance language perspective",
                184: u"Multiword expressions: Insights from a multi-lingual perspective",
                189: u"Advances in formal Slavic linguistics 2016",
                190: u"East Benue-Congo: Nouns, pronouns, and verbs",
                199: u"René de Saussure and the theory of word formation",
                201: u"Perspectives on information structure in Austronesian languages",
                204: u"Multiword expressions at length and in depth: Extended papers from the MWE 2017 workshop",
                209: u"Interpreting and technology",
                },
        'monographs': {
                44:  u".",
                85:  u"A grammar of Pichi",
                111: u"Modeling information structure in a cross-linguistic perspective ",
                116: u"Sprachliche Imitation",
                118: u"A grammar of Moloko",
                123: u"Attributive constructions in NENA",
                134: u"Absolute Komplexität in der Nominalflexion",
                137: u"Tonal placement in Tashlhiyt",
                149: u"Beiträge zur deutschen Grammatik",
                154: u"Dynamische Modellierung",
                155: u"Morphologisch komplexe Wörter",
                163: u"A lexicalist account of argument structure",
                174: u"A typology of questions in Northeast Asia",
                175: u"Distribution und Interpretation von Modalpartikel-Kombinationen",
                187: u"Can integrated subtitles improve the viewing experience",
                191: u"The numeral system of Proto-Niger-Congo",
                193: u"Deletion phenomena in comparative constructions",
                195: u"Grammatical theory²",
                196: u"Problem solving activities",
                203: u"The acrolect in Jamaica",
                210: u"Sound change, priming, salience",
                212: u"A grammar of Komnzo",
                231: u"Analyzing meaning²"
                }     
        }
    self.books = {} 
    for category in self.booklist:
      for ID in self.booklist[category]: 
        self.books[ID] = Book(ID, self.booklist[category][ID], colors, shapes, category)
    #collect all directories with access information
    self.dirs = glob.glob('webreport_langsci-press.org_catalog_20[0-9][0-9]_[01][0-9]')
    #extract access data from all log files
    self.monthstats = dict([(d[-7:], Stats(os.path.join(d,'awstats.langsci-press.org.urldetail.html')).getBooks()) for d in self.dirs]) 
    #pprint.pprint(self.monthstats)
    aggregationdictionary = {}
    for bID in self.books:
      aggregationdictionary[int(bID)] = {}   
    #print aggregationdictionary
    lastmax = []
    for month in sorted(self.monthstats.keys()):  
      monthmaxs = []
      monthfactor = 1 #correctionfactor for incomplete logs
      if month == "2016_05": #in May 2016, only 24/31 days were logged
        monthfactor = 1.3        
      if month == "2016_06": #in June 2016, only 15/30 days were logged
        monthfactor = 2      
      for book in self.monthstats[month]:
        if int(book) == 94 and month == "2016_05": #book 94 was published mid-may, hence the factor is 16/8 and not 31/24
            monthfactor = 2
        if int(book) == 49 and month == "2018_03": #book 49 had grossly inflated downloads in March 2018
            monthfactor = .005
        effectivedownloads = int(self.monthstats[month][book]*monthfactor) 
        monthmaxs.append((effectivedownloads,book))
        if int(book) in self.books: #only aggregate books relevant for this category
          try: 
            aggregationdictionary[book][month] = effectivedownloads
          except KeyError:          
            aggregationdictionary[book][month] = 0       
      lastmaxs = monthmaxs
      #take care of second editions       
      secondeditions = [(46,101,224),(25,195),(22,157),(144,231)] 
      for title in secondeditions:
        editiondownloads = []
        newkey = int(''.join([str(x) for x in title]))
        for edition in title:
            try:
                editiondownloads.append(aggregationdictionary[edition][month])
            except KeyError:
                pass
        combineddownloads = sum(editiondownloads)
        try:
            aggregationdictionary[newkey][month] = combineddownloads
        except KeyError:
            aggregationdictionary[newkey] = {}                
            aggregationdictionary[newkey][month] = combineddownloads
    try:  
      aggregationdictionary[52]["2016_06"] = 48 #logging was off in that month
    except KeyError:
      pass    
    try:  
      aggregationdictionary[53]["2016_06"] = 84 #logging was off in that month   
    except KeyError:
      pass
    for bookID in aggregationdictionary: 
      try:
        self.books[bookID].downloads = aggregationdictionary[bookID]
      except KeyError:
          if bookID>1000: #secondedition 
              print(bookID)
              self.books[bookID] = Book(bookID,str(bookID),plt.cm.Set1(np.linspace(0, 1, 45)),'v^osp*D','10000')      
    for x in sorted(lastmaxs)[::-1][:3]:
        title = "??"
        try:
            title =  self.books[x[1]].title
        except KeyError:
            pass
        print ' ', x[1], title , x[0]
    self.countrystats = dict([(d[-7:],CountryStats(os.path.join(d,'awstats.langsci-press.org.alldomains.html')).getCountries()) for d in self.dirs])   
        
  def setupPlot(self, labels, timeframe):  
    fig = plt.figure()
    #use a wide picture
    fig.set_figwidth(12)
    #fig.add_subplot(ax)
     
    plt.rc('legend',**{'fontsize':9})
    plt.xticks(range(len(labels)+1)[-timeframe:], [l[-5:].replace('_','/') for l in labels[-timeframe:]], fontsize = 10) 
    
    #fig.patch.set_visible(False)
    #ax.axis('off')
    return fig, plt
  
  def matplotcumulative(self, typ='',ID=False, legend=True, fontsizetotal=15, threshold=99, timeframe=13, excludes=[]):
    category = typ
    """
    produce cumulative graph
    
    Aggregate cumulative data for time sequence.
    Plot this data with matplotlib.
    Also plot all individual books
    """
    
    #sort the keys so we get them in temporal order
    labels = sorted(self.monthstats.keys())    
    #setup matplot 
    fig, plt = self.setupPlot(labels,timeframe)
    ax = plt.subplot(111)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    ax.set_ylabel('downloads')
    ax.set_xlabel('months')   
      
    #displaylimit = timeframe
    origlabels = labels
    
    aggregatedownloads = 0    
    graphs = 0
    for bookID in self.books:
      self.books[bookID].computeYAggregates(labels, threshold)
      
    #cumulative plot  
    print "plotting", typ
    for bookID in sorted(self.books.keys(), key=lambda k: self.books[k].yaggregates[-1],reverse=True): 
      book = self.books[bookID]
      if bookID in excludes: 
          #we exclude all books with multiple editions
          #the complete aggregates will still be correct since the combined editions will be counted
          continue
      if bookID not in self.booklist[category]:
        continue
      print bookID,
      #compute total download data over all books
      try:
        totaldownloads = book.yaggregates[-1]
        aggregatedownloads +=  totaldownloads
        graphs += 1
      except TypeError: #no download data
        pass
      if book.yaggregates[-1]<30: #make sure no test or bogus data are displayed
        continue            
      xs = range(len(labels)+1)[-timeframe-1:] + [None]
      ys = book.yaggregates[-timeframe-1:] + [None]
      #plot line
      ax.plot(xs, ys, color=book.color, linewidth=1.5) 
      #plot marks
      ax.plot(xs, ys, book.shape, color=book.color, label="(%s) %s" % (ys[-2], book.title[:45])) 
    print ""  
    #position legend box
    if legend:
      box = ax.get_position()
      ax.set_position([box.x0, box.y0, box.width * 0.66, box.height]) 
      if graphs == 0:
        graphs = 1
      stretchfactor=25/graphs
      ax.legend(loc='center left', bbox_to_anchor=(1, 0.5),frameon=False,numpoints=1,labelspacing=stretchfactor)     
    #save file
    plt.savefig('cumulativeall%s.svg'%category)
    plt.savefig('cumulativeall%s.png'%category)
    plt.close(fig)    
    plt.cla()      
    #print "plotted cumulative graph"
    print "total downloads of all %s:"%category, aggregatedownloads    
    #print "plotting invididual graphs: "
    
    #individual plots
    for bookID in self.books:
      book = self.books[bookID]
      if book.yaggregates[-1]<30: #only generate graphics for books with sizable downloads
        continue      
      bookfig, bookplt = self.setupPlot(labels,timeframe)      
      bookax = plt.subplot(111)
      bookax.spines['right'].set_visible(False)
      bookax.spines['top'].set_visible(False)
      bookax.yaxis.set_ticks_position('left')
      bookax.xaxis.set_ticks_position('bottom')
      bookax.set_ylabel('downloads')
      bookax.set_xlabel('months')           
      xs = range(len(labels)+1)[-timeframe-1:] + [None]
      ys = book.yaggregates[-timeframe-1:] + [None]
      totaldownloads = book.yaggregates[-1]
      #plot line
      bookax.plot(xs, ys, color=book.color, linewidth=1.5) 
      #plot marks
      bookax.plot(xs, ys, book.shape, color=book.color, label="%s" % (ys[-2])) 
      #add number at end of graph
      bookax.text(len(origlabels), totaldownloads, '      %s'%totaldownloads, fontsize=12)       
      bookplt.savefig('%s.svg'%bookID)
      bookplt.savefig('%s.png'%bookID)
      bookplt.close(fig)   
      bookplt.cla()      
      #print bookID,  
    #print ''
    return aggregatedownloads
   
  def plotCountries(self,threshold=12, typ=''):
    """
    Produce a pie chart of downloads per country.
    $threshold countries will be named, the rest
    will be aggregated as "other"
    """
    
    aggregationdictionary = {}
    for month in self.countrystats:
      monthdictionary = self.countrystats[month]
      monthfactor = 1 #correctionfactor for incomplete logs
      if month == "2016_05": #in May 2016, only 24/31 days were logged
        monthfactor = 1.3        
      if month == "2016_06": #in June 2016, only 15/30 days were logged
        monthfactor = 2    
      for country in monthdictionary:
        try:
          aggregationdictionary[country] += int(int(monthdictionary[country].replace(',',''))*monthfactor)
        except KeyError:
          aggregationdictionary[country] = int(int(monthdictionary[country].replace(',',''))*monthfactor)
        except ValueError:
          pass
          
    #for k in aggregationdictionary:
      #print k, aggregationdictionary[k]
    #get list of countries and downloads
    list_ = [(k,aggregationdictionary[k]) for k in aggregationdictionary]        
    #sort list by number of downloads
    list_.sort(key=lambda x: x[1], reverse=True) 
    #compute values for named countries and "other"
    values = [t[1] for t in list_][:threshold]+[sum([t[1] for t in list_][threshold:])]  
    #set labels for named countries and "other"
    labels = ['%s: %s'%t for t in list_][:threshold]+['Other:%s'%values[-1]]
    #for i in range(threshold+1,len(labels)):
      #labels[i]=''
    #print labels, values
    cmap = plt.get_cmap('Paired')
    colors = [cmap(i) for i in np.linspace(0, 1, threshold+1)]
    #setup matplot 
    fig = plt.figure()
    plt.axis("equal") 
    fig.set_figwidth(12)
    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.66, box.height]) 
    plt.pie(values, labels=labels, colors=colors, labeldistance=1.4)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5),frameon=False,numpoints=1) 
    plt.savefig('%scountries.png'%typ) 
    plt.savefig('%scountries.svg'%typ) 
    plt.close(fig)
    #plt.cal(fig)
    
    
  def dumpcsv(self): 
        maxID = max([self.books[book].ID for book in self.books if self.books[book].ID<1000]) 
        columnheaders = [x for x in range(maxID+1)]
        columnheaders[0] = '' 
        rows = [columnheaders]
        for month in sorted(self.monthstats):
            row = [0 for x in range(maxID+1)]
            row[0] = month
            for book in self.books: 
                if book in self.monthstats[month]:
                    row[book] = self.monthstats[month][book] 
            rows.append(row)
        out = open('langscidownloads.csv','w')        
        for row in rows:
            out.write(','.join([str(x) for x in row]))
            out.write('\n')
        out.close()
        
  def plot(self):
      multipleditions =(22,25,46,101,157,195,224,144,231)  
      for category in self.booklist:
        catalog.matplotcumulative(fontsizetotal=7, typ=category, excludes=multipleditions)   
  
        
              
          
      
         
class Stats():
  def __init__(self,f):
    """
    navigate the html file to find the relevant <td>s and
    create a dictionary mapping urls to download figures
    """
    
    self.hits = dict(
                      [
                        (
                          #locate key
                          tr.findAll('td')[0].text,
                          #remove thousands separator and convert value to int
                          int(tr.findAll('td')[1].text.replace(',',''))
                        ) 
                        for tr in BeautifulSoup.BeautifulSoup(open(f))\
                                              .find('table',attrs={'class':'aws_data'})\
                                              .findAll('tr')[1:]
                      ]
                  )    


    
  def getBooks(self):
    """
    analyze the access data and aggregate stats for books across publication formats
    """
    
    aggregationdictionary = {}
    for k in self.hits:
      if 'view' in k: #ignore /download/, which is used for files other than pdf
        i=0
        try:
          #extract ID
          i = int(re.search('view/([0-9]+)',k).groups()[0])
        except AttributeError:
          #print "no valid book key in %s" %k
          continue
        try:
          #accumulate figures for the various publication formats
          aggregationdictionary[i] += self.hits[k]
        except KeyError:
          aggregationdictionary[i] = self.hits[k]
    return aggregationdictionary
    
        
  def getCountries(self):
    """
    analyze the access data and aggregate stats for countries
    """
    
    aggregationdictionary = {}
    for k in self.hits: 
      try:
        #accumulate figures for the various publication formats
        aggregationdictionary[k] += self.hits[k]
      except KeyError:
        aggregationdictionary[k] = self.hits[k] 
    return aggregationdictionary

   
class CountryStats(Stats):
  def __init__(self,f):
    """
    navigate the html file to find the relevant <td>s and
    create a dictionary mapping urls to download figures
    """		  
    self.hits = dict(
                    [
                      (
                        #locate key
                        tr.findAll('td')[2].text,
                        #remove thousands separator and convert value to int
                        tr.findAll('td')[4].text
                      ) 
                      for tr in BeautifulSoup.BeautifulSoup(open(f))\
                                              .find('table',attrs={'class':'aws_data'})\
                                              .findAll('tr')[1:]
                    ]
                    )  

                    
if __name__=='__main__':
  totaldownloads = 0
  catalog = Catalog()
  catalog.dumpcsv()
  catalog.plot()
  print "created png and svg files"
  #print "total downloads combined", totaldownloads
  
  #print "country plot"
  #catalog.plotCountries(threshold=20,typ='all')
  