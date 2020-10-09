# :filename: covid/models.py
#
# our initial data is a dataframe with this structure (csv format):
#
#   dateRep,    day, month, year, cases, deaths, countriesAndTerritories, geoId, countryterritoryCode, popData2018, continentExp
#   24/04/2020, 24,  4,     2020, 105,   2,      Afghanistan,             AF,    AFG,                  37172386,    Asia
#
# with:
#
#   * dateRep,                   representation of the date as dd/mm/aaaa
#   * day,  
#   * month,
#   * year, 
#   * cases,                     positive cases in the day
#   * deaths,                    deaths in the day
#   * countriesAndTerritories,   name of the nation (or territory)
#   * geoId,                     identification code of nation
#   * countryterritoryCode,      another code of nation
#   * popData2018,               population of nation on the year 2018; WARNING: could be popData2019
#   * continentExp               continent of the nation
#   * Cumulative_number_for_14_days_of_COVID-19_cases_per_100000   not used
#
# from version 1.2
# we use a class GeoEntities to classify contries, continents and subcontinents
#     a geographic entity has a (str from initial data) identity as key, and these attributes:
#         - type                    'nation' | 'continent'
#         - original_country        bool - true if entity is from initial data
#         - name                    str - from initial data
#         - population              int - calculated or from initial data
#         - countryterritoryCode    str - another code from initial data
#         - continentexp            str - from initial data or we assigned 
#         - nations                 list of geoIds
#         
# versions less than 1.2 used a dict of dict, named AREAS, to classify
#     geographic areas versus countries. It had this structure:
#     
#     {area_name : {'context':              'nations' | 'continents',
#                   'geoId':                geographic_identifier,
#                   'countryterritoryCode': anotherCode,
#                   'continentExp':         continent_name,
#                   'nations':              {nation_geoId: nation_name,
#                                            nation_geoId: nation_name, ...
#                                           }
#                  } ...
#     }
#
# We'll have these two query patterns:
#     where target is to obtain a dataframe with only the necessary rows
#     by nations or continents,
#     and "area" could be a federation of nations (EU), or a subcontinent:
#
#     1 - nations + areas + date
#         subset rows by date
#         create rows by area         (note: context=='nations')
#         subset rows by nations
#         append area rows to nations rows
#     
#     2 - continents + subcontinents + dates
#         subset rows by date          (note: this is as 1st row in the above pattern)
#         create rows by subcontinents (note: this is the same of "create rows by area", but with context=='continents')
#         subset rows by continents
#         append subcontinents rows to continents rows (note: this is as last row in above pattern)
#
# Given a dataframe with only the necessary nations/continents, we need:
#
#     a. drop unnecessary columns                 (subset_cols)
#     b. add other columns as daily cases ...     (add_cols)
#     c. calculate cumulative sum of cases and deaths by nation/continent (calculate_cumulative_sum)

# std libs import
from datetime import datetime, date, timedelta
from math     import ceil
import json

# 3rd parties libs import
import click
from flask       import current_app, g
from flask_babel import _
#from flask_babel import lazy_gettext as _l
#from flask_babel import get_locale
from flask.cli   import with_appcontext

import pandas as pd
import numpy  as np

POP_FIELD = ''         # placeholder to register the population field name

# START GeoEntities as {geoId: {"population": nnnn, ...}, ....}
#    in this version we rationalize Nations+Continents+AREAS
class MC(type):
    def __contains__(self, key):
        return self.__class_contains__(self, key)
        
    def __len__(self):
        return self.__class_len__(self)
    
    def __repr__(self):
        return self.__class_repr__(self)
    
    def __str__(self):
        return self.__class_repr__(self)
    

class GeoEntities(object, metaclass=MC):
    '''a class of geographic entities
    
    remarks.
        - it uses a dict of dict as class as a protected attribute
        - actual dict structure:
            geoId: { "type":             "nation" | "continent",
                     "original_country": true |false,
                     "name":             aname,
                     "population":       anumber,
                     "countryterritoryCode": another_code,
                     "continentExp":     continent,
                     "nations":          a list of geoId(s)
                   }
    '''
    
    _entities = dict()
    
    @classmethod
    def set_entity(cls, id, value):
        '''set a single entity'''
        if type(value) is not type(dict()):
            raise ValueError('setting geographic entity requires a <dict> as value, not {}'.format(type(value)))
        cls._entities[id] = value
        
    @classmethod
    def get_entity(cls, id):
        '''get a single entity by id'''
        return cls._entities.get(id, None)

    @classmethod
    def del_entity(cls, id):
        '''delete a single entity by id'''
        cls._entities.pop(id, None)
        
    @classmethod
    def set_entity_att(cls, id, attribute, value):
        '''set a single entity attribute'''
        e = cls._entities.get(id, None)
        if e is not None:
            e[attribute] = value
        else:
            cls.set_entity(id, {attribute: value})

    @classmethod
    def get_entity_att(cls, id, attribute):
        '''get a single entity attribute'''
        e = cls._entities.get(id, None)
        if e is not None:
            return e.get(attribute, None)
        return None
    
    @classmethod
    def del_entity_att(cls, id, attribute):
        '''delete a single entity attribute'''
        e = cls._entities.get(id, None)
        if e is not None:
            e.pop(attribute, None)

    @classmethod
    def load_from_json(cls, fname):
        with open(fname, 'r') as f:
            cls._entities = json.load(f)
        
    @classmethod
    def write_to_json(cls, fname):
        with open(fname, 'w') as f:
            json.dump(cls._entities, f)
    
    #classmethod from MC
    def  __class_contains__(cls, key):
        return key in cls._entities
    
    #classmethod from MC
    def __class_repr__(self):          # here the self object is the class, NOT a GeoIdentities instance
        #return str(GeoEntities._entities)   # as a memo
        return str(self._entities)
        
    #classmethod from MC
    def __class_len__(self):          # as above: here the self object is the class
        return len(self._entities)

    def __contains__(self, key):
        return key in self.ids

    def __init__(self, ids=None, attribute=None, value=None):
        mname = '__init__'
        if ids is not None:
            self.ids = []
            for id in ids:
                if id in self.__class__:
                    self.ids.append(id)
                else:
                    raise ValueError(_('%(theclass)s.%(method)s: identifier %(id)s is unknown in nations and areas', theclass=self.__class__.__name__, method=mname, id=id))
        else:
            self.ids = list(self.__class__._entities.keys())
        if attribute is not None and value is not None:
            self.ids = self._get_entities_by_att(attribute=attribute, value=value)
            
    def __getitem__(self, key):
        mname = '__getitem__'
        if key in self.ids:
            return self.__class__.get_entity(key)
        else:
            raise KeyError(_('%(theclass)s.%(method)s: identifier %(id)s is not in this set of geographic entities', theclass=self.__class__.__name__, method=mname, id=key))
            
    def keys(self):
        return self.ids
        
    def values(self):
        result = []
        for id in self.ids:
            result.append(self.__class__.get_entity(id))
        if result == []:
            result = None
        return result
    
    def get_entities_by_att(self, attribute, value):
        '''modify self from an initial group of entities excluding
           identities with attribute of different value from given parameter
           
           parameters
               - attribute     str - key to use
               - value         obj - value to compare; it must be equal

           returns
               - self
        '''
        if attribute is not None and value is not None:
            self.ids = self._get_entities_by_att(attribute, value)
        return self
    
    def _get_entities_by_att(self, attribute, value):
        '''get a group of entities (as e list of identities) 
           with attribute of indicated value
           
           parameters
               - attribute     str - key to use
               - value         obj - value to compare; it must be equal
           
           return
               - nids          list of str - identities with equal values
                                   by the given attribute | None
           
           remark
               - self.ids      list of str - list of self's identities
        '''

        nids = []                     # new ids
        for id in self.ids:       
            e = self.__class__.get_entity(id)
            vatt = e.get(attribute, None)
            if vatt is not None and vatt==value:
                nids.append(id)
        if nids == []:
            nids = None
            
        return nids

    def get_entities_att(self, attribute):
        '''get a single entity attribute'''
        result = dict()
        for id in self.ids:
            e = self.__class__.get_entity(id)
            if e is not None:
                val = e.get(attribute, None)
                result[id] = val
        if len(result) == 0:
            result = None
        return result


    def get_list_of_keys_names(self, names_only=False):
        ''' from self, extract (key, name,) pairs'''
        fname = 'get_list_of_keys_names'
        resp = []
        for id in self.ids:
            name = self.__class__.get_entity_att(id,'name')
            if names_only:
                resp.append(name)
            else:
                resp.append((id, name))
        return tuple(resp)
    
    def __repr__(self):          # here the self object is the class, NOT a GeoIdentities instance
        return str(self.ids)

    def __len__(self):          # as above: here the self object is the class
        return len(self.ids)

