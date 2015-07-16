import pypyodbc
import datetime
import random
import time
import threading

#Strings to be used to create the aggrigate tables
AggTable = """CREATE TABLE dbo.Aggrigate(TimeStamp datetime2(7),ServiceName varchar(100),count Integer, date varchar(10), functionName varchar(100));"""
AggTableForFuncSpeed = """CREATE TABLE dbo.Aggrigate_FuncSpeed(FunctionName varchar(100), ElapsedTime Integer, ServiceName varchar(100), DateOfAction varchar(10))"""

#function that performs the initial data query and also updates the aggrigate tables
def data(cursor):
    print('Performing initial queries...')
    
    #inital Queries:

    #Num_calls_per_service = """ SELECT  Count([FunctionName]) as count , B.ServiceName, cast(A.LogDate as date) as date,  [FunctionName]
    #FROM [CoreServices].[dbo].[tCoreServiceLog] A join [CoreServices].[dbo].[tCoreLoggingService] B on A.ServiceId = B.ServiceId
    #GROUP BY cast(A.LogDate as date),B.ServiceName, [FunctionName] """

    Num_calls_per_service = """declare @data datetime = (SELECT MAX(TimeStamp) FROM [CoreServices].[dbo].[Aggrigate])
    SELECT  COUNT(LogId) as count, ServiceName, cast(A.LogDate as date), A.FunctionName
    FROM [CoreServices].[dbo].[tCoreServiceLog] A join [CoreServices].[dbo].[tCoreLoggingService] B
    on A.ServiceId = B.ServiceId and A.LogDate > @data
    GROUP BY   ServiceName, cast(A.LogDate as date), A.FunctionName"""


    get_data_from_agg = """declare @date date = (SELECT GETDATE ( ))
    SELECT  A.count,  A.ServiceName, A.date
    FROM [CoreServices].[dbo].[Aggrigate] A
    WHERE A.date >= DATEADD(year, -500, @date)"""
    
    #til thess ad fa oll grunn gognin i agg speed tofluna.

    #speed_of_service = """ SELECT  FunctionName, AVG(DATEDIFF(MILLISECOND, T.StartTime, T.StopTime)) as elapsed, ServiceName,
    #cast(T.StartTime as varchar(10))
    #FROM [CoreServices].[dbo].[v_TotalElapsedTime] T
    #GROUP BY cast(T.StartTime as varchar(10)), FunctionName, ServiceName
    #ORDER BY cast(T.StartTime as varchar(10)) """

    speed_of_service = 	"""declare @maxdate varchar(10) = (SELECT MAX(DateOfAction) FROM [CoreServices].[dbo].[Aggrigate_FuncSpeed])
	declare @maxmax varchar(10) = (SELECT DATEADD(day, 1, DATEFROMPARTS( SUBSTRING(@maxdate,1,4), SUBSTRING(@maxdate,6,2), SUBSTRING(@maxdate,9,2))))
    SELECT  FunctionName, AVG(DATEDIFF(MILLISECOND, T.StartTime, T.StopTime)) as elapsed, ServiceName,
    cast(T.StartTime as varchar(10))
    FROM [CoreServices].[dbo].[v_TotalElapsedTime] T
    WHERE
    T.StartTime > @maxmax
    GROUP BY cast(T.StartTime as varchar(10)), FunctionName, ServiceName
	ORDER BY cast(T.StartTime as varchar(10))"""
    

    get_speed_from_agg = """declare @maxdate varchar(10) =(SELECT MAX(DateOfAction) FROM [CoreServices].[dbo].[Aggrigate_FuncSpeed])
    Select * From [CoreServices].[dbo].[Aggrigate_FuncSpeed]
    WHERE ServiceName = 'CreditCardService' AND DateOfAction > DATEADD(month, -1, @maxdate)"""
    
    #all inital queries
    queries = []

    #all initial queries for aggrigate tables
    A_queries = []

    #results of queries are stored in an array as classes. each class contains a result where each column is stored as an array
    queryResult = []

    #fill out the queries
    queries.append(Num_calls_per_service)
    queries.append(speed_of_service)

    #fill out the aggrigate queries
    A_queries.append(get_data_from_agg)
    A_queries.append(get_speed_from_agg)

    #for each query, load the appropriate result into queryResult. queryResault will be a 3d array that looks like this:
    #queryResault[ query ][row in resault ][column in row], NOTE!!!! the first row in each result contains the name of the columns for the resutl
    for i in range(0,len(queries)):
        print('Executing query #'+str(i))
        queryResult.append(get_data(queries[i], cursor))

        #check if the latest result from the query is empty. if so then i get the data from the aggrigate table...
        if len( queryResult[i]) < 2:
            queryResult[i] = get_data(A_queries[i], cursor)
            print(str(i)+' got data from aggrigate')
        else: 
            #...if not then i update the aggrigate tables and return the latest date from the aggrigate table
            print('Updating Aggrigate table for query...')
            latestData = update_data_from_query(queryResult[i], cursor, A_queries[i], i)
            queryResult[i]=latestData
            
        print(str(i)+' finished')
    return queryResult

