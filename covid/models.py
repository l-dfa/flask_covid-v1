# :filename: covid/df.py

# std libs import
from datetime import datetime, date, timedelta
import sqlite3

# 3rd parties libs import
import click
from flask import current_app, g
from flask.cli import with_appcontext

def world_shape(df):
    '''
    models dataframe to our needs
    
    params: df        pandas dataframe - df to model
    
    return df         pandas dataframe - the modeled dataframe
    '''
    df['dateRep'] = df['dateRep'].map(lambda x: datetime.strptime(x, current_app.config['D_FMT2']).date()) # from str to date
    df.loc[(df['countriesAndTerritories']=='CANADA'), 'countriesAndTerritories'] = 'Canada'
    return df


def open_df(fname, opener, shaper):
    '''read a dataframe from file
    
    params
      - fname      str or Path - name of file to read
      - opener     pandas method - method to use to read file
      - shaper     function - to shape dataframe before to return it
      
    return df          pandas dataframe
    
    remark: The dataframe is unique for each request and will be reused
            if this is called again
    '''
    if 'df' not in g:
        g.df = opener(fname)
        g.df = shaper(g.df)
    #else:
    #    pass
    return g.df


def close_df(e=None):
    """If this request connected to the dataframe, close the connection
    
    params: e        error
    """
    df = g.pop("df", None)

    if df is not None:
        del df