# END   GeoEntities as {name: {"population": nnnn, ...}, ....}


def subset_cols(df, cols, direct=True):
    '''
    '''
    df_result = df.copy(deep=True)
    all_cols = list(df.columns)
    for col in all_cols:
        if col in cols:
            if direct:
                continue
            else:
                del df_result[col]
        else:
            if direct:
                del df_result[col]
            
    return df_result


def add_cols(df, cols):
    '''add columns to dataframe
    
    params:
        - df         pandas dataframe - with original data
        - cols       list of str - accepted values for str: 'cases/day' | '\N{Greek Capital Letter Delta}cases/day'
        
    return:
        - df_result  pandas dataframe - with the requested columns
    '''
    fname = 'add_cols'
    df_result = df.copy(deep=True)
    for col in cols:
        if col == 'cases/day':
            df_result[col] = df_result['cases']
        elif col == '\N{Greek Capital Letter Delta}cases/day':
            df_result[col] = df_result['cases'] - df_result['cases'].shift(-1)
        else:
            raise ValueError(_('%(function)s: field %(field)s not known', function=fname, field=col))
    
    return df_result


def calculate_cumulative_sum(df, fields, normalize=False):
    '''give a dataframe with cumulative sums
    
    parameters:
        - df              pandas dataframe - with daily data
        - fields          list of str - fields to sum ('cases' &| 'deaths')
        
    returns:
        - df_result       pandas dataframe - with cumulative data
    '''
    #cols = ['dateRep', 'countriesAndTerritories']
    #cols.extend(fields)
    
    #df_result = df.loc[:, cols]
    
    df_result = df.copy(deep=True)
    df_result = pd.pivot_table(df_result, index='dateRep', columns='countriesAndTerritories')

    for field in fields:
        df_result[field] = df_result[field].cumsum()
    if normalize:
        for field in fields:
            df_result[field] = df_result[field]/df_result[POP_FIELD]
        del df_result[POP_FIELD]
        
    return df_result