#functions that gets the data for the chart on the service site. this data is gathered form the parameters service name, two dates and a time span
def getStats(cursor, service, date1, date2, span):

    #combine the services if needed
    if service == 'CreditCardService':
        service = """CreditCardService' OR ServiceName = 'CreditCardsService """
    elif service == 'PublicCreditCards':
        service = """ PublicCreditCardsService' OR ServiceName = 'PublicCreditCards """
    
    #container for the data
    data= []
    dates = [date1,date2]

    #query to get the time for the first date span
    query = """ declare @date1 varchar(10) = (SELECT DATEFROMPARTS( SUBSTRING('"""+dates[0]+"""',1,4), SUBSTRING('"""+dates[0]+"""',6,2), SUBSTRING('"""+dates[0]+"""',9,2)))
	Select * From [CoreServices].[dbo].[Aggrigate_FuncSpeed]
    WHERE (ServiceName = '"""+ service+ """') AND (DateOfAction >= DATEADD(month, -"""+str(span)+""", @date1) AND DateOfAction <= @date1)
    ORDER BY FunctionName, DateOfAction"""

    #get data from query and store the result in the data array 
    data.append(get_data(query,cursor))

    #query to get the time for the second date span
    query = """ 
	declare @date2 varchar(10) = (SELECT DATEFROMPARTS( SUBSTRING('"""+dates[1]+"""',1,4), SUBSTRING('"""+dates[1]+"""',6,2), SUBSTRING('"""+dates[1]+"""',9,2)))
    Select * From [CoreServices].[dbo].[Aggrigate_FuncSpeed]
    WHERE (ServiceName = '"""+ service+ """') AND (DateOfAction >= DATEADD(month, -"""+str(span)+""", @date2) AND DateOfAction <= @date2)
    ORDER BY FunctionName, DateOfAction"""

    #get data from query and store the result in the data array
    data.append(get_data(query,cursor))

    #get the number of function calls per day for the first date span
    query = """DECLARE @date date = '"""+date1+"""'
    DECLARE @date2 date = (SELECT DATEADD(month,-"""+str(span)+""", @date))
    SELECT   A.[functionName], sum(A.count) as count,  A.ServiceName, A.date
    FROM [CoreServices].[dbo].[Aggrigate] A
    WHERE A.date <= @date AND A.date >= @date2 AND (A.ServiceName = '"""+service+"""')
    GROUP BY A.date, A.ServiceName, A.functionName"""

    #get data from query and store the result in the data array
    data.append(get_data(query,cursor))

    #get the number of function calls per day for the first date span
    query = """DECLARE @date date = '"""+date2+"""'
    DECLARE @date2 date = (SELECT DATEADD(month,-"""+str(span)+""", @date))
    SELECT  A.[functionName], sum(A.count) as count,  A.ServiceName, A.date
    FROM [CoreServices].[dbo].[Aggrigate] A
    WHERE A.date <= @date AND A.date >= @date2 AND (A.ServiceName = '"""+service+"""')
    GROUP BY A.date, A.ServiceName, A.functionName"""
    
    #get data from query and store the result in the data array
    data.append(get_data(query,cursor))
    
    return data

