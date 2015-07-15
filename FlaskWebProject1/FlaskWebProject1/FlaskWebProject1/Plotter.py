from __future__ import print_function
from __future__ import division
import pypyodbc 
import collections
import datetime
import itertools
import copy
import os
from datetime import date
from hashtable import HashTable

#function to format the data for the pie chart, for HighChart
def prepare_pie(result_set):

    #variable to calculate percentages later
    total_calls = 0;

    #container for the total calls of each function
    calls_for_functions = {}

    #create a dictionary for the number of calls to functions of services and also keep track of total_calls
    for tuple in range(1,len(result_set)):
        total_calls = total_calls + result_set[tuple][0]
        if result_set[tuple][1] not in calls_for_functions:
            calls_for_functions[result_set[tuple][1]] = result_set[tuple][0]
        
        calls_for_functions[result_set[tuple][1]] = calls_for_functions[result_set[tuple][1]] + result_set[tuple][0]

    total_calls = total_calls + result_set[tuple][0]

    #in some situations we need to combine data to get the right figures
    try:
        #combine services 
        calls_for_functions['CreditCardService'] = calls_for_functions['CreditCardService'] + calls_for_functions['CreditCardsService']
        calls_for_functions['PublicCreditCards'] = calls_for_functions['PublicCreditCards'] + calls_for_functions['PublicCreditCardsService']

        #delete the unneccicary services
        del calls_for_functions['']
        del calls_for_functions['PublicCreditCardsService']
        del calls_for_functions['CreditCardsService']
    except KeyError:
    	print ("Key does not exist!")


    #container for the percentage of each service
    percentage_for_service = {}
    
    #find the percentage of each service
    for key in calls_for_functions:
        percentage_for_service[key] = ((calls_for_functions[key]/total_calls)*100)
     
    #transfer data from precentage_for_service to the array ser_per that is then returned, also this
    #loop deletes services that have too little percentage
    ser_per = []
    for key in calls_for_functions:
        if percentage_for_service[key] > 0.1:
            temp = [key,percentage_for_service[key]]
            ser_per.append(temp)

    return(ser_per)

#function to get a date span from a data and a span, this function then returns two dates with the interval of 'span'
def createTimeDeltas(date,span):

    date1 = datetime.date(int(date[:4]), int(date[5:7]), int(date[8:10]))
    date2 = date1  - datetime.timedelta(int(span)*365/12)
    return [date2, date1]

#function that helps with the formatting of data for the function plotCCinfo(). it does this by filling 
# in missing dates in the sorted data with 0. 
def formatDataForPlot(dateInterval, sortedData, span):

    #start by creating empty arrays for the data and and names. this is later returned
    data = [None]*sortedData[1]
    names = [None]*sortedData[1]
    stats = [None]*sortedData[1]

    #go through the loop for each name
    for j in range(0,sortedData[1]):
        
        #hash table for data entry
        HT = HashTable(int(span)*365/12)
        
        #container for the final data
        xdata=[]

        #the start date--(current date)
        tempdate = dateInterval[0]

        #loop that goes through each day and fills it in with 0
        while tempdate < dateInterval[1]:

            #id for the hash table
            ID = hash(str(tempdate)[:4]+str(tempdate)[5:7]+str(tempdate)[8:10])

            #fill inn the day with 0
            HT.put(ID,0.0)

            #increment current date
            tempdate = tempdate + datetime.timedelta(days = 1)
        
        #for loop that goes through all the dates in the result set and sets the data for those dates 
        for i in range(0,len(sortedData[0][j])):

            value = float(sortedData[0][j][i][1])
            date = sortedData[0][j][i][3]
            ID = hash(date[:4]+date[5:7]+date[8:10])
            HT.put(ID,value)
        
        tempdate = dateInterval[0]

        #values to find out the min, max, and avr
        tempMax = -1000000000000
        tempMin = 1000000000000
        sum = 0
        count = 0
        tempAVR = 0

        #a loop that gets all the values for all the days in the span and puts it into an array
        while tempdate < dateInterval[1]:

            count += 1

            ID = hash(str(tempdate)[:4]+str(tempdate)[5:7]+str(tempdate)[8:10])

            data32 = HT.get(ID)
            if data32 > tempMax:
                tempMax = data32

            if data32 < tempMin:
                tempMin = data32
            
            sum += data32

            xdata.append(data32)
            tempdate = tempdate + datetime.timedelta(days = 1)
        
        tempAVR = float(sum/float(count))
        AVR = "%.2f" % tempAVR
              
        #load the data into a new arrays
        data[j] = xdata
        names[j] = sortedData[0][j][0][0]
        stats[j] = [tempMax,tempMin,AVR]

    
    #return the formatted data
    return [data, names, stats]
        