#< WARNING this function could "drop" one or more nation(s) if it cannot handle a good
#      pair of days as "take off" point. maybe in future it is necessary to study
#      this case
def calculate_cumulative_sum_with_overlap(df, column= 'cases', threshold=200, normalize=False):
    '''pivot a dataframe iterating over columns and dates traslating values to start at the same date
    
    params 
        - df                     pandas dataframe MultiIndex: dateRep+countriesAndTerritories
        - column                 str - column with values to check: cases|deaths
        - threshold              int - value to overcome for two consecutive days
        - normalize              bool - if True calculate ratio to population 
    
    return
        - sdf          pandas dataframe
        - or None      in case of empty dataframe
    
    remark.
      in this function input dataframe has daily cases in "cases" column. BUT this function works
      only if cases are cumulative. So we need to transform them before calculate the
      day to use to overlap.
      
      e.g. if input dataframe is
          |                                    cases
          |dateRep    countriesAndTerritories
          |2020-04-24 Afghanistan                105
          |           Albania                     29
          |2020-04-25 Afghanistan                 70
          |           Albania                     15
          |...
          |2020-04-30 Afghanistan                122
          |           Albania                     16

        we need to calculate:
          |                                    cases
          |dateRep    countriesAndTerritories
          |2020-04-24 Afghanistan                105
          |           Albania                     29
          |2020-04-25 Afghanistan                175
          |           Albania                     44
          |...
          |2020-04-30 Afghanistan                773
          |           Albania                    132
        
                 ...
      this function builds a dataframe as
                 country1 country2 ... countryN
            row
            01   10       80           100
            02   20       20           ...
            03   ...      ...          ...
      where values in country-i are the cases in that country
      
      Warning: this function is pretty slow because iterate over rows
      
      Again: to align, seach a couple of adjacent days that exceed the indicated threshold
    '''
    fname = 'calculate_cumulative_sum_with_overlap'

    ndf = df.copy(deep=True)
    # here df MUST have hierarchical index, two levels. and here we are getting dates and countries from that indices
    #     Note. the next from https://stackoverflow.com/questions/29753060/how-to-convert-numpy-datetime64-into-datetime
    dates = df.index.get_level_values('dateRep').drop_duplicates().values.astype('M8[D]').astype('O').tolist()
    countries = df.index.get_level_values('countriesAndTerritories').drop_duplicates().values.tolist()
    
    # passing from daily to cumulative
    #    thanks to https://stackoverflow.com/questions/53927460/select-rows-in-pandas-multiindex-dataframe
    idx = pd.IndexSlice
    for country in countries:
        ndf.loc[idx[:, country], column] = ndf.loc[idx[:, country], column].cumsum()

    # building an empty df ...
    sdf = pd.DataFrame(columns=[[],[]])                          # empty df, hierarchical columns (two levels)
    population = None

    #    ... iterating over countries ...
    for country in countries:
        # if normalize is true, set country's population (now on population is not none)
        if normalize:
            min_date = ndf.loc[idx[:, country], :].index.get_level_values('dateRep').min() # min date for this country
            population = ndf.loc[(min_date, country,), POP_FIELD].astype(int)
        acountry = ndf.xs(country, level='countriesAndTerritories')
        cases_list = []
        zero_flag = True                   # while true: skip to next day
        #        ... iterating over dates in a country
        for adate in dates:
            #            catch two adjacent days data
            try:
                cases = acountry.loc[adate, column]
            except:
                cases = None
            #            if we are skipping and cases is None, needless to continue, shunt the cicle
            if zero_flag and cases is None:
                continue
            #            cases is not None, get the 2nd day
            if zero_flag:
                try:
                    next_cases = acountry.loc[adate+timedelta(days=1), column]
                except:
                    next_cases = None
                
            #             if skip is true and two value are not None (cases isn't for sure) ...
            if (zero_flag and not next_cases is None):
                #         ... we check if the two values are both over threshold
                if (cases >= threshold and next_cases>= threshold):
                    zero_flag=False
                else:
                    continue
            #             if first condition is false, we check if skip is true; in such a case shunt to the for cycle
            elif zero_flag:
                continue
            #             if first condition is false, and skip is false, then we can work in the body of the for cycle
            else:
                pass
            #             preparing a list of cases
            cases = cases if cases is not None else 0
            # + ldfa,2020-09-20 in case of normalize==True we divide cases by population
            cases = cases / population if population is not None else cases
            cases_list.append(cases)
             #            if not last date, cicle, else add column to dataframe
            if adate+timedelta(days=1) in dates:
                continue
            else:
                # if new column is higher of dataframe, we need to stretch it, otherwise new column will be cutted
                if sdf.shape[1] > 0 and (sdf.shape[0] < len(cases_list)):
                    sdf = stretch(sdf, len(cases_list))
                sdf[column, country] = pd.Series(cases_list).astype(int)
                #current_app.logger.debug('{}: adding ({},{}) length: {}'.format(fname, column, country, len(cases_list)))

    if sdf.columns.to_list() == []:
        sdf = None
    else:
        pass
        #for country in countries:
        #    try:
        #        sdf[(column,country,)] = sdf[(column,country,)].cumsum()
        #    except:
        #        pass

    return sdf


def stretch(df, height):
    '''raise the height of a dataframe to the requested size'''
    if df.shape[0] >= height:
        return df
    
    for ndx in range(df.shape[0], height):
        df.loc[ndx] = np.NaN * df.shape[1]
    return df


def suggest_threshold(df, column='cases', ratio=0.1):
    '''ratio of the smaller between the max cases of the countries
    
    params:
        - df                     pandas dataframe MultiIndex: dateRep+country_name_field (countries | continents)
        - column                 str - column with values to check: cases|deaths
        - ratio                  float - ratio to apply default is 10%
        
    return threshold      int 
    '''

    countries = df.index.get_level_values('countriesAndTerritories').drop_duplicates().values.tolist()
    little_country, little_cases = (countries[0], df.xs(countries[0], level='countriesAndTerritories')[column].max(), )
    
    for country in countries[1:]:
        max_cases =  df.xs(country, level='countriesAndTerritories')[column].max()
        if max_cases < little_cases:
            little_country, little_cases = (country, max_cases,)
    return ceil(little_cases * ratio)
    

def worst_countries(df, field, countries, lndx, rndx, normalize=False):
    '''return worst countries from a given list respect to a given field.
       worst means higher value of cumulative sum of field.
       Both extremes are included.
       
       parameters
           - df           pandas dataframe
           - field        str - field to analize
           - countries    list of str - geoId of countries to analize
           - lndx         int - left index, >= 1
           - rndx         int - right index, >= lndx
           - normalize    bool - if true use ratio to population
       return
           - l            list of str - geoId of countries with worst values
       
       remark. 
           - this function sorts countries list using cumulative data
                  from field. Then it returns [lndx-1 : rndx] positions from 
                  the sorted countries list.
           - must be rndx < lndx
    '''
    fname = 'worst_countries'
    if lndx<=0 or rndx<=0 or lndx > rndx:
        raise ValueError(_('%(function)s: left (%(lndx)s) and/or right (%(rndx)s) indexes have not acceptable value(s)', function=fname, lndx=lndx, rndx=rndx))
        
    if lndx>len(countries) or rndx>len(countries):
        raise ValueError(_('%(function)s: left (%(lndx)s) and/or right (%(rndx)s) indexes cannot be greater than len of countries (%(lencountries)s', function=fname, lndx=lndx, rndx=rndx, lencountries=len(countries)))

    if rndx-lndx-1>=len(countries):
        return countries[:]
    
    # make a copy, expand it by eventual areas nations, drop unnecessary columns (we need field and geoId only)
    ndf = df.copy()
    
    areas = []                                                    # START expand it by eventual areas nations
    for country in countries:
        try:
            if len(GeoEntities.get_entity_att(country, 'nations')) > 1:
                areas.append(country)
        except:
            pass
    if len(areas) > 0:
        areas_df = create_rows_by_areas(df, areas, 'nations')
        ndf = pd.concat([ndf, areas_df])                          # END   expand it by eventual areas nations
        
    columns = ndf.columns.to_list()
    columns.remove(field)
    columns.remove('geoId')
    ndf = ndf.drop(columns, axis='columns')
    
    # remove unwanted countries, groub by country and sum field column
    ndf = ndf[ndf['geoId'].isin(countries)]
    ndf = ndf.groupby(['geoId'])[field].sum()     # this is a pandas series with country as index, cells are int64
    
    if normalize:
        ndf = ndf.astype(np.float64)             # from int64 to float64 otherwise we'll get zeroes
        ndf_index = ndf.index.to_list()
        for country in ndf_index:
            #ndf.at[country] /= GeoEntities.get_entity_att(country, 'population')
            try:
                ndf.at[country] = ndf.at[country] / GeoEntities.get_entity_att(country, 'population')
            except:
                ndf = ndf.drop(index=country)
    
    # sort in descending order and we get first how_many index
    ndf = ndf.sort_values(ascending=False)
    l   =  ndf.index.to_list()[lndx-1:rndx]
    return l