#function to get the dates from datetime format onto string format in order to be able to use them better in the SQL query
def refactorDates(date1,date2):

    #break the dates down to the formats YYYY-MM-DD...
    year1 = date1[6:10]
    year2 = date2[6:10]

    month1 = date1[:2]
    month2 = date2[:2]

    day1 = date1[3:5]
    day2 = date2[3:5]

    #...and then put them back together into a string
    tempDate1 = year1+'-'+month1+'-'+day1
    tempDate2 = year2+'-'+month2+'-'+day2

    #load it into an array and return
    dates = [tempDate1,tempDate2]
    return dates

#function to get all the available services
def getServices(cursor):
    query = """  select ServiceName
    From [CoreServices].[dbo].[tCoreLoggingService] """ 

    data = get_data(query,cursor)

    #format the data
    FrmData = formatData(data)
    return FrmData

#make the data usable for the html parser
def formatData(data):

    #make the data into a list
    georg = map(list, data)

    #remove the first 4 items since the data is already available in other items
    del georg[0]
    del georg[0]
    del georg[0]
    del georg[0]

    #container for the formatted data
    formattedData = []

    #loop to take out all the ['']
    for i in range(0,len(georg)):
        formattedData.append(georg[i][0])

    #remove the forth item for the same reason as above
    del formattedData[4]

    return formattedData

#function that updates the aggrigate tables for the appropriate queryes
def update_data_from_query(newData, cursor, query, i):
    
    #this function works like this: we get new data (NewData) and in index (i) that tells us which query
    #the data belongs to and a query string (query) to query the appropriate aggrigate table. then we put the new 
    #data into the aggrigate table, after which we query the aggrigatetable and return that data

    #update the data for the pie chart aggrigate table
    if i == 0:
        updateAggrigate(cursor,newData)
        newData = get_data(query, cursor)
    elif i ==1: #update the data for the function time
        updateAggrigateforFuncSpeed(cursor, newData)
        newData = get_data(query, cursor)

    return newData

#class that connects to the database
class connect_to_DB():
     
    #set up the connection
    def __init__(self):

        print('Connecting to database')
        self.connection_string = r"DRIVER={SQL Server};SERVER=vissqlt2\dailyrestore;DATABASE=CoreServices;Trusted_Connection=True;"
        self.connection = pypyodbc.connect(self.connection_string)
        print('Connected')
        self.curr = self.connection.cursor()
        self.Creation_strings = [AggTable, AggTableForFuncSpeed]
    
    #get a query string that is used to create a table
    def get_creation_string(self,index):
        return self.Creation_strings[index]

    #function to create the main aggrigate table
    def create_agg(self):
        self.curr.execute(self.get_creation_string(0))
        self.curr.commit()

    #function to create the speed aggrigate table
    def create_agg_for_func_speed(self):
        query = self.get_creation_string(1)
        self.curr.execute(query)
        self.curr.commit()

    #function to get the cursor for the connection
    def get_cursor(self):
        return self.curr

    def close(self):
        self.curr.close()
        self.connection.close()
        print('connection closed')

#function that uses the cursor to connect to the database and perform a Query. then returns the result for that query
def get_data(Query, cursor):

    #execute query
    cursor.execute(Query)
   
    #containers for the results
    rows_from_query=[]
    titles_of_columns = []

    #go through the data from the result and get the titles of the columns
    for d in cursor.description: 
        titles_of_columns.append(d[0])

    #put the titles of columns into the result array
    rows_from_query.append(titles_of_columns)

    #go through the result and put into the result array row by row
    for row in cursor.fetchall():
        rows_from_query.append(row)

    return rows_from_query

