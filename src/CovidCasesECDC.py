import pandas as pd
import numpy as np
import math
import re
import time
import datetime
import os
import requests
import re
from datetime import date
from CovidCases import CovidCases
from GeoInformationWorld import GeoInformationWorld

class CovidCasesECDC(CovidCases):
    """The class will expose data attributes in form of a DataFrame. Its base class also provides methods to process 
    the data which will end up in additional columns in the DataFrame. These are the name sof the columns
    that are generated. Notice: The 'Continent' column is additionally and specific to this sub class

    Date
    The date of the data 
    
    GeoID
    The GeoID of the country such as FR for France or DE for Germany

    GeoName
    The name of the country

    Continent
    The continent of the country

    Population
    The population of the country

    DailyCases
    The number of new cases on a given day

    DailyDeaths
    The number of new deaths on the given date

    Continent
    The continent of the country as an additional column
    
    Returns:
        CovidCasesECDC: A class to provide access to some data based on the ECDC file.
    """

    def __init__(self, filename):
        """The constructor takes a string containing the full filename of a CSV
        database you can download from the ECDC website until 14.12.2021. Since  
        than the ECDC publishes only 14 day numbers. That was the link until 
        14.12.2020, the site also contains a link to the new published numbers:
        https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide
        The database will be loaded and kept as a private member. To retrieve the
        data for an individual country you can use the public methods
        GetCountryDataByGeoID or GetCountryDataByCountryName. These functions take 
        ISO 3166 alpha_2 (2 characters long) GeoIDs.

        Args:
            filename (str): The full path and name of the csv file. 
        """
        # some benchmarking
        start = time.time()
        # open the file
        self.__df = pd.read_csv(filename)
        # remove columns that we don't need
        self.__df = self.__df.drop(columns=['day', 
                                            'month', 
                                            'year', 
                                            'countryterritoryCode', 
                                            'Cumulative_number_for_14_days_of_COVID-19_cases_per_100000'])
        # rename the columns to be more readable
        self.__df.columns = ['Date',
                             'DailyCases',
                             'DailyDeaths',
                             'GeoName',
                             'GeoID',
                             'Population',
                             'Continent']
        # re-order the columns to be similar for all sub-classes                                   
        self.__df = self.__df[['Date', 
                              'GeoName', 
                              'GeoID', 
                              'Population', 
                              'Continent', 
                              'DailyCases',
                              'DailyDeaths']]
        # now apply the country names from our internal list
        giw = GeoInformationWorld()
        # get all country info
        dfInfo = giw.get_geo_information_world()
        
        # fix the 'namibia' problem by replacing nan with 'NAM'
        self.__df['GeoID'] = self.__df['GeoID'].replace(np.nan, 'NAM')
        # fix the 'UK' problem by replacing UK with GB
        self.__df['GeoID'] = self.__df['GeoID'].replace('UK', 'GB')
        # fix the 'EL' problem by replacing EL with GR
        self.__df['GeoID'] = self.__df['GeoID'].replace('EL', 'GR')
        # our result data frame
        dfs = []
        for geoID in self.__df['GeoID'].unique():
            # get the geoName for this geoID
            geoName = giw.geo_name_from_geoid(geoID)
            # get the data for a country and add the additional rows
            dfSingleCountry = self.__df.loc[self.__df['GeoID'] == geoID].copy()
            # reset the index
            dfSingleCountry.reset_index(inplace=True, drop=True)
            dfSingleCountry.head()   
            # the current name         
            curName = dfSingleCountry['GeoName'][0]
            # replace it if necessary
            if geoName != curName:
                dfSingleCountry['GeoName'] = [geoName for _ in range(0, len(dfSingleCountry['GeoID']))]
            # append this dataframe to our result
            dfs.append(dfSingleCountry)
        # keep the concatenated dataframe
        self.__df = pd.concat(dfs)
        # change the type of the 'date' field to a pandas date
        self.__df['Date'] = pd.to_datetime(self.__df['Date'],
                                           format='%d/%m/%Y')
        # some benchmarking
        end = time.time()
        print('Pandas loading the ECDC CSV: ' + str(end - start) + 's')
        # pass the dataframe to the base class
        super().__init__(self.__df)

    @staticmethod
    def download_CSV_file():
        """automatically downloads the database file if it doesn't exists. Need
        to be called in a try-catch block as it may throw FileNotFoundError or
        IOError errors

        Raises:
            FileNotFoundError: In case it couldn't download the file

        Returns:
            str: The filename of the database wether it has been downloaded or not.
        """
        # todays date
        today = date.today()
        # the prefix of the CSV file is Y-m-d
        preFix = today.strftime('%Y-%m-%d') + "-ECDC"
        try:
            # check if it is running in jupyter
            get_ipython
            # the absolute directory of this python file
            absDirectory = os.path.dirname(os.path.abspath(os.path.abspath('')))
            # the target filename
            targetFilename = os.path.join(absDirectory, './data/' + preFix + '-db.csv')
        except:
            # the absolute directory of this python file
            absDirectory = os.path.dirname(os.path.abspath(__file__))
            # the target filename
            targetFilename = os.path.join(absDirectory, '../data/' + preFix + '-db.csv')
        # check if it exist already
        if os.path.exists(targetFilename):
            print('using existing file: ' + targetFilename)
        else:
            # download the file from the ecdc server
            url = 'https://opendata.ecdc.europa.eu/covid19/casedistribution/csv/'
            r = requests.get(url, timeout=1.0)
            if r.status_code == requests.codes.ok:
                with open(targetFilename, 'wb') as f:
                    f.write(r.content)
            else:
                raise FileNotFoundError('Error getting CSV file. Error code: ' + str(r.status_code))
        return targetFilename

    def get_available_GeoID_list(self):
        """Returns a dataframe having just two columns for the GeoID and Country name

        Returns:
            Dataframe: A dataframe having two columns: The country name and GeoID
        """ 
        # the list of GeoIDs in the dataframe
        geoIDs = self.__df['GeoID'].unique()
        # the list of country names in the dataframe
        countries = self.__df['GeoName'].unique()
        # merge them together
        list_of_tuples = list(zip(geoIDs, countries))
        # create a dataframe out of the list
        dfResult = pd.DataFrame(list_of_tuples, columns=['GeoID', 'GeoName'])
        return dfResult

    def get_data_source_info(self):
        """
        Returns a list containing information about the data source. The list holds 3 strings:
        InfoFullName: The full name of the data source
        InfoShortName: A shortname for the data source
        InfoLink: The link to get the data

        Returns:
            Dataframe: A dataframe holding the information
        """
        info = ["European Centre for Disease Prevention and Control", 
                "ECDC",
                "https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide"]
        return info

    def review_geoid_list(self, geoIDs):
        """
        Returns a corrected version of the given geoID list to ensure that cases of mismatches like UK-GB are corrected by the sub-class.  
        geoIDs: The list holding the geoIDs as requested such as ['DE', 'UK']

        Returns:
            list: A corrected list such as ['DE', 'GB'] that translates incorrect country codes to corrected codes 
        """
        # fix the ECDC mistakes and map e.g. UK to GB 
        corrected = []
        for geoID in geoIDs:
            if geoID == 'GB':
                corrected.append('UK')
            elif geoID == 'GR':
                corrected.append('EL')
            elif geoID == 'NA':
                corrected.append('NAM')
            else:
                corrected.append(geoID)
        return corrected

    @staticmethod
    def get_pygal_european_geoid_list():
        """Returns a list of GeoIDs of European countries that are available in PayGal and 
        the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            list: List of strings of GeoID's
        """
        # just the main countries for a map
        geoIDs = re.split(r',\s*', CovidCases.get_pygal_european_geoid_string_list().upper())
        return geoIDs

    @staticmethod
    def get_pygal_european_geoid_string_list():
        """
        Returns a comma separated list of GeoIDs of European countries that are available in 
        PayGal and the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            str: A comma separate list of GeoID's
        """
        # just the main european countries for a map, pygal doesn't contain e.g. 
        # Andorra, Kosovo (XK)
        geoIdList = 'AM, AL, AZ, AT, BA, BE, BG, BY, CH, CY, CZ, ' + \
                    'DE, DK, EE, GR, ES, FI, FR, GE, GL, '  + \
                    'HU, HR, IE, IS, IT, LV, LI, LT, ' + \
                    'MD, ME, MK, MT, NL, NO, PL, PT, ' + \
                    'RU, SE, SI, SK, RO, UA, GB, RS'
        return geoIdList

    @staticmethod
    def get_pygal_american_geoid_list():
        """Returns a list of GeoIDs of American countries that are available in PayGal and 
        the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            list: List of strings of GeoID's
        """
        # just the main countries for a map
        geoIDs = re.split(r',\s*', CovidCases.get_pygal_american_geoid_string_list().upper())
        return geoIDs
        
    @staticmethod
    def get_pygal_american_geoid_string_list():
        """
        Returns a comma separated list of GeoIDs of American countries that are available in 
        PayGal and the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            str: A comma separate list of GeoID's
        """
        # just the main american countries for a map, pygal doesn't contain e.g. 
        # Bahamas (BS), Barbados (BB), Bermuda (BM), Falkland Island (FK)
        geoIdList = 'AR, BB, BM, BO, BR, BS, CA, CL, CO, ' + \
                    'CR, CU, DO, EC, SV, GT, GY, HN, HT, ' + \
                    'JM, MX, NI, PA, PE, PR, PY, SR, US, UY, VE'
        return geoIdList

    @staticmethod
    def get_pygal_asian_geoid_list():
        """Returns a list of GeoIDs of Asian countries that are available in PayGal and 
        the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            list: List of strings of GeoID's
        """
        # just the main countries for a map
        geoIDs = re.split(r',\s*', CovidCases.get_pygal_asian_geoid_string_list().upper())
        return geoIDs
        
    @staticmethod
    def get_pygal_asian_geoid_string_list():
        """
        Returns a comma separated list of GeoIDs of Asian countries that are available in 
        PayGal and the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            str: A comma separate list of GeoID's
        """
        # just the main asian countries for a map, pygal doesn't contain e.g. 
        # Qatar (QA)
        geoIdList = 'AF, BH, BD, BT, BN, KH, CN, IR, IQ, IL, JP, JO, '  + \
                    'KZ, KW, KG, LA, LB, MY, MV, MN, MM, NP, OM, PK, PS, PH, '  + \
                    'QA, SA, SG, KR, LK, SY, TW, TJ, TH, TL, TR, AE, UZ, VN, YE, IN, ID'
        return geoIdList
    
    @staticmethod
    def get_pygal_african_geoid_list():
        """Returns a list of GeoIDs of African countries that are available in PayGal and 
        the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            list: List of strings of GeoID's
        """
        # just the main countries for a map
        geoIDs = re.split(r',\s*', CovidCases.get_pygal_african_geoid_string_list().upper())
        return geoIDs
        
    @staticmethod
    def get_pygal_african_geoid_string_list():
        """
        Returns a comma separated list of GeoIDs of African countries that are available in 
        PayGal and the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            str: A comma separate list of GeoID's
        """
        # just the main african countries for a map, pygal doesn't contain e.g. 
        # Comoros (KM)
        geoIdList = 'DZ, AO, BJ, BW, BF, BI, CM, CV, CF, TD, KM, CG, CI, CD, '  + \
                    'DJ, EG, GQ, ER, SZ, ET, GA, GM, GH, GN, GW, KE, LS, LR, '  + \
                    'LY, MG, MW, ML, MR, MU, MA, MZ, NE, NG, RW, ST, SN, SC, '  + \
                    'SL, SO, ZA, SS, SD, TG, TN, UG, TZ, EH, ZM, ZW'
        return geoIdList

    @staticmethod
    def get_pygal_oceania_geoid_list():
        """Returns a list of GeoIDs of Oceanian countries that are available in PayGal and 
        the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            list: List of strings of GeoID's
        """
        # just the main countries for a map
        geoIDs = re.split(r',\s*', CovidCases.get_pygal_oceania_geoid_string_list().upper())
        return geoIDs

    @staticmethod
    def get_pygal_oceania_geoid_string_list():
        """
        Returns a comma separated list of GeoIDs of Oceanian countries that are available in 
        PayGal and the WHO data. 
        Be aware:
        Not all countries of the WHO are available in PayGal and some names are different 
        (GB in PyGal = UK in WHO, GR in PyGal = EL in WHO). PyGal uses lower case and WHO
        upper case. 

        Returns:
            str: A comma separate list of GeoID's
        """
        # just the main oceania countries for a map, pygal doesn't contain e.g. 
        # Comoros (KM)
        geoIdList = 'AU, FJ, PF, GU, NC, NZ, MP, PG'
        return geoIdList