def get_areas(ids, direct=True):
    '''return a list with areas (i.e. NOT ORIGINAL) identities present in ids
    
    parameters:
        - ids             list of str - identities to check
        - direct          bool - if true return a list of areas present in ids
                                 otherwise the inverse, i.e. original identites
        
    retun: result_ids     list of str - as requested
    
    remark.
        - Here (not) original means geographical entity is (not) derived
            from the dataframe with infection's data. Dataframe downloaded from ECDC:
            https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide
    '''
    result_ids = []
    for id in ids:
        # - ldfa,2020-09-29 passing to GeoEntities
        #if ( (direct and is_id_in_areas(id))
        #     or
        #     (not direct and not is_id_in_areas(id))
        #   ):
        original = GeoEntities.get_entity_att(id, 'original_country')
        if ((direct and original==False) or 
           (not direct and original==True)):
            result_ids.append(id)
    return result_ids


def create_rows_by_continents(df, ids, pop_field='popData2019'):
    '''create rows where continentExp value is in ids
    
    parameters:
        - df              pandas dataframe - to subset
                              see heading comment in this module to get this dataframe format
        - ids             list of str - names of continents to select
    
    return:
        - ndf             (new) pandas dataframe - subset of df
        
    rem: this is very similar to create_rows_by_areas, but here an there
         there are small differences. So, for sake of readability, I've
         decided to duplicate some code
    '''
    df_result = pd.DataFrame()
    for id in ids:
        df_tmp = pd.DataFrame()
        df_nrc = df[df['continentExp']==id]
        # ... calculating area population
        grouped = df_nrc.groupby(by='dateRep', as_index=False)
        population = df_nrc[['countriesAndTerritories', pop_field]].drop_duplicates().sum()[pop_field]
        # ... grouping by date and adding new cols to new df
        grouped = df_nrc.groupby(by='dateRep', as_index=False)
        df_tmp['dateRep'] = grouped.groups       # 1st col: dates
        df_tmp = df_tmp.reset_index()            #
        del df_tmp['index']
        df_tmp['day'] = df_tmp['dateRep'].map(lambda x: x.day)
        df_tmp['month'] = df_tmp['dateRep'].map(lambda x: x.month)
        df_tmp['year'] = df_tmp['dateRep'].map(lambda x: x.year)
    
        df_tmp['cases'] = grouped.sum()['cases']
        df_tmp['deaths'] = grouped.sum()['deaths']
        
        df_tmp['countriesAndTerritories'] = id[:]
        df_tmp['geoId']                   = id[:]
        df_tmp['countryterritoryCode']    = id[:]
        df_tmp[pop_field]                 = population
        df_tmp['continentExp']            = id[:]
        # adding continent's data to final result (all continents)
        df_result = pd.concat([df_result, df_tmp])
    return df_result


def subset_rows_by_nations(df, ids):
    '''get rows where geoId value is in ids
    
    parameters:
        - df              pandas dataframe - to subset
                              see heading comment in this module to get this dataframe format
        - ids             list of str - codes of nations to select
    
    return:
        - ndf             (new) pandas dataframe - subset of df
    '''
    
    return df[df['geoId'].isin(ids)]


def create_rows_by_areas(df, ids, context, pop_field='popData2019'):
    '''create rows of given areas ids
    
    parameters:
        - df              pandas dataframe - containing raw data
                              see heading comment in this module to get this dataframe format
        - ids             list of str - identities of areas
        - context         str - 'nations' | 'continents'
        - pop_field       str - field name to store area's population
        
    return:
        - result_df       pandas dataframe - with data of given areas,
                              same format of originating df
    '''
    df_result = pd.DataFrame()
    
    for id in ids:          # for every area's id
        df_tmp = pd.DataFrame()
        # getting area's countries
        # - ldfa,2020-09-28 passing to GeoEntities
        #area_name = areas_get_nation_name(id, context)
        area_name = GeoEntities.get_entity_att(id, 'name')
        if area_name is None:
            continue
        # - ldfa,2020-09-28 passing to GeoEntities
        #localities = [ k for k in AREAS[area_name]['nations'].keys()]   # ids of countries forming area
        localities = GeoEntities.get_entity_att(id, 'nations')
        # ... calculating area population
        df_nrc  = df[df['geoId'].isin(localities)] 
        
        # - ldfa,2020-09-28 passing to GeoEntities
        #population = df_nrc[['countriesAndTerritories', pop_field]].drop_duplicates().sum()[pop_field]
        
        # ... grouping by date and adding new cols to new df
        grouped = df_nrc.groupby(by='dateRep', as_index=False)
        df_tmp['dateRep'] = grouped.groups       # 1st col: dates
        df_tmp = df_tmp.reset_index()            #
        del df_tmp['index']
        df_tmp['day'] = df_tmp['dateRep'].map(lambda x: x.day)
        df_tmp['month'] = df_tmp['dateRep'].map(lambda x: x.month)
        df_tmp['year'] = df_tmp['dateRep'].map(lambda x: x.year)
    
        df_tmp['cases'] = grouped.sum()['cases']
        df_tmp['deaths'] = grouped.sum()['deaths']
        
        df_tmp['countriesAndTerritories'] = area_name[:]
        # - ldfa,2020-09-29 passing to GeoEntities
        #df_tmp['geoId']                   = AREAS[area_name]['geoId']
        #df_tmp['countryterritoryCode']    = AREAS[area_name]['countryterritoryCode']
        #df_tmp[pop_field]                 = population
        #df_tmp['continentExp']            = AREAS[area_name]['continentExp']

        df_tmp['geoId']                   = id[:]
        df_tmp['countryterritoryCode']    = GeoEntities.get_entity_att(id, 'countryterritoryCode')
        df_tmp[pop_field]                 = GeoEntities.get_entity_att(id, 'population')
        df_tmp['continentExp']            = GeoEntities.get_entity_att(id, 'continentExp')

        # adding area's data to final result (all areas)
        df_result = pd.concat([df_result, df_tmp])
    return df_result