#function that connects to the database and inserts values into the main aggrigate table
def updateAggrigate(cursor,data):

    #get timestamp
    dateNow = datetime.datetime.now()

    #go through the data and load it into the aggrigate table
    for i in range(1,len(data)):
        query = """INSERT INTO [CoreServices].[dbo].[Aggrigate](TimeStamp, ServiceName, count, date, functionName) VALUES(?,?,?,?,?)"""
        cursor.execute(query,(dateNow,data[i][1],data[i][0],data[i][2],data[i][3]))
    print('buid ad uppfaera gogn i aggrigate toflu')

    #commit the new data
    cursor.commit()
    
#function that connects to the database and inserts values into the speed aggrigate table
def updateAggrigateforFuncSpeed(cursor, data):

    #go through the data and load it into the aggrigate table
    for i in range(1,len(data)-1):
        query = """INSERT INTO [CoreServices].[dbo].[Aggrigate_FuncSpeed](FunctionName,ElapsedTime, ServiceName, DateOfAction) VALUES(?,?,?,?)"""
        cursor.execute(query,(data[i][0],data[i][1],data[i][2],data[i][3]))
    print('buid ad uppfaera gogn fyrir speed i aggrigate toflu')

    #commit the new data
    cursor.commit()

#function that connects to the database and gets data that is used in the details chart on the service sites, this function also formats the data.
#this function gets data for the parameters, service name, function name from the service provided and a date
def getDetails(cursor, date, service, function):

    #combine the services if needed
    if service == 'CreditCardService':
        service = """CreditCardService' OR ServiceName = 'CreditCardsService """
    elif service == 'PublicCreditCards':
        service = """ PublicCreditCardsService' OR ServiceName = 'PublicCreditCards """

    #query to get the numbers for the date
    query = """DECLARE @date datetime = ('"""+date+"""')
    SELECT  Count([FunctionName]) as count , DATEPART(HOUR, A.LogDate) as hour
    FROM [CoreServices].[dbo].[tCoreServiceLog] A join [CoreServices].[dbo].[tCoreLoggingService] B on A.ServiceId = B.ServiceId
	WHERE cast(A.LogDate as date) = @date  AND (B.ServiceName = '"""+service+"""') AND A.functionName = '"""+function+"""'
	GROUP BY DATEPART(HOUR, A.LogDate)"""

    #get data from query and store the result in the result_set array 
    result_set = get_data(query, cursor)

    #format the data for Highcharts
    frmData = formatDataForDetail(result_set)

    return frmData

#function to format data for the function: getDetails()
def formatDataForDetail(data):

    #containers for the data
    ALL = []
    hour = []
    number = []

    #seperate the data into two arrays...
    for i in range(1, len(data)):
        hour.append(data[i][1])
        number.append(data[i][0])

    #...and then combine them again in the ALL array and return that
    ALL.append(hour)
    ALL.append(number)

    return ALL

#function that gets data for the outer pie chart
def getNewPieData(cursor, span):

    #default value for the value
    value = 1

    #select the appropriate spann and value to get the correct query period
    spann = span 
    if span == 'day':
        spann = 'day'
    elif span == 'week':
        spann = 'day'
        value = 7
    elif span == 'month':
        spann = 'month'
    elif span == 'year':
        spann = 'year'
    else:
        spann = 'year'
        value = 500

    #query to get the count for services over a period
    query = """declare @date date = (SELECT GETDATE ( ))
    SELECT  A.count,  A.ServiceName, A.date
    FROM [CoreServices].[dbo].[Aggrigate] A
    WHERE A.date >= DATEADD("""+spann+""", -"""+str(value)+""", @date)
    GROUP BY A.ServiceName, A.count, A.date"""

    result_set = get_data(query, cursor)

    return result_set

