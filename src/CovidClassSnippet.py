import math
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os
import time
from datetime import timedelta, date
from CovidCases import CovidCases
from CovidCasesECDC import CovidCasesECDC
from CovidCasesOWID import CovidCasesOWID
from CovidCasesWHOv1 import CovidCasesWHOv1
from CovidCasesWHO import CovidCasesWHO
from PlotterBuilder import PlotterBuilder
import CovidMap as dfm
from IPython.display import SVG, display

def plot_the_data (df):
    # the name of the attribute we want to plot
    attribute = 'DailyCases'
    # plot
    (PlotterBuilder(attribute)
        .set_title(attribute)
        #.set_log()
        .set_grid()
        .plot_dataFrame(df))

    # the name of the attribute we want to plot
    attribute = "DailyCases7"
    # plot
    (PlotterBuilder(attribute)
        .set_title(attribute)
        #.set_log()
        .set_grid()
        .plot_dataFrame(df))

    # the name of the attribute we want to plot
    attribute = 'R7'
    # plot
    (PlotterBuilder(attribute)
        .set_title(attribute)
        #.set_log()
        .set_grid()
        .set_yaxis_formatter(mpl.ticker.StrMethodFormatter('{x:,.2f}'))
        .plot_dataFrame(df))

    # the name of the attribute we want to plot
    attribute = 'VaccineDosesAdministered'
    # plot
    (PlotterBuilder(attribute)
        .set_title(attribute)
        .set_log()
        .set_grid()
        .plot_dataFrame(df))

    # the name of the attribute we want to plot
    attribute = 'PercentPeopleReceivedFirstDose'
    # plot
    (PlotterBuilder(attribute)
        .set_title(attribute)
        #.set_log()
        .set_grid()
        .set_yaxis_formatter(mpl.ticker.PercentFormatter())
        .plot_dataFrame(df))

    # the name of the attribute we want to plot
    attribute = 'PercentPeopleReceivedAllDoses'
    # plot
    (PlotterBuilder(attribute)
        .set_title(attribute)
        #.set_log()
        .set_grid()
        .set_yaxis_formatter(mpl.ticker.PercentFormatter())
        .plot_dataFrame(df))

    # the name of the attribute we want to plot
    attribute = 'DailyVaccineDosesAdministered7DayAverage'
    # plot
    (PlotterBuilder(attribute)
        .set_title(attribute)
        #.set_log()
        .set_grid()
        .plot_dataFrame(df))

def plot_map(theClass):
    # the root of the output directory
    outputDirectory = str(os.path.expanduser('~/Desktop')) 
    # the list of comma separated geoIDs for the major European countries
    countryListAll = theClass.get_pygal_american_geoid_string_list() + ',' + \
                     theClass.get_pygal_european_geoid_string_list() + ',' + \
                     theClass.get_pygal_african_geoid_string_list() + ',' + \
                     theClass.get_pygal_oceania_geoid_string_list() + ',' + \
                     theClass.get_pygal_asian_geoid_string_list()  
    # get the dataframe for these countries
    dfAll = theClass.get_data_by_geoid_string_list(countryListAll)
    # create a map for the dataframe
    map = dfm.CovidMap(dfAll)
    # a list of requested maps
    gis = []
    # append maps to be generated
    gis.append(dfm.mapInfo("Cases", 'Accumulated confirmed cases', outputDirectory))
    # select a date
    theDay = date.today() - timedelta(days=4)
    for gi in gis:
        # generate the map
        result = map.create_map_for_date(gi, theDay)
        # ...and render it
        result.map.render_in_browser()

def main():
    # get the latests database files as a CSV
    try:
        pathToCSV_owid = CovidCasesOWID.download_CSV_file()
        pathToCSV_who = CovidCasesWHO.download_CSV_file()
    except FileNotFoundError:
        # print an error message
        print('Unable to download the database. Try again later.')
        return

    # some benchmarking
    start = time.time()
    # create instances
    covidCases_owid = CovidCasesOWID(pathToCSV_owid)
    covidCases_who = CovidCasesWHO(pathToCSV_who)
    # create tuples of instances and country codes
    objList = [covidCases_owid, covidCases_who]

    # just in case we want to use some optionals
    numCasesSince = 1000
    lastN = 90
    # the list of comma separated geoIDs
    countryList = 'DE, GB, FR, ES, IT, CH, AT, EL, NA'
    # get the combined dataframe
    #df = CovidCases.create_combined_dataframe_by_geoid_string_list(objList, countryList)
    #df = CovidCases.create_combined_dataframe_by_geoid_string_list(objList, countryList, lastNdays=lastN)
    df = CovidCases.create_combined_dataframe_by_geoid_string_list(objList, countryList, sinceNcases=numCasesSince)

    # the width for a filter
    width = 7
    for obj in objList:
        # add lowpass filtered DailyCases
        df = obj.add_lowpass_filter_for_attribute(df, 'DailyCases', width)
        # add r0
        df = obj.add_r0(df)
        # add lowpass filtered R
        df = obj.add_lowpass_filter_for_attribute(df, "R", 7)

    # benchmarking
    end = time.time()
    print(str((end - start)) + 's')
    # plot it
    plot_the_data (df)
    # show the plot
    plt.show()
    # plot a map
    #plot_map(covidCases_who)
    return

# execute main
if __name__ == "__main__":
    main()