def select_rows_by_dates(df, first, last, remember=False):
    '''drops rows with date out of the indicated [first, last] time interval
    
    params:
        -df          pandas dataframe - to analize
        - first      datetime.date - left extreme of time interval
        - last       datetime.date - right extreme of time interval
        - remember   bool - if true sum values in dropped rows on the 1st surviving row
                            considering countriesAndTerritories field as a grouping criterion
    
    return a new pandas dataframe
    '''
    fname = 'select_rows_by_dates'
    min_date = df['dateRep'].min()
    ti_df = df[(df['dateRep']>=first) & (df['dateRep']<=last)]    # result candidate: time interval dataframe; this has rows in indicated time interval
    if not remember or first <= min_date:
        result= ti_df
    else:
        # here we calculate cases and deaths totals for every country ...
        base_df = df[(df['dateRep']<first)]
        cols_to_drop = [col for col in base_df.columns.to_list() if col not in {'countriesAndTerritories', 'cases', 'deaths',}]
        base_df = base_df.drop(cols_to_drop, axis='columns')
        base_df = base_df.set_index('countriesAndTerritories').groupby(level=[0]).sum()  # ... this is: country (as index), (total)cases, (total)deaths
        
        # ... and now we need sum up these totals on the min day of each country
        ti_df2 = ti_df.set_index(['countriesAndTerritories', 'dateRep'])
        for country in base_df.index.to_list():
            try:
                country_min_date = ti_df[(ti_df['countriesAndTerritories']==country)]['dateRep'].min()
                ti_df2.at[(country, country_min_date,), 'cases']  = ti_df2.at[(country, country_min_date,), 'cases'] + base_df.at[country, 'cases']
                ti_df2.at[(country, country_min_date,), 'deaths'] = ti_df2.at[(country, country_min_date,), 'deaths'] + base_df.at[country, 'deaths']
            except:
                pass
        result = ti_df2.reset_index()             # ... and here we have result, with cases and deaths of days before first summed up to first
   
    return result


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
    global POP_FIELD
    
    POP_FIELD = app.config['POP_FIELD'][:]
    geoe = app.config['DATA_DIR'][:] +'/'+ app.config['GEOE_FILE'][:] # geoEntities filename path
    GeoEntities.load_from_json(geoe)
    app.teardown_appcontext(close_df)
    

# + ldfa,2020.09.14 classifing context values for select
CONTEXT_SELECT = ('nations', 'continents',)


# START section about deleted code

# - ldfa,2020-09-29 not used
#def get_geographic_name(id, nations, areas=None):
#    '''
#    parameters:
#        - id         str - identifier of nation or continents; they could be areas
#        - nations    istance of class Nations
#        - areas      dict of dict - as AREAS
#    '''
#    fname = 'get_geographic_name'
#    if areas is None: areas = AREAS
#    name = None
#    
#    if id in nations:                        # this is a continent, it is name==id
#        name = id[:]
#    elif nations.get_nation_name(id):        # this is a nation
#        name = nations.get_nation_name(id)[:]
#    elif areas_get_nation_name(id, 'nations', areas=areas):
#        name = areas_get_nation_name(id, 'nations', areas=areas)[:]
#    elif areas_get_nation_name(id, 'continents', areas=areas):
#        name = areas_get_nation_name(id, 'continents', areas=areas)[:]
#    else:
#        raise ValueError(_('%(function)s: identifier %(id)s is unknown in nations and areas', function=fname, id=id))
#    
#    return name


# - ldfa,2020-0929 not used
#def get_geographic_names(ids, nations, areas=None):
#    '''
#    parameters:
#        - ids        list of str - identifiers of nation or continents; they could be areas
#        - nations    istance of class Nations
#        - areas      dict of dict - as AREAS
#    '''
#    fname = 'get_geographic_names'
#    
#    #if areas is None: areas = AREAS
#    names = []
#    for id in ids:
#        name = get_geographic_name(id, nations, areas=areas)
#        if id is not None:
#            names.append(name)
#        else:
#            raise ValueError(_('%(function)s: identifier %(id)s is unknown in nations and areas', function=fname, id=id))
#    if names == []: names = None
#    return names