#function that formats the data for the service sites. this function formats the data for the speed and the number of function calls 
#for each function in the main chart of the service sites.
def plotCCinfo(data, date1, date2,span):
    
    #container for the return data
    outputData = []
    
    #create date intervals for both the dates with the appropriate span
    dateInterval1 = createTimeDeltas(date1,span)
    dateInterval2 = createTimeDeltas(date2,span)
    
    #sort all the data into arrays
    sortedData1 = sortDataForpCCi(data[0])
    sortedData2 = sortDataForpCCi(data[1])
    sortedData4 = sortDataForpCCi(data[2])
    sortedData5 = sortDataForpCCi(data[3])

    #format the data by adding in missing values for missing dates in the data set
    xdata1 = formatDataForPlot(dateInterval1,sortedData1, span)
    xdata2 = formatDataForPlot(dateInterval2,sortedData2, span)
    xdata4 = formatDataForPlot(dateInterval1,sortedData4, span)
    xdata5 = formatDataForPlot(dateInterval2,sortedData5, span)



    #go through each function and create a datapacket object that holds the data and name of the function.
    #each packet looks like this: {data: [[speed1], [speed2], [numberOfCalls1], [numberOfCalls2]] name: nameoffunction}
    #these data packets are then loaded into the outputData array
    for i in range(0,min(len(xdata1[0]),len(xdata2[0]))):
        data666 = [xdata1[0][i],xdata2[0][i], xdata4[0][i], xdata5[0][i]]
        name = xdata1[1][i]
        stats = [xdata1[2][i],xdata2[2][i],xdata4[2][i],xdata5[2][i]]

        datapack = dataPacket(data666, name,stats) 
        outputData.append(datapack)
    
    #container for the names of functions
    names=[]

    #loop to get all the function names
    for i in range(0,len(outputData)):
        names.append(outputData[i].getName())
    
    #put the names at the back of the outputData array 
    outputData.append(names)

    return outputData

#class to hold data that is in the correct format for highcharts.
#this class is pretty self explanatory
class dataPacket():

    def __init__(self, data, funcName, stats):
        self.data = data
        self.funcName = funcName
        self.stats = stats

    def getData(self):
        return self.data

    def getName(self):
        return self.funcName

    def getStats(self):
        return self.stats

#a function for sorting the data from plotCCinfo(), this function returns an array that looks like this:
# [[[data for function 1],[data for function 2],...],number of functions,[function name 1, function name 2 ,...]]
def sortDataForpCCi(data):

    #containers for the final data
    numOfFunctions = 0
    listOfFunctions = []
    array = []

    #find all the different names for functions and update listoffuntions and numoffunctions accordingly. also create a container for each name in the array, array 
    for i in range(1,len(data)):

        if data[i][0] not in listOfFunctions:
            listOfFunctions.append(data[i][0])
            numOfFunctions = numOfFunctions +1
            array.append([])

    #fill out the containers within the array, array, with the appropriate data
    for i in range(1,len(data)):
        for j in range(0, len(listOfFunctions)):
            if data[i][0] == listOfFunctions[j]:
                array[j].append(data[i])

    #combine all the data in an array and return it
    resultData = [array,numOfFunctions,listOfFunctions]
    
    return resultData