#function that gets data fur the inner pie chart
def getNumPie(cursor, span):

    #default value for the value
    value = 1

    #select the appropriate spann and value to get the correct query period
    spann = span 
    if span == 'day':
        spann = 'day'
    elif span == 'week':
        spann = 'day'
        value = 7
    elif span == 'month':
        spann = 'month'
    elif span == 'year':
        spann = 'year'
    else:
        spann = 'year'
        value = 500

    #query to get number of functions for a specific service
    query = """declare @date date = (SELECT GETDATE ( ))
    SELECT  sum(A.count) as count,  A.[functionName], A.ServiceName
    FROM [CoreServices].[dbo].[Aggrigate] A
    WHERE A.date >= DATEADD("""+spann+""", -"""+str(value)+""", @date)
    GROUP BY A.ServiceName, A.functionName"""

    result_set = get_data(query, cursor)

    #format the data 
    data = formatThisData(result_set)

    return data

#function to format the data from the function: getNumPie()
def formatThisData(result_set):

    # a dictionary for the formatted data
    functions = {}

    #a loop to convert the result_set into a dictionary in the format: { servicename 1: {functionname 1: count, functionname 2: count, ...}, servicename 2: {...}...}
    for tuple in range(1,len(result_set)):

        if result_set[tuple][2] not in functions:
            
            functions[result_set[tuple][2]] = {}

        if result_set[tuple][1] not in functions[result_set[tuple][2]]:
            functions[result_set[tuple][2]][result_set[tuple][1]] = result_set[tuple][0]

    #for loop to combine the data for 'publiccreditcardservice' and 'creditcardservice'
    for item in functions:
        if item == 'PublicCreditCardsService':
            for dot in functions[item]:
                if dot not in functions['PublicCreditCards']:
                    functions['PublicCreditCards'][dot] = dot
                else:
                    functions['PublicCreditCards'][dot] = functions['PublicCreditCards'][dot] + functions[item][dot]
        if item == 'CreditCardsService':
            for dot in functions[item]:
                if dot not in functions['CreditCardService']:
                    functions['CreditCardService'][dot] = dot
                else:
                    functions['CreditCardService'][dot] = functions['CreditCardService'][dot] + functions[item][dot]

    #change the dictionary into a list again to make readable for Highcharts
    data_set=[]
    for item in functions:
        somfin = []
        somfin.append(item)
        for dot in functions[item]:

            somfin.append(functions[item][dot])
        data_set.append(somfin)
    return functions