#< TODO delete this, passing to GeoEntites
#class Nations(object):
#    '''an istance of this class lists all nations present in dataframe,
#    with their continent
#    
#    remark: it uses a (self.__n__) dictionary with this structure:
#        {continent_name: {nation_id: nation_name,
#                          nation_id: nation_name,
#                          ...
#                         }
#         ...
#        }
#    '''
#
#    def __init__(self, csv_file=None, dataframe=None):
#        self.__n__ = dict()
#        df = None
#        if csv_file is not None:
#            df = pd.read_csv(csv_file)
#        elif dataframe is not None:
#            df = dataframe
#        if df is not None:
#            cdf = df[['countriesAndTerritories', 'geoId', 'continentExp']].drop_duplicates()
#            for row, c in cdf.iterrows():           # row, country:(name, id,, continent)
#                self.add_nation(c[2], c[1], c[0])      # continent, id, name
#
#    def __setitem__(self, key, item):
#        self.__n__[key] = item
#
#    def __getitem__(self, key):
#        return self.__n__[key]
#
#    def __repr__(self):
#        return repr(self.__n__)
#
#    def __len__(self):
#        return len(self.__n__)
#
#    def __delitem__(self, key):
#        del self.__n__[key]
#
#    def get(self, key, default=None):
#        if key in self.__n__:
#            return self.__n__[key]
#        else:
#            return None
#
#    def has_key(self, k):
#        return k in self.__n__
#
#    def update(self, *args, **kwargs):
#        return self.__dict__.update(*args, **kwargs)
#
#    def keys(self):
#        return self.__n__.keys()
#
#    def values(self):
#        return self.__n__.values()
#
#    def items(self):
#        return self.__n__.items()
#
#    def pop(self, *args):
#        return self.__n__.pop(*args)
#
#    def __cmp__(self, dict_):
#        return self.__cmp__(self.__n__, dict_)
#
#    def __contains__(self, item):
#        return item in self.__n__
#
#    def __iter__(self):
#        return iter(self.__n__)
#
#    def __unicode__(self):
#        return repr(self.__n__)
#
#    def get_for_select(self, continents=None):
#        '''create a list of 2-tuple (id,nations,) of indicated continents
#        
#        params:
#            - continents              str or list of str - a single continent, or 
#                                          a list of continents; if None we get all continents
#        
#        return: a list of 2-tuple (id,nations,) of indicated continents
#        '''
#        l = []
#        if continents is None:
#            continents = list(self.__n__.keys())
#        elif type(continents) == type([]):
#            pass
#        else:
#            continents = [continents]
#        
#        for continent in continents:
#            l.extend( [(id, name) for id, name in self.__n__[continent].items()] )
#        l.sort(key = lambda x: x[1])
#        return l
#        
#    def get_for_list(self, continents=None):
#        '''create a list of nations of indicated continents
#        
#        params:
#            - params                str or list of str - a single continent, or 
#                                        a list of continents; if None we get all continents
#        
#        return: a list of names of nations belonging to the indicated continents
#        '''
#        l = []
#        if continents is None:
#            continents = list(self.__n__.keys())
#        elif type(continents) == type([]):
#            pass
#        else:
#            continents = [continents]
#        
#        for continent in continents:
#            l.extend([name for id, name in self.__n__[continent].items()])
#        l.sort()
#        return l
#
#    def add_nation(self, continent, id, name):
#        ''' add a single nation
#        
#        params:
#            - continent       str - continent name
#            - id              str - identifier of nation
#            - name            str - name of nation
#            
#        return None
#        '''
#        if continent not in self.__n__:
#            self.__n__[continent] = dict()
#        self.__n__[continent][id] = name
#
#    def get_nation_name(self, id, default=None):
#        ''' get a single nation by id
#        
#        params:
#            - continent       str - continent name
#            - id              str - identifier of nation
#            - name            str - name of nation
#            
#        return name    str - nation name
#        '''
#        name = None
#        continents = list(self.__n__.keys())
#        for continent in continents:
#            name = self.__n__.get(continent).get(id, None)
#            if name is not None:
#                break
#        if name is None:
#            name = default
#            
#        return name