def init_app(app):
    """Register dataframe functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_df)
    
    
class Nations(object):
    '''an istance of this class lists all nations present in dataframe,
    with their continent
    
    remark: it uses a (self.__n__) dictionary with this structure:
        {continent_name: {nation_id: nation_name,
                          nation_id: nation_name,
                          ...
                         }
         ...
        }
    '''

    def __init__(self, csv_file=None, dataframe=None):
        self.__n__ = dict()
        df = None
        if csv_file is not None:
            df = pd.read_csv(csv_file)
        elif dataframe is not None:
            df = dataframe
        if df is not None:
            cdf = df[['countriesAndTerritories', 'geoId', 'continentExp']].drop_duplicates()
            for row, c in cdf.iterrows():           # row, country:(name, id,, continent)
                self.add_nation(c[2], c[1], c[0])      # continent, id, name

    def __setitem__(self, key, item):
        self.__n__[key] = item

    def __getitem__(self, key):
        return self.__n__[key]

    def __repr__(self):
        return repr(self.__n__)

    def __len__(self):
        return len(self.__n__)

    def __delitem__(self, key):
        del self.__n__[key]

    def get(self, key, default=None):
        if key in self.__n__:
            return self.__n__[key]
        else:
            return None

    def has_key(self, k):
        return k in self.__n__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__n__.keys()

    def values(self):
        return self.__n__.values()

    def items(self):
        return self.__n__.items()

    def pop(self, *args):
        return self.__n__.pop(*args)

    def __cmp__(self, dict_):
        return self.__cmp__(self.__n__, dict_)

    def __contains__(self, item):
        return item in self.__n__

    def __iter__(self):
        return iter(self.__n__)

    def __unicode__(self):
        return repr(self.__n__)

    def get_for_select(self, continents=None):
        '''create a list of 2-tuple (id,nations,) of indicated continents
        
        params:
            - continents              str or list of str - a single continent, or 
                                          a list of continents; if None we get all continents
        
        return: a list of 2-tuple (id,nations,) of indicated continents
        '''
        l = []
        if continents is None:
            continents = list(self.__n__.keys())
        elif type(continents) == type([]):
            pass
        else:
            continents = [continents]
        
        for continent in continents:
            l.extend( [(id, name) for id, name in self.__n__[continent].items()] )
        l.sort(key = lambda x: x[1])
        return l
        
    def get_for_list(self, continents=None):
        '''create a list of nations of indicated continents
        
        params:
            - params                str or list of str - a single continent, or 
                                        a list of continents; if None we get all continents
        
        return: a list of names of nations belonging to the indicated continents
        '''
        l = []
        if continents is None:
            continents = list(self.__n__.keys())
        elif type(continents) == type([]):
            pass
        else:
            continents = [continents]
        
        for continent in continents:
            l.extend([name for id, name in self.__n__[continent].items()])
        l.sort()
        return l

    def add_nation(self, continent, id, name):
        ''' add a single nation
        
        params:
            - continent       str - continent name
            - id              str - identifier of nation
            - name            str - name of nation
            
        return None
        '''
        if continent not in self.__n__:
            self.__n__[continent] = dict()
        self.__n__[continent][id] = name

    def get_nation_name(self, id, default=None):
        ''' add a single nation
        
        params:
            - continent       str - continent name
            - id              str - identifier of nation
            - name            str - name of nation
            
        return None
        '''
        name = None
        continents = list(self.__n__.keys())
        for continent in continents:
            name = self.__n__.get(continent).get(id, None)
            if name is not None:
                break
        if name is None:
            name = default
            
        return name


# + ldfa,2020-05-11 geographical areas definitions.
# in case of federation (EU) key is 'countriesAndTerritories' field
AREAS = {'European_Union': {'contest': 'nations',
                            'geoId':      'EU',
                            'countryterritoryCode': 'EU',
                            'continentExp': 'Europe',
                            'nations': { "AT": "Austria",
                                         "BE": "Belgium",  
                                         "BG": "Bulgaria",  
                                         "HR": "Croatia",  
                                         "CY": "Cyprus",  
                                         "CZ": "Czechia",  
                                         "DK": "Denmark",  
                                         "EE": "Estonia",  
                                         "FI": "Finland",  
                                         "FR": "France",  
                                         "DE": "Germany",  
                                         "EL": "Greece", 
                                         "HU": "Hungary", 
                                         "IE": "Ireland", 
                                         "IT": "Italy", 
                                         "LV": "Latvia", 
                                         "LT": "Lithuania", 
                                         "LU": "Luxembourg", 
                                         "MT": "Malta", 
                                         "NL": "Netherlands", 
                                         "PL": "Poland", 
                                         "PT": "Portugal", 
                                         "RO": "Romania", 
                                         "SK": "Slovakia", 
                                         "SI": "Slovenia", 
                                         "ES": "Spain", 
                                         "SE": "Sweden", 
                                       },
                           },
         'Central_America':{'contest': 'continents',
                          'geoId':   'Central_America',                 # MUST be equal to name
                          'countryterritoryCode': 'Central_America',
                          'continentExp': 'Central_America',            # MUST be equal to name
                          'nations': { "BZ": "Belize",
                                       "CR": "Costa_Rica",
                                       "SV": "El_Salvador",
                                       "GT": "Guatemala",
                                       "HN": "Honduras",
                                       "NI": "Nicaragua",
                                       "PA": "Panama",
                                     },
                         },
         'North_America':{'contest': 'continents',
                          'geoId':   'North_America',                 # MUST be equal to name
                          'countryterritoryCode': 'North_America',
                          'continentExp': 'North_America',            # MUST be equal to name
                          'nations': { "CA": "Canada",
                                       "US": "United_States_of_America",
                                       "AG": "Antigua_and_Barbuda",
                                       "BS": "Bahamas",
                                       "BB": "Barbados",
                                       "BZ": "Belize",
                                       "CU": "Cuba",
                                       "DM": "Dominica",
                                       "DO": "Dominican_Republic",
                                       "GD": "Grenada",
                                       "HT": "Haiti",
                                       "JM": "Jamaica",
                                       "MX": "Mexico",
                                       "KN": "Saint_Kitts_and_Nevis",
                                       "LC": "Saint_Lucia",
                                       "VC": "Saint_Vincent_and_the_Grenadines",
                                       "TT": "Trinidad_and_Tobago",
                                       "AI": "Anguilla",
                                       "BM": "Bermuda",
                                       "VG": "British_Virgin_Islands",
                                       "KY": "Cayman_Islands",
                                       "MS": "Montserrat",
                                       "PR": "Puerto_Rico",
                                       "TC": "Turks_and_Caicos_islands",
                                       "VI": "United_States_Virgin_Islands",
                                       "BQ": "Bonaire, Saint Eustatius and Saba",
                                       "CW": "Curaçao",
                                       "GL": "Greenland",
                                       "SX": "Sint_Maarten",
                                     },
                         },
         'South_America':{'contest': 'continents',
                          'geoId':   'South_America',                 # MUST be equal to name
                          'countryterritoryCode': 'South_America',
                          'continentExp': 'South_America',            # MUST be equal to name
                          'nations': { "CO": "Colombia",
                                       "VE": "Venezuela",
                                       "GY": "Guyana",
                                       "SR": "Suriname",
                                       "BR": "Brazil",
                                       "PY": "Paraguay",
                                       "UY": "Uruguay",
                                       "AR": "Argentina",
                                       "CL": "Chile",
                                       "BO": "Bolivia",
                                       "PE": "Peru",
                                       "EC": "Ecuador",
                                       "FK": "Falkland_Islands_(Malvinas)",
                                       #"GF": "French Guiana",
                                     },
                         },
        }

# + ldfa 2020-05-11 managing geographic areas
def areas_get_nation_name(geoId, contest, areas=None):
    '''get name given id from a 'geographic area definition' data structure
    
    params:
       - geoId                 str - id of area (2 letters)
       - contest               str - 'nations' | 'continents'
       - areas                 dict of dict - e.g. {'European_Union': {'contest': 'nations',
                                                                       'geoId':   'EU',
                                                                       'countryterritoryCode': 'EU',
                                                                       'continentExp': 'Europe',
                                                                       'nations': ( "Austria", ...)
                                                                      },
                                                    'North_America':{'contest': 'continents',
                                                                     'geoId':   'North_America',
                                                                     'countryterritoryCode': None,
                                                                     'continentExp': 'North_America',
                                                                     'nations': ( "Canada", ...),
                                                                    },
                                                    ...
                                                   }
    
    return str: nation or continent name of given geoId;
           None if geoId not found
    '''
    if areas is None: areas = AREAS
    for k, v in areas.items():
        if v['contest'] == contest and v['geoId'] == geoId:
            return k
    return None


# + ldfa 2020-05-11 managing geographic areas
def areas_get_names(contest, areas=None):
    '''get all names given contest from a 'geographic area definition' data structure
    
    params:
       - contest               str - 'nations' | 'continents'
       - areas                 dict of dict - see areas_get_nation_name(...) comment
    
    return list of str: nations or continents names;
           None if contest not found
    '''
    if areas is None: areas = AREAS
    names = []
    for k, v in areas.items():
        if v['contest'] == contest:
            names.append(k)
    if names == []: names= None
    return names


