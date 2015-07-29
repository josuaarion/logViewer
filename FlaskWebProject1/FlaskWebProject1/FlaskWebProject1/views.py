"""
Routes and views for the flask application.
"""

from datetime import datetime
from FlaskWebProject1 import app
from flask import *
from FlaskWebProject1 import *
from functools import wraps
import SQLclient
import Plotter
import xmlWorker
import auditLogger
import wtforms.form
from datetime import date
import ast
#object to connect to the DB, created in the StartPage function

init = True
flagg = True
audit = None


def initz():
    global audit
    audit = auditLogger.auditLog()


#log in checker
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):

        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to log in first')
            return redirect(url_for('log'))
    return wrap

#logout function
@app.route('/logout')
def logout():
    global audit
    global init
    global flagg
    init = True
    flagg = False
    try:
        audit.closeConnection()
    except:
        print('you are already logged out')
    session.pop('logged_in', None)
    flash('you were logged out')
    return redirect(url_for('log'))

#login site
@app.route('/log', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def log():
    global init
    global audit
    global flagg

    if init and flagg:
        initz()
        init = False
    error = None
    if request.method == 'POST':
        if (request.form.get('username', None) != 'admin' and request.form.get('password', None) != 'admin') and (request.form.get('username', None) != 'josua' and request.form.get('password', None) != 'door'):
            error = 'Invalid credentials, please try again'
        else:
            flagg = True
            session['logged_in'] = True
            return redirect(url_for('frontPage'))
    return render_template('log.html', error = error )

#the status page
@app.route('/frontPage', methods=['GET','POST'])

@login_required
def frontPage():
    global audit

    #get service name from the html site frontPage
    service = request.args.get('name', '')

    #get a date for the query
    now = datetime.datetime.now()
    thenTemp = now - datetime.timedelta(hours = 10*24)
    then = thenTemp.strftime("%Y-%m-%d %H:%M")

    #get data for the last 5 hours

    #check the status for the services
    data = xmlWorker.checkServices()

    #if the page has not initialized then service won't be empty since it is a query from the frontPage
    #in that case we go here to answer the response...
    if service != '':

        SpanData = audit.getRealTime(then, service)
        #format data for Json with the data from DetailData
        service2 = str(service)+str(service)
        data = {'now':SpanData[0][service], 'then':SpanData[1][service],'nowC':SpanData[0][service2], 'thenC':SpanData[1][service2], 'flags':data}

        return jsonify(data)

    #...else we simply render the page with the defaults
    audit.getInitialRealTime()
    return render_template('frontPage.html', flags = data, SD = audit.initdata)

#startpage that contain the mainpie chart
@app.route('/StartPage', methods=['GET', 'POST'])
@login_required
def StartPage():

    #the audit object is used throughout this project so i will only mention it here. it is created in this function and is used to manage connections with the DB
    global audit
    audit.updateAggTables()

    #if the page gets a request like a button press etc... it will go into this if statement
    if request.method == 'POST':

        #get data from the buttons. the only value to come here are "day", "week", "month", "year" and "all-time"
        stuff = request.form['form']

        #get data for the outer pie
        data = audit.getNewPie(stuff)

        #get data for the inner pie
        data2 = audit.getNumPie(stuff)
        
        # little something to get rid of the data that was too small to be in the pie chart
        names=[]
        for item in data:
            names.append(item[0])

        names2 = []
        for item in data2:
            if item not in names:
                names2.append(item)

        for name in names2:
            del data2[name]
        
        #get the list of services available
        listOfServices = audit.getServices()

        #audit.loadNewDataIntoTable()

        #render the site with the new data
        return render_template('StartPage.html', list = listOfServices, data = data, data2 = data2)
   
    #uses default values
    data = audit.getNewPie('all-time')
    data2 = audit.getNumPie('all-time')
    
    #same as in the if statement above
    names=[]
    for item in data:
        names.append(item[0])

    names2 = []
    for item in data2:
        if item not in names:
            names2.append(item)

    for name in names2:
        del data2[name]


    #audit.loadNewDataIntoTable()

    listOfServices = audit.getServices()
    return render_template('StartPage.html', list = listOfServices, data = data, data2 = data2)


###################################################################################################
# the following segment is for five fuctions that all have the same functionality,                #
# that is, they render a service site with all the graphs                                         #
###################################################################################################

@app.route('/<service>', methods=['GET', 'POST'])
@login_required
def general(service):

    global audit

    #get dates and the name of the function within 'service' in order to get the daitailed data for the detail graph default values for both is ''
    date = request.args.get('date', '')
    name = request.args.get('name', '')

    #gather data with the date and name variables
    DetailData = audit.getDetail(date, service, name )

    #if the default values for the date and name are apparent, i will not return json response, because then that would be the only thing that would be rendered on the site
    # however, if the values are not the default, then the page has been loaded before and someone has requested new data. in that case it is ok to only send the
    # json response since in that case you are answering a specific client request that wants a json response
    if date != '':

        #format data for Json with the data from DetailData
        data = {'number' : DetailData[1], 'hour': DetailData[0], 'date': date}
        return jsonify(data)

    #if the page gets a request like a button press etc... it will go into this if statement
    if request.method == 'POST':

        #get dates from the calendar 
        dags1 = request.form['datedate']
        dags2 = request.form['date']
        if not isinstance(dags1, datetime.date) or not isinstance(dags2, datetime.date):
            now = datetime.datetime.now().date()
            then = now - datetime.timedelta(days = 30.0)

            dates =[str(now),str(then)]
        else:
            #refactor dates to get the right format for the SQL query returns [date1,date2]
            dates = SQLclient.refactorDates(dags1,dags2)

        #get the span from site
        span = request.form['span']
        if  not span.isdigit():
            span = 1

        #functions is a data array that looks like this: [datapacket for speed of service, datapacket for the number of function calls, name of the functions for the service]
        # the data gathered is found through SQL with the parameters given
        functions = audit.getInfo(service,dates[0],dates[1],span)

        #get the names in a seperate array
        names = functions[-1]

        # then remove it from the functions array, leaving the functions array to look like this: [datapacket for speed of service, datapacket for the number of function calls]
        del functions[-1]

        #a little something in order to get the YYYY - MM - DD format into the site to be used in numerous places
        date1 = datetime.date(int(dates[0][:4]), int(dates[0][5:7]), int(dates[0][8:10])) - datetime.timedelta(int(span)*365/12)
        date2 = datetime.date(int(dates[1][:4]), int(dates[1][5:7]), int(dates[1][8:10])) - datetime.timedelta(int(span)*365/12)

        dags1y = date1.year
        dags2y = date2.year

        dags1m = date1.month
        dags2m = date2.month

        dags1d = date1.day
        dags2d = date2.day

        #render the page with all the gathered data
        return render_template('speedLogger.html', functions = names, name=service,dags1Y = dags1y, dags1M=dags1m, dags1D = dags1d, dags2Y=dags2y, dags2M = dags2m, dags2D = dags2d, data= functions, DD = DetailData[0])
    
    #get default dates for the page when it is being loaded for the first time
    now = datetime.datetime.now().date()
    then = now - datetime.timedelta(days = 30.0)

    #format the dates like in the if statement above to get the YYYY - MM - DD format into the site
    dags11 = str(now)
    dags22 = str(then)

    date1 = datetime.date(int(dags11[:4]), int(dags11[5:7]), int(dags11[8:10])) - datetime.timedelta(1*365/12)
    date2 = datetime.date(int(dags22[:4]), int(dags22[5:7]), int(dags22[8:10])) - datetime.timedelta(1*365/12)

    dags1y = date1.year
    dags2y = date2.year

    dags1m = date1.month
    dags2m = date2.month
    
    dags1d = date1.day
    dags2d = date2.day

    #get the data from the SQL connection with the default parameters -- same as above
    functions = audit.getInfo(service,dags11,dags22,1)
    names = functions[-1]
    del functions[-1]
    return render_template('speedLogger.html', functions = names, name=service,dags1Y = dags1y, dags1M=dags1m, dags1D = dags1d, dags2Y=dags2y, dags2M = dags2m, dags2D = dags2d, data= functions, DD = DetailData[0])

@app.route('/moo', methods=['GET', 'POST'])
@login_required
def moo():
    return render_template('moo.html')