#function to load in mock data into the ServiceLog table
def loadNewData(cursor):

    #get a random 20 rows from the table
    query = """  SELECT top 20 *
    FROM [CoreServices].[dbo].[tCoreServiceLog] A
    WHERE A.logID >= RAND()*50000000 """
    
    #get the data and format it
    result_set = get_data(query, cursor)
    data = formatter(result_set)
    
    #values for the change later
    randomint = random.randrange(0, 100)
    new_time = datetime.datetime.now()
    thenTemp3 = new_time + datetime.timedelta(days = 1)
    thenTemp = thenTemp3 + datetime.timedelta(milliseconds = randomint)

    #not really used, (child of it's time)
    ids=[]

    #change the initial data
    for i in range(1,len(data)):
        data[i][15] = new_time
        ids.append(100000000+random.randrange(1,1000000))
        data[i][0] = ids[i-1]
        data[i][1] = str(hash(data[i][0]))
        data[i][17] = thenTemp3
        data[i][18] = thenTemp

    #update the table
    cursor.execute("""SET IDENTITY_INSERT [CoreServices].[dbo].[tCoreServiceLog] ON""")
    for i in range(1,len(data)):
        query = """INSERT INTO [CoreServices].[dbo].[tCoreServiceLog](LogId,ReferenceId,ServiceId,FunctionName,RequestArguments, UserId, RequestTokenId,SystemId,RequestMachineId,ResponseInfo,ResponseMachineId,IsResponseError,ProcessingDiagnostics,VersionNumber,LogTypeId,LogDate,LogBy,StartTime,StopTime) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        cursor.execute(query,(data[i][0],data[i][1],data[i][2],data[i][3],data[i][4],data[i][5],data[i][6],data[i][7],data[i][8],data[i][9],data[i][10],data[i][11],data[i][12],data[i][13],data[i][14],data[i][15],data[i][16],data[i][17],data[i][18]))
    
    cursor.execute("""SET IDENTITY_INSERT [CoreServices].[dbo].[tCoreServiceLog] OFF""")

    #and commit the changes
    cursor.commit()
    
#format the data for the function  loadNewData   
def formatter(data):

    container = []
    for i in range(0,len(data)):
        container.append([])
        for j in range(0,len(data[i])):
            container[i].append(data[i][j])

    return container


#function to get a new point for the front page for the time, 'date' and the service specified
def getRealTimeData(cursor, date, service):

    #container for the final data
    data=[None,None]

    #map a service with a serviceID
    if service == 'collateral':
        id = str(9)
    elif service == 'accounts':
        id = str(6)
    elif service == 'creditcards':
        id = str('2 OR A.ServiceId = 4')
    elif service == 'loans' :
        id = str(7)
    else:
        #default
        id = '999'

    #queries to get speed and number of function calls for a date and for a service
    query = """DECLARE @date datetime = '"""+date+"""'
    DECLARE @date2 datetime = (SELECT DATEADD(minute,-10, @date))
    
    SELECT  AVG(DATEDIFF(MILLISECOND, A.StartTime, A.StopTime)) as aveg, A.ServiceId,count(B.LogId) as tal
    FROM [CoreServices].[dbo].[tCoreServiceLog] A join [CoreServices].[dbo].[tCoreServiceLogTiming] B on A.LogId = B.LogId
    WHERE B.StartTime <= @date AND B.StartTime >= @date2 AND (A.ServiceId = """+id+""") AND (B.StartTime is not null) and B.StopTime is not null
	GROUP BY A.ServiceId"""

    #get the data
    result_set = get_data(query, cursor)

    #format it and put it into the container
    data[0] = formatRealTimeData(result_set, service)

    #queries to get speed and number of function calls for a date week before the one above and for a service
    query = """DECLARE @date123 datetime = '"""+date+"""'
    DECLARE @date datetime = (SELECT DATEADD(day,-7, @date123))
    DECLARE @date2 datetime = (SELECT DATEADD(minute,-10, @date))
    
    SELECT  AVG(DATEDIFF(MILLISECOND, A.StartTime, A.StopTime)) as aveg, A.ServiceId,count(B.LogId) as tal
    FROM [CoreServices].[dbo].[tCoreServiceLog] A join [CoreServices].[dbo].[tCoreServiceLogTiming] B on A.LogId = B.LogId
    WHERE B.StartTime <= @date AND B.StartTime >= @date2 AND (A.ServiceId = """+id+""") AND (B.StartTime is not null) and B.StopTime is not null
	GROUP BY A.ServiceId"""

    result_set = get_data(query, cursor)

    #format it and store it in the container
    data[1] = formatRealTimeData(result_set, service)

    return data

#formatter for the funtion getRealTimeData()
def formatRealTimeData(data, service):
    
    #this function creates a dictionary for the result_set
    newData = {}

    try:
        newData[service] = data[1][0]
        newData[service+service] = data[1][2]
    except IndexError:
        newData[service] = 0
        newData[service+service] = 0

    return newData

#a thread worker that is used to execute the queries from the function getInitialRealTime()
def worker(query,cursor,flag,i,data):
    result_set = get_data(query, cursor)
    data[i] = formatInitRealTimeData(result_set, flag)


#function to get all the initial pionts for all the different services for the frontpage
def getInitialRealTime(cursor,date):

    #flag for the formatter to have the correct size of the container
    flag = False
    if date[15:16] == '0':
        flag=True

    #query to get speed and number of function calls for all the services for a specific date
    #this query used the date to create indexes that is then used in the formatting function
    query = """    DECLARE @date datetime = '"""+date+"""'
    DECLARE @date2 datetime = (SELECT DATEADD(hour,-5, @date))
    declare @Hstart integer = (SELECT DATEPART(HOUR,@date2)*6)
    declare @Mstart integer = (SELECT (DATEPART(MINUTE, @date2)/10))
    declare @Dstart integer = ((SELECT DATEPART(day,@date2)*144))
    declare @starter integer = (SELECT @Dstart+@Hstart+@Mstart)

    
    SELECT  AVG(DATEDIFF(MILLISECOND, A.StartTime, A.StopTime)) as aveg, COUNT(B.LogId) as tal, A.ServiceId,
    
    (DATEPART(day,B.StartTime)*(144)+DATEPART(HOUR,B.StartTime)*(6) + ((DATEPART(MINUTE, B.StartTime)/10)))-(@starter) as indexinn
    
    FROM [CoreServices].[dbo].[tCoreServiceLog] A join [CoreServices].[dbo].[tCoreServiceLogTiming] B on A.LogId = B.LogId
    WHERE B.StartTime <= @date AND B.StartTime >= @date2 AND (A.ServiceId = 9 OR A.ServiceId = 2 OR A.ServiceId = 3 OR A.ServiceId = 4 OR A.ServiceId = 5 OR A.ServiceId = 6 OR A.ServiceId = 7)
	GROUP BY DATEPART(DAY, B.StartTime),DATEPART(HOUR,B.StartTime),DATEPART(Minute, B.StartTime)/10, A.ServiceId
	ORDER BY A.ServiceId, DATEPART(DAY, B.StartTime),DATEPART(HOUR,B.StartTime),DATEPART(Minute, B.StartTime)/10
	"""

    #query to get speed and number of function calls for all the services for a date a week earlier then the one above
    query2 = """    DECLARE @date123 datetime = '"""+date+"""'
    DECLARE @date datetime = (SELECT DATEADD(day,-7, @date123))
    DECLARE @date2 datetime = (SELECT DATEADD(hour,-5, @date))
    declare @Hstart integer = (SELECT DATEPART(HOUR,@date2)*6)
    declare @Mstart integer = (SELECT (DATEPART(MINUTE, @date2)/10))
    declare @Dstart integer = ((SELECT DATEPART(day,@date2)*144))
    declare @starter integer = (SELECT @Dstart+@Hstart+@Mstart)

    
    SELECT  AVG(DATEDIFF(MILLISECOND, A.StartTime, A.StopTime)) as aveg, COUNT(B.LogId) as tal, A.ServiceId,
    
    (DATEPART(day,B.StartTime)*(144)+DATEPART(HOUR,B.StartTime)*(6) + ((DATEPART(MINUTE, B.StartTime)/10)))-(@starter) as indexinn
    
    FROM [CoreServices].[dbo].[tCoreServiceLog] A join [CoreServices].[dbo].[tCoreServiceLogTiming] B on A.LogId = B.LogId
    WHERE B.StartTime <= @date AND B.StartTime >= @date2 AND (A.ServiceId = 9 OR A.ServiceId = 2 OR A.ServiceId = 3 OR A.ServiceId = 4 OR A.ServiceId = 5 OR A.ServiceId = 6 OR A.ServiceId = 7)
	GROUP BY DATEPART(DAY, B.StartTime),DATEPART(HOUR,B.StartTime),DATEPART(Minute, B.StartTime)/10, A.ServiceId
	ORDER BY A.ServiceId, DATEPART(DAY, B.StartTime),DATEPART(HOUR,B.StartTime),DATEPART(Minute, B.StartTime)/10
	"""

    #make new connections to access the database concurrently with two threads. i do this to cut the time from 22 secs to 11 secs
    connections = [connect_to_DB(),connect_to_DB()]

    #container for the final data
    data = [None,None]

    threads = [None,None]

    querys = [query,query2]
    for i in range(len(threads)):
        threads[i] = threading.Thread(target=worker, args=(querys[i],connections[i].get_cursor(),flag,i,data,))
        threads[i].start()

    for i in range(len(threads)):
        threads[i].join()
        connections[i].close()

    return data

#formatter for the function getInitialRealTime()
def formatInitRealTimeData(data,flag):

    #this function creates a dictionary for the result_set
    newData = {}
   
    #go through all the rows and...
    for item in data:

        #...check for the serviceID...
        if item[2] == 9:

            #...and see if the service is already in the dictionary...
            if 'collateral' in newData:

                #...if it is, then i fill in the dictionary with the data for that date
                # with  the index that was created with the query. (the index is in 'item[3]')
                newData['collateral'][item[3]] = item[0]
                newData['collateralcollateral'][item[3]] = item[1]
            else:

                #...if the service is not in the dictionary then i check the flag in order to have the correct size for the subset in the dictionary...
                if flag:

                    #...for the correct size we fill in the dictionary be putting a container for the name...
                    newData['collateral'] = [0]*30
                    newData['collateralcollateral'] = [0]*30

                    #...then fill in the first point...
                    newData['collateral'][item[3]] = item[0]
                    newData['collateralcollateral'][item[3]] = item[1]
                else:
                    newData['collateral'] = [0]*31
                    newData['collateralcollateral'] = [0]*31
                    newData['collateral'][item[3]] = item[0]
                    newData['collateralcollateral'][item[3]] = item[1]

        #... AND REPEATE FOR ALL THE SERVICES
        elif item[2] == 6:
            if 'accounts' in newData:
                newData['accounts'][item[3]] = item[0]
                newData['accountsaccounts'][item[3]] = item[1]
            else:
                if flag:
                    newData['accounts'] = [0]*30
                    newData['accountsaccounts'] = [0]*30
                    newData['accounts'][item[3]] = item[0]
                    newData['accountsaccounts'][item[3]] = item[1]
                else:
                    newData['accounts'] = [0]*31
                    newData['accountsaccounts'] = [0]*31
                    newData['accounts'][item[3]] = item[0]
                    newData['accountsaccounts'][item[3]] = item[1]


        elif item[2] == 2 or item[2] == 4:
            if 'creditcards' in newData:
                newData['creditcards'][item[3]] = item[0]
                newData['creditcardscreditcards'][item[3]] = item[1]
            else:
                if flag:
                    newData['creditcards'] = [0]*30
                    newData['creditcardscreditcards'] = [0]*30
                    newData['creditcards'][item[3]] = item[0]
                    newData['creditcardscreditcards'][item[3]] = item[1]
                else:
                    newData['creditcards'] = [0]*31
                    newData['creditcardscreditcards'] = [0]*31
                    newData['creditcards'][item[3]] = item[0]
                    newData['creditcardscreditcards'][item[3]] = item[1]

        elif item[2] == 7:
            if 'loans' in newData:
                newData['loans'][item[3]] = item[0]
                newData['loansloans'][item[3]] = item[1]
            else:
                if flag:
                    newData['loans'] = [0]*30
                    newData['loansloans'] = [0]*30
                    newData['loans'][item[3]] = item[0]
                    newData['loansloans'][item[3]] = item[1]
                else:
                    newData['loans'] = [0]*31
                    newData['loansloans'] = [0]*31
                    newData['loans'][item[3]] = item[0]
                    newData['loansloans'][item[3]] = item[1]
    
    # after all the insertions, this bit fills in if a service was missing from the result_set (usually not used)
    if 'collateral' not in newData:
        newData['collateral'] = [0]*30
        newData['collateralcollateral'] = [0]*30

    if 'accounts' not in newData:
        newData['accounts'] = [0]*30
        newData['accountsaccounts'] = [0]*30

    if 'creditcards' not in newData:
        newData['creditcards'] = [0]*30
        newData['creditcardscreditcards'] = [0]*30
         
    if 'loans' not in newData:
        newData['loans'] = [0]*30
        newData['loansloans'] = [0]*30
    
    #return the dictionary
    return newData
