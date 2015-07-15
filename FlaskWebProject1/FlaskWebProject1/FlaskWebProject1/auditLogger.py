from __future__ import print_function
import pypyodbc
import collections
import datetime
import itertools
import copy
import os
import Plotter
import SQLclient


#class that manages all connections to the database
class auditLog():

    #initialize the class by connecting to the database, get the cursor and either initialize the aggrigate tables or get info from them. 
    def __init__(self):
        self.connection = SQLclient.connect_to_DB()
        self.cursor = self.connection.get_cursor()
        #self.connection.create_agg()
        #self.connection.create_agg_for_func_speed()
        self.data_gogn = SQLclient.data(self.cursor)
    
    #update the aggregate tables and the self data
    def updateAggTables(self):
        self.data_gogn = SQLclient.data(self.cursor)

    #getInfo is a function that gets data for service sites and formats the data for Highcharts.
    def getInfo(self, service, date1, date2, span):

        #get the data
        data = SQLclient.getStats(self.cursor,service, date1, date2, span)

        #format data
        names = Plotter.plotCCinfo(data,date1,date2,span)
        return names
    
    #function that loads new data into the DB for test purposes
    def loadNewDataIntoTable(self):
        SQLclient.loadNewData(self.cursor)

        self.data_gogn = SQLclient.data(self.cursor)

    #function that closes the DB connection
    def closeConnection(self):
        self.cursor.close()
        self.connection.connection.close()

    #function that gets all available services
    def getServices(self):
        services = SQLclient.getServices(self.cursor)
        return services

    #function that gets data for the Detail graph on a specific service site
    def getDetail(self, date, service, function):

        #gets data according to the service name, function name within that service and the date requested
        data = SQLclient.getDetails(self.cursor, date, service, function)
        return data

    #function that gets data for the outer pie chart for the mainpage, this function also sees to that the data is formated
    def getNewPie(self, span):

        #get the data from the DB
        data = SQLclient.getNewPieData(self.cursor, span)

        #format the data for Highcharts
        pie_gogn = Plotter.prepare_pie(data)
        return pie_gogn

    #function that gets the data for the inner chart
    def getNumPie(self, span):
        data = SQLclient.getNumPie(self.cursor, span)
        return data

    #function to get a new point for the front page
    def getRealTime(self, date, service):
        data = SQLclient.getRealTimeData(self.cursor, date, service)
        return data

    #get all the initialdata for the front page. this function stores that data in this object
    def getInitialRealTime(self):

        #date for the query
        now = datetime.datetime.now()
        thenTemp = now - datetime.timedelta(hours = 10*24)
        then = thenTemp.strftime("%Y-%m-%d %H:%M")

        data = SQLclient.getInitialRealTime(self.cursor, then)

        self.initdata = data

