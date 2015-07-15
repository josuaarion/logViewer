import xml.etree.ElementTree as ET
import urllib2, StringIO
import time

def checkServices():

    services = [
        ['http://internetbackend.arionbanki.is/CoreCollateralsServiceHost/StatusVerification/Report.xml','IsIT.Core.Collaterals.Services.Schema20150301','collateral'],
        ['http://internetbackend.arionbanki.is/CoreAccountsServiceHost/StatusVerification/Report.xml','IsIT.Core.Accounts.Services.Schema20131201','accounts'],
        ['http://internetbackend.arionbanki.is/CoreCreditCardsServiceHost/StatusVerification/Report.xml','CreditCardService','creditcards'],
        ['http://internetbackend.arionbanki.is/CoreLoansServiceHost/StatusVerification/Report.xml','IsIT.Core.Loans.Services.Schema20141201','loans']    
    ]


    roots = getRoots(services)

    flags = []
    counter = 0
    for root in roots[0]:
        flag = True
        for child in root:
            
            if child.tag == 'check':

                if child.attrib['status'] == 'Unsuccessful' or child.attrib['status']=='RuntimeFault':
                    flag = False
        flags.append([flag,services[counter][1],services[counter][0],services[counter][2]])
        counter +=1
    


    return flags

def getRoots(services):
    trees = []
    roots = []

    for i in range(0,len(services)):

        page_with_xml = urllib2.urlopen(services[i][0])
        io_xml = StringIO.StringIO()
        io_xml.write(page_with_xml.read())
        io_xml.seek(0)
        trees.append(ET.parse(io_xml))
        roots.append(trees[i].getroot())

    return [roots]