#< TODO delete this, passing to GeoEntites
# +- ldfa,2020-09-14 renamed contest to context
# + ldfa,2020-05-11 geographical areas definitions: federations, subcontinents, supercontinents, or otherwise.
# Note. Here US is a single nation, not a federation. We haven't the US nations data about cases and deaths.
# In every case, federation (EU) or subcontinent, key is 'countriesAndTerritories' field
#AREAS = {'European_Union': {'context': 'nations',
#                            'geoId':      'EU',
#                            'countryterritoryCode': 'EU',
#                            'continentExp': 'Europe',
#                            'nations': { "AT": "Austria",
#                                         "BE": "Belgium",  
#                                         "BG": "Bulgaria",  
#                                         "HR": "Croatia",  
#                                         "CY": "Cyprus",  
#                                         "CZ": "Czechia",  
#                                         "DK": "Denmark",  
#                                         "EE": "Estonia",  
#                                         "FI": "Finland",  
#                                         "FR": "France",  
#                                         "DE": "Germany",  
#                                         "EL": "Greece", 
#                                         "HU": "Hungary", 
#                                         "IE": "Ireland", 
#                                         "IT": "Italy", 
#                                         "LV": "Latvia", 
#                                         "LT": "Lithuania", 
#                                         "LU": "Luxembourg", 
#                                         "MT": "Malta", 
#                                         "NL": "Netherlands", 
#                                         "PL": "Poland", 
#                                         "PT": "Portugal", 
#                                         "RO": "Romania", 
#                                         "SK": "Slovakia", 
#                                         "SI": "Slovenia", 
#                                         "ES": "Spain", 
#                                         "SE": "Sweden", 
#                                       },
#                           },
#         'Central_America':{'context': 'continents',
#                            'geoId':   'Central_America',                 # MUST be equal to name
#                            'countryterritoryCode': 'Central_America',
#                            'continentExp': 'Central_America',            # MUST be equal to name
#                            'nations': { "BZ": "Belize",
#                                         "CR": "Costa_Rica",
#                                         "SV": "El_Salvador",
#                                         "GT": "Guatemala",
#                                         "HN": "Honduras",
#                                         "NI": "Nicaragua",
#                                         "PA": "Panama",
#                                       },
#                           },
#         'North_America':{'context': 'continents',
#                          'geoId':   'North_America',                 # MUST be equal to name
#                          'countryterritoryCode': 'North_America',
#                          'continentExp': 'North_America',            # MUST be equal to name
#                          'nations': { "CA": "Canada",
#                                       "US": "United_States_of_America",
#                                       "AG": "Antigua_and_Barbuda",
#                                       "BS": "Bahamas",
#                                       "BB": "Barbados",
#                                       "BZ": "Belize",
#                                       "CU": "Cuba",
#                                       "DM": "Dominica",
#                                       "DO": "Dominican_Republic",
#                                       "GD": "Grenada",
#                                       "HT": "Haiti",
#                                       "JM": "Jamaica",
#                                       "MX": "Mexico",
#                                       "KN": "Saint_Kitts_and_Nevis",
#                                       "LC": "Saint_Lucia",
#                                       "VC": "Saint_Vincent_and_the_Grenadines",
#                                       "TT": "Trinidad_and_Tobago",
#                                       "AI": "Anguilla",
#                                       "BM": "Bermuda",
#                                       "VG": "British_Virgin_Islands",
#                                       "KY": "Cayman_Islands",
#                                       "MS": "Montserrat",
#                                       "PR": "Puerto_Rico",
#                                       "TC": "Turks_and_Caicos_islands",
#                                       "VI": "United_States_Virgin_Islands",
#                                       "BQ": "Bonaire, Saint Eustatius and Saba",
#                                       "CW": "Curaçao",
#                                       "GL": "Greenland",
#                                       "SX": "Sint_Maarten",
#                                     },
#                         },
#         'South_America':{'context': 'continents',
#                          'geoId':   'South_America',                 # MUST be equal to name
#                          'countryterritoryCode': 'South_America',
#                          'continentExp': 'South_America',            # MUST be equal to name
#                          'nations': { "CO": "Colombia",
#                                       "VE": "Venezuela",
#                                       "GY": "Guyana",
#                                       "SR": "Suriname",
#                                       "BR": "Brazil",
#                                       "PY": "Paraguay",
#                                       "UY": "Uruguay",
#                                       "AR": "Argentina",
#                                       "CL": "Chile",
#                                       "BO": "Bolivia",
#                                       "PE": "Peru",
#                                       "EC": "Ecuador",
#                                       "FK": "Falkland_Islands_(Malvinas)",
#                                       #"GF": "French Guiana",
#                                     },
#                         },
#         'World':{'context': 'continents',
#                 'geoId':   'World',                 # MUST be equal to name
#                 'countryterritoryCode': 'World',
#                 'continentExp': 'World',            # MUST be equal to name
#                 'nations': {'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria',
#                             'AD': 'Andorra', 'AO': 'Angola', 'AI': 'Anguilla',
#                             'AG': 'Antigua_and_Barbuda', 'AR': 'Argentina', 'AM': 'Armenia',
#                             'AW': 'Aruba', 'AU': 'Australia', 'AT': 'Austria',
#                             'AZ': 'Azerbaijan', 'BS': 'Bahamas', 'BH': 'Bahrain',
#                             'BD': 'Bangladesh', 'BB': 'Barbados', 'BY': 'Belarus',
#                             'BE': 'Belgium', 'BZ': 'Belize', 'BJ': 'Benin',
#                             'BM': 'Bermuda', 'BT': 'Bhutan', 'BO': 'Bolivia',
#                             'BQ': 'Bonaire, Saint Eustatius and Saba', 'BA': 'Bosnia_and_Herzegovina',
#                             'BW': 'Botswana', 'BR': 'Brazil', 'VG': 'British_Virgin_Islands',
#                             'BN': 'Brunei_Darussalam', 'BG': 'Bulgaria', 'BF': 'Burkina_Faso',
#                             'BI': 'Burundi', 'KH': 'Cambodia', 'CM': 'Cameroon',
#                             'CA': 'Canada', 'CV': 'Cape_Verde', 'JPG11668': 'Cases_on_an_international_conveyance_Japan',
#                             'KY': 'Cayman_Islands', 'CF': 'Central_African_Republic', 'TD': 'Chad',
#                             'CL': 'Chile', 'CN': 'China', 'CO': 'Colombia',
#                             'KM': 'Comoros', 'CG': 'Congo', 'CR': 'Costa_Rica',
#                             'CI': 'Cote_dIvoire', 'HR': 'Croatia', 'CU': 'Cuba',
#                             'CW': 'Curaçao', 'CY': 'Cyprus', 'CZ': 'Czechia',
#                             'CD': 'Democratic_Republic_of_the_Congo',
#                             'DK': 'Denmark', 'DJ': 'Djibouti', 'DM': 'Dominica',
#                             'DO': 'Dominican_Republic', 'EC': 'Ecuador', 'EG': 'Egypt',
#                             'SV': 'El_Salvador', 'GQ': 'Equatorial_Guinea', 'ER': 'Eritrea',
#                             'EE': 'Estonia', 'SZ': 'Eswatini', 'ET': 'Ethiopia',
#                             'FK': 'Falkland_Islands_(Malvinas)', 'FO': 'Faroe_Islands', 'FJ': 'Fiji',
#                             'FI': 'Finland', 'FR': 'France', 'PF': 'French_Polynesia',
#                             'GA': 'Gabon', 'GM': 'Gambia', 'GE': 'Georgia',
#                             'DE': 'Germany', 'GH': 'Ghana', 'GI': 'Gibraltar',
#                             'EL': 'Greece', 'GL': 'Greenland', 'GD': 'Grenada',
#                             'GU': 'Guam', 'GT': 'Guatemala', 'GG': 'Guernsey',
#                             'GN': 'Guinea', 'GW': 'Guinea_Bissau', 'GY': 'Guyana',
#                             'HT': 'Haiti', 'VA': 'Holy_See', 'HN': 'Honduras',
#                             'HU': 'Hungary', 'IS': 'Iceland', 'IN': 'India',
#                             'ID': 'Indonesia', 'IR': 'Iran', 'IQ': 'Iraq', 
#                             'IE': 'Ireland', 'IM': 'Isle_of_Man', 'IL': 'Israel',
#                             'IT': 'Italy', 'JM': 'Jamaica', 'JP': 'Japan',
#                             'JE': 'Jersey', 'JO': 'Jordan', 'KZ': 'Kazakhstan', 
#                             'KE': 'Kenya', 'XK': 'Kosovo', 'KW': 'Kuwait', 
#                             'KG': 'Kyrgyzstan', 'LA': 'Laos', 'LV': 'Latvia',
#                             'LB': 'Lebanon', 'LS': 'Lesotho', 'LR': 'Liberia',
#                             'LY': 'Libya', 'LI': 'Liechtenstein', 'LT': 'Lithuania',
#                             'LU': 'Luxembourg', 'MG': 'Madagascar', 'MW': 'Malawi',
#                             'MY': 'Malaysia', 'MV': 'Maldives', 'ML': 'Mali',
#                             'MT': 'Malta', 'MR': 'Mauritania', 'MU': 'Mauritius',
#                             'MX': 'Mexico', 'MD': 'Moldova', 'MC': 'Monaco', 
#                             'MN': 'Mongolia', 'ME': 'Montenegro', 'MS': 'Montserrat', 
#                             'MA': 'Morocco', 'MZ': 'Mozambique', 'MM': 'Myanmar',
#                             'NA': 'Namibia', 'NP': 'Nepal', 'NL': 'Netherlands',
#                             'NC': 'New_Caledonia', 'NZ': 'New_Zealand', 'NI': 'Nicaragua',
#                             'NE': 'Niger', 'NG': 'Nigeria', 'MK': 'North_Macedonia',
#                             'MP': 'Northern_Mariana_Islands', 'NO': 'Norway', 'OM': 'Oman',
#                             'PK': 'Pakistan', 'PS': 'Palestine', 'PA': 'Panama', 
#                             'PG': 'Papua_New_Guinea', 'PY': 'Paraguay', 'PE': 'Peru', 
#                             'PH': 'Philippines', 'PL': 'Poland', 'PT': 'Portugal', 
#                             'PR': 'Puerto_Rico', 'QA': 'Qatar', 'RO': 'Romania', 
#                             'RU': 'Russia', 'RW': 'Rwanda', 'KN': 'Saint_Kitts_and_Nevis', 
#                             'LC': 'Saint_Lucia', 'VC': 'Saint_Vincent_and_the_Grenadines', 
#                             'SM': 'San_Marino', 'ST': 'Sao_Tome_and_Principe', 'SA': 'Saudi_Arabia', 
#                             'SN': 'Senegal', 'RS': 'Serbia', 'SC': 'Seychelles', 
#                             'SL': 'Sierra_Leone', 'SG': 'Singapore', 'SX': 'Sint_Maarten', 
#                             'SK': 'Slovakia', 'SI': 'Slovenia', 'SO': 'Somalia', 
#                             'ZA': 'South_Africa', 'KR': 'South_Korea', 'SS': 'South_Sudan', 
#                             'ES': 'Spain', 'LK': 'Sri_Lanka', 'SD': 'Sudan', 
#                             'SR': 'Suriname', 'SE': 'Sweden', 'CH': 'Switzerland', 
#                             'SY': 'Syria', 'TW': 'Taiwan', 'TJ': 'Tajikistan', 
#                             'TH': 'Thailand', 'TL': 'Timor_Leste', 'TG': 'Togo', 
#                             'TT': 'Trinidad_and_Tobago', 'TN': 'Tunisia', 'TR': 'Turkey',
#                             'TC': 'Turks_and_Caicos_islands', 'UG': 'Uganda', 'UA': 'Ukraine', 
#                             'AE': 'United_Arab_Emirates', 'UK': 'United_Kingdom', 'TZ': 'United_Republic_of_Tanzania', 
#                             'US': 'United_States_of_America', 'VI': 'United_States_Virgin_Islands', 'UY': 'Uruguay',
#                             'UZ': 'Uzbekistan', 'VE': 'Venezuela', 'VN': 'Vietnam', 
#                             'EH': 'Western_Sahara', 'YE': 'Yemen', 'ZM': 'Zambia', 'ZW': 'Zimbabwe'}
#                 },
#        }


#< - ldfa, 2020-09-xx passing to GeoEntities
# +- ldfa,2020-09-14 renamed contest to context
# + ldfa 2020-05-11 managing geographic areas
#def areas_get_nation_name(geoId, context, areas=None):
#    '''get name given id from a 'geographic area definition' data structure
#    i.e. if contest=='continent' & geoId=='South_America'-> ['Colombia', 'Venezuela', ...]
#    
#    params:
#       - geoId                 str - id of area
#       - context               str - 'nations' | 'continents'
#       - areas                 dict of dict - e.g. {'European_Union': {'contest': 'nations',
#                                                                       'geoId':   'EU',
#                                                                       'countryterritoryCode': 'EU',
#                                                                       'continentExp': 'Europe',
#                                                                       'nations': ( "Austria", ...)
#                                                                      },
#                                                    'North_America':{'contest': 'continents',
#                                                                     'geoId':   'North_America',
#                                                                     'countryterritoryCode': None,
#                                                                     'continentExp': 'North_America',
#                                                                     'nations': ( "Canada", ...),
#                                                                    },
#                                                    ...
#                                                   }
#    
#    return str: nation or continent name of given geoId;
#           None if geoId not found
#    '''
#    if areas is None: areas = AREAS
#    for k, v in areas.items():
#        if v['context'] == context and v['geoId'] == geoId:
#            return k
#    return None


# +- ldfa,2020-09-14 renamed contest to context
# + ldfa 2020-05-11 managing geographic areas
#def areas_get_names(context, areas=None):
#    '''get all names given contest from a 'geographic area definition' data structure
#    i.e. if contest=='continent' -> ['North America', 'South America', ...]
#    
#    params:
#       - context               str - 'nations' | 'continents'
#       - areas                 dict of dict - see areas_get_nation_name(...) comment
#    
#    return list of str: nations or continents names;
#           None if contest not found
#    '''
#    if areas is None: areas = AREAS
#    names = []
#    for k, v in areas.items():
#        if v['context'] == context:
#            names.append(k)
#    if names == []: names= None
#    return names

# - ldfa,2020-09-29 not used
#def get_population(id, df, nations, areas=None):
#    fname = 'get_population'
#    if areas is None: areas = AREAS
#    population = None
#    
#    if id in nations:                        # this is a continent
#        pass
#    elif nations.get_nation_name(id):        # this is a nation
#        ndf = df[df['geoId']==id]
#        ndf.iloc(0)
#        name = nations.get_nation_name(id)[:]
#    elif areas_get_nation_name(id, 'nations', areas=areas):
#        name = areas_get_nation_name(id, 'nations', areas=areas)[:]
#    elif areas_get_nation_name(id, 'continents', areas=areas):
#        name = areas_get_nation_name(id, 'continents', areas=areas)[:]
#    else:
#        raise ValueError(_('%(function)s: identifier %(id)s is unknown in nations and areas', function=fname, id=id))
#    
#    return population

# - ldfa,2020-09-29 not used
#def get_geographic_characteristics(ids, df, nations, areas=None):
#    '''
#    parameters:
#        - ids        list of str - identifiers of nation or continents; they could be areas
#        - nations    istance of class Nations
#        - areas      dict of dict - as AREAS
#    '''
#    fname = 'get_geographic_characteristics'
#    if areas is None: areas = AREAS
#    result = dict()
#    for id in ids:
#        name = get_geographic_name(id, nations, areas=areas)
#        if name is not None:
#            chs = dict()
#            result[name] = chs
#            population = get_population(id, df, nations, areas=areas)
#            if population:
#                result[name]['population'] = population
#        else:
#            raise ValueError(_('%(function)s: identifier %(id)s is unknown in nations and areas', function=fname, id=id))
#    if result is dict(): result = None
#    return result


# - ldfa,2020-09-29 not used
#def is_id_in_areas(id, context=None, area=None):
#    '''returns True/False if id is in AREAS'''
#    # - ldfa, 2020-09-29 passing to GeoEntities
#    #if area==None:
#    #    area = AREAS
#    #for k, v in area.items():
#    #    if not context==None and area[k]['context']!=context:
#    #        continue
#    #    if area[k]['geoId']==id:
#    #        return True
#    if id in GeoEntities:
#        if context is not None:
#            if GeoEntities.get_entity_att(id, 'context')==context:
#                return not GeoEntities.get_entity_att(id, 'original_country')
#            else:
#                return False
#        else:
#            return not GeoEntities.get_entity_att(id, 'original_country')
#    return False

# END   section about deleted code

