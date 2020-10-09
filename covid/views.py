# :filename: covid/views.py
#   views of flask_covid project / covid application
#
# marks:   #?      something to discover
#          #<      make attention; probably: remove this line

# std libs import
from datetime import datetime, date, timedelta
from io       import StringIO
from math     import ceil

# 3rd parties libs import
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
    current_app
)
from werkzeug.exceptions import abort
from flask_babel import _
from flask_babel import lazy_gettext as _l
from flask_babel import get_locale
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import bs4    as bs
import numpy  as np
import pandas as pd

# application libs import
from . import models
from . import forms


bp = Blueprint('views', __name__)

# here we go
THRESHOLD = 200
THRESHOLD_RATIO = 0.05


# ldfa,2020-10-03 remark: max 10 colors. not good for EU
COLORS=['tab:blue',
        'tab:orange',
        'tab:green',
        'tab:red',
        'tab:purple',
        'tab:brown',
        'tab:pink',
        'tab:gray',
        'tab:olive',
        'tab:cyan']

FIRST     = ''     # this placeholder to register the 1st day available ...
LAST      = ''     #   ... and this to hold the last day available
POP_FIELD = ''     # placeholder to register the population field name
EU_NUM = 10        # placehoder

@bp.before_request
def before_request():
    '''open data when request starts'''
    global FIRST
    global LAST
    global POP_FIELD
    global EU_NUM
    current_app.logger.debug('> before_request()')
    g.locale = str(get_locale())
    df = models.open_df(current_app.config['DATA_DIR']+'/'+current_app.config['DATA_FILE'],
                        pd.read_csv,
                        models.world_shape)                     # stores dataframe in g.df
    FIRST, LAST = (df['dateRep'].min(), df['dateRep'].max(),)
    #g.nations = models.Nations(dataframe=df)  # - ldfa, 2020-10-01 passing to models.GeoEntities
    g.first_date = df['dateRep'].min()
    g.last_date = df['dateRep'].max()
    POP_FIELD = current_app.config['POP_FIELD'][:]
    EU_NUM = current_app.config['EU_NUM']


@bp.teardown_request
def teardown_request(error=None):
    '''close data after request
    
    params: error         error - use str(error) to print
    '''

    current_app.logger.debug('> teardown_request({})'.format(error))
    models.close_df(error)
    if error:
        current_app.logger.error(str(error))      # Log the error


@bp.route('/')
@bp.route('/index')
@bp.route('/index.html')
def index():
    '''section's home'''
    
    fname = 'select'
    current_app.logger.debug('> {}()'.format(fname))
    how_many = g.df['countriesAndTerritories'].drop_duplicates().count()
    
    return render_template('index.html', 
                           title=_("Covid: time trend analysis"), 
                           #NATIONS=nations.get_for_list(), 
                           FIRST=FIRST,
                           LAST =LAST,
                           HOW_MANY=how_many
                          )

#< ldfa,2020-10-04 do we need to review this one due to the use of form.process()?
#<     see other_select()
@bp.route('/select', methods=['GET', 'POST'])
def select():
    '''select what country's trend to show'''
    
    fname = 'select'
    current_app.logger.debug('> {}() by {} http method'.format(fname, request.method))
    
    form = forms.SelectForm()
    
    # builds MAIN fields selection, i.e. [(1, 'cases',), ...]
    mkeys = forms.list_delta_fields(direct=False)
    form.mfields.choices = list(zip([forms.FIELDS[key]['id'] for key in mkeys], mkeys))

    # builds SECONDARY fields selection, i.e. [(1, 'cases',), ...]
    skeys = forms.list_delta_fields(direct=True)
    form.sfields.choices = list(zip([forms.FIELDS[key]['id'] for key in skeys], skeys))
    
    #form.fields.default = ['1',] # to set a default, this does not work;
                                  #    we use the "default" parameter in the class;
                                  #    alternatively we can set data (see below)
    
    #form.context.choices = [('nations','nations',), ('continents', 'continents',),]
    form.context.choices = list(zip(models.CONTEXT_SELECT, models.CONTEXT_SELECT))
    
    # builds continents selection: [('Africa', 'Africa',), ...] + [('North_America', 'North America',), ...]
    # - ldfa,2020.09.25 using models.GeoEntities instead of g.nations
    #form.continents.choices = [ (c, c, ) for c in g.nations.keys()]
    #form.continents.choices.extend( [ (c, c, ) for c in models.AREAS.keys() if models.AREAS[c]['context']=='continents'] )
    n = models.GeoEntities(attribute='type', value='nation')             # countries
    c = models.GeoEntities(attribute='type', value='continent')             # continents
    form.continents.choices = list(c.get_list_of_keys_names())
    form.continents.choices.sort(key=lambda x: x[1])                           # sort by name
    continents = [continent for continent in c.get_entities_att('name').values()]       # this is used in render_template
    nations    = [country for country in n.get_entities_att('name').values()]       # this is used in render_template
    
    # - ldfa,2020.09.25 using models.GeoEntities instead of g.nations
    #form.countries.choices = g.nations.get_for_select()
    #form.countries.choices.extend( [ (v['geoId'], c, ) for c, v in models.AREAS.items() if models.AREAS[c]['context']=='nations'] )
    n = models.GeoEntities(attribute='type', value='nation')             # nations
    form.countries.choices = list(n.get_list_of_keys_names())
    form.countries.choices.sort(key=lambda x: x[1])            # sort by name

    if request.method=='POST':
        time_range1 = forms.Range(FIRST, LAST)   #+- ldfa fix bug #2 initializing TimeRange for POST
        form.first.validators.append(time_range1)    #+-
        form.last.validators.append(time_range1)     #+-

    if form.validate_on_submit():

        # check context: nations or continents
        context = form.context.data[:]
        if context == 'nations':
            ids = '-'.join(form.countries.data)             # here build string with nations ids: e.g. it-fr-nl
        elif context == 'continents':
            ids = '-'.join(form.continents.data)             # here build string with continents ids: e.g. Asia-Europe
        else:
            raise ValueError(_('%(function)s: %(context)s is not a valid context', function='select', context=context))
            
        # chaining names of fields to plot i.e.: 'cases-deaths-cases/day-\N{Greek Capital Letter Delta}cases/day'
        mcolumns = [forms.FIELDS[name]['sid'] for name in forms.FIELDS.keys() if forms.FIELDS[name]['id'] in form.mfields.data ]
        scolumns = [forms.FIELDS[name]['sid'] for name in forms.FIELDS.keys() if forms.FIELDS[name]['id'] in form.sfields.data ]
        all_columns = mcolumns + scolumns
        columns = '-'.join(all_columns)
        
        first = form.first.data
        last  = form.last.data
        remember = form.remember.data
        
        # type of values: normal or normalized
        normalize = form.ratio_to_population.data
        #normalize = False
        overlap   = False
        
        form.first.validators.remove(time_range1)  # fix bug #2: we need to remove timerange validators to destroy them
        form.last.validators.remove(time_range1)   #    otherwise they will be reused in succedings calls
        
        return redirect(url_for('views.draw_graph', 
                                context=context, 
                                ids=ids, 
                                fields=columns, 
                                normalize=normalize, 
                                overlap=overlap,
                                first=first,
                                last=last,
                                remember=remember
                               )
                       )
    
    try:                                           # again: removing timerange validators. see previous comment
        if time_range1 in form.first.validators:
            form.first.validators.remove(time_range1)
        if time_range1 in form.last.validators:
            form.last.validators.remove(time_range1)
    except:
        pass

    #form.fields.data = ['1']                            # this sets a default value # WRONG: ldfa,2020-10-04 see below about "How to dynamically ..."
    form.first.data = FIRST # and this sets a default date
    form.last.data  = LAST
    #current_app.logger.debug('= {} - form.first.data: {}'.format(fname, form.first.data))
    #current_app.logger.debug('= {} - form.last.data: {}'.format(fname, form.last.data))
    
    # + ldfa,2020-10-04
    #< is it necessary to review the time validators behavior?
    # next by https://stackoverflow.com/questions/31423495/how-to-dynamically-set-default-value-in-wtforms-radiofield
    # about "How to dynamically set default value in WTForms RadioField?". This is valid even for integer fields
    # after a form.field.default=nn
    #form.process()
    
    
    return render_template('select.html', 
                           title=_('Select country'), 
                           main_fields=forms.dict_delta_fields(direct=False),
                           secondary_fields=forms.dict_delta_fields(direct=True),
                           form=form,
                           nations=nations,
                           continents=continents
                          )

@bp.route('/other_select', methods=['GET', 'POST'])
def other_select():
    '''other_select address: shows some precostituited queries to selct from a form'''
    
    fname = 'other_select'
    current_app.logger.debug('{}() using {} http method'.format(fname, request.method))
    
    # NOT READY
    #return 'Sorry. World select is not implemented yet. We will fix it soon.'

    # FROM HERE we go
    form = forms.OtherSelectForm()
    
    #form.fields.choices = list(zip([forms.FIELDS[key]['id'] for key in forms.FIELDS.keys()], forms.FIELDS.keys()))
    # builds MAIN fields selection, i.e. [(1, 'cases',), ...]
    mkeys = forms.list_delta_fields(direct=False)
    form.mfields.choices = list(zip([forms.FIELDS[key]['id'] for key in mkeys], mkeys))

    # builds SECONDARY fields selection, i.e. [(1, 'cases',), ...]
    skeys = forms.list_delta_fields(direct=True)
    form.sfields.choices = list(zip([forms.FIELDS[key]['id'] for key in skeys], skeys))
    
    form.query.choices = forms.OTHER_CHOICES
    
    # TRY - ldfa,2020-10-04 does form.process() resolve this problem? No, it doesn't
    if request.method=='POST':
        #time_range1 = forms.TimeRange(FIRST, LAST)   #+- ldfa fix bug #1 initializing TimeRange for GET AND FOR POST
        time_range1 = forms.Range(FIRST, LAST)   #+- ldfa fix bug #1 initializing TimeRange for GET AND FOR POST
        form.first.validators.append(time_range1)    #+-
        form.last.validators.append(time_range1)     #+-

    if form.validate_on_submit():
        # chaining names of fields to plot
        mcolumns = [forms.FIELDS[name]['sid'] for name in forms.FIELDS.keys() if forms.FIELDS[name]['id'] in form.mfields.data ]
        scolumns = [forms.FIELDS[name]['sid'] for name in forms.FIELDS.keys() if forms.FIELDS[name]['id'] in form.sfields.data ]
        all_columns = mcolumns + scolumns
        columns = '-'.join(all_columns)
        
        normalize = form.ratio_to_population.data
        overlap   = False
        
        # getting time range
        first = form.first.data
        last  = form.last.data
        remember = form.remember.data

        # TRY - ldfa,2020-10-04 does form.process() resolve this problem? no, it doesn't
        form.first.validators.remove(time_range1)  # fix bug #2: we need to remove timerange validators to destroy them
        form.last.validators.remove(time_range1)   #    otherwise they will be reused in succedings calls

        # check query type
        query = form.query.data[:]
        query_worst_set = {'Worst_World', 'Worst_EU', }
        if query == 'World':
            return redirect(url_for('views.draw_graph',    # redirect World query to continents/World
                                    context='continents',
                                    ids='World',
                                    fields=columns, 
                                    normalize=normalize,
                                    overlap=overlap,
                                    first=first,
                                    last=last,
                                    remember=remember
                                   )
                           )
        elif query in query_worst_set:
            if query == 'Worst_World':
                #idsl = models.GeoEntities.get_entity_att('World', 'nations')
                w = models.GeoEntities()                      # all the world
                w = w.get_entities_by_att('type', 'nation')   # nations only (EU included)
                idsl = w.keys()
            elif query == 'Worst_EU':
                idsl = models.GeoEntities.get_entity_att('EU', 'nations')
            # get from n1 to n2 worst nations in World and redirect query to nations/...
            n1 = form.n1.data
            n2 = form.n2.data
            idsl = models.worst_countries(g.df, all_columns[0], idsl, n1, n2, normalize=normalize)
            ids = '-'.join(idsl)
            return redirect(url_for('views.draw_graph',
                                    context='nations',
                                    ids=ids,
                                    fields=columns, 
                                    normalize=normalize,
                                    overlap=overlap,
                                    first=first,
                                    last=last,
                                    remember=remember
                                   )
                           )
        # ldfa: future reference
        #elif somequery:
        #    return redirect(url_for('views.draw_query_graph', 
        #                            query=query, 
        #                            fields=columns, 
        #                            normalize=normalize,
        #                            first=first,
        #                            last=last
        #                           )
        #                   )
        else:
            raise ValueError(_('%(function)s: %(query)s is not a valid query', function=fname, query=query))

    # TRY - ldfa,2020-10-04 does form.process() resolve this problem? No, it doesn't
    try:                                           # again: removing timerange validators. see previous comment
        if time_range1 in form.first.validators:
            form.first.validators.remove(time_range1)
        if time_range1 in form.last.validators:
            form.last.validators.remove(time_range1)
    except:
        pass
    
    form.first.default = FIRST # and this sets a default date
    form.last.default  = LAST
    
    form.n1.default = 1
    form.n2.default = EU_NUM

    # + ldfa,2020-10-04
    # is it necessary to review the time validators behavior?
    #     because I suspect previous behaviour of TimeRange was due to lack of form.process()
    #     conclusion: no, TimeRange validators behaviour is unchanged by the presence of form.process()
    # next by https://stackoverflow.com/questions/31423495/how-to-dynamically-set-default-value-in-wtforms-radiofield
    #     about "How to dynamically set default value in WTForms RadioField?". This is valid even for integer fields
    #     warning: apply this ONLY AFTER the GET, not the POST
    form.process()
    
    return render_template('select_other.html', 
                           title=_('Select a query'), 
                           all_fields=forms.FIELDS,
                           main_fields=forms.dict_delta_fields(direct=False),
                           secondary_fields=forms.dict_delta_fields(direct=True),
                           form=form,
                          )


def query_patterns(df, context, ids, first=None, last=None, remember=False):
    '''implements models.py query patterns
    
    parameters:
        - df            pandas dataframe - carring initial data
        - context       str - 'nations' | 'continents'
        - ids           str - with geoId of nations or name of continents;
                              could contain areas names;
                              e.g. 'AF-AL-AT-EU' or 'Asia-North_America'
        - first         date - left of date interval
        - last          date - right of date interval
    
    returns:
        - ndf           pandas dataframe - with (only) requested rows
                              carring daily data about cases and deaths;
                              countriesAndTerritories field carries names of
                              nations and/or "area nation", or 
                              continents and/or subcontinents;
                              population field is calculated accordingly
    
    remarks. here we implement (from models.py heading comment):
    
        # We'll have these query patterns: <cut>
        #
        # 1 - nations + areas + date
        #     subset rows by date
        #     create rows by area         (note: context=='nations')
        #     subset rows by nations
        #     append area rows to nations rows
        #
        # 2 - continents + subcontinents + dates
        #     subset rows by date          (note: this is as 1st row in the above pattern)
        #     create rows by subcontinents (note: this is the same of "create rows by area", but with context=='continents')
        #     subset rows by continents
        #     append subcontinents rows to continents rows (note: this is as last row in above pattern)
    '''
    
    # list of ids of countries or continents
    l_ids = ids.split('-')
    areas = models.get_areas(l_ids)
    not_areas = list(set(l_ids) - set(areas))
    
    # in all patterns: 1 & 2 ...
    #     ... get all records in dates interval (note: here we modify globally g.df)
    #             ATTENTION: if df['dateRep'].min() < first => we lose initial cases and deaths data
    #             hence starting with cases & deaths == 0
    #             to store initial data in initial_df: 
    #                 if df['dateRep'].min() < first:
    #                     initial_df = df[df['dateRep']<first]
    if (   (first is None)        # if first and last are both None we skip date filter
       and (last  is None)):
        ddf = df
    else:
        if first is None: first = df['dateRep'].min()
        if last  is None: last  = df['dateRep'].max()
        ddf = models.select_rows_by_dates(df, first, last, remember)
    
    #     ... this creates rows for areas as 'nations' or 'continents' depending on context
    df_areas = models.create_rows_by_areas(ddf, areas, context, pop_field=POP_FIELD)

    # query pattern 1: nations + areas + date ...
    #     ... date filter & create rows by area already applied
    if context=='nations':
        df_not_areas = models.subset_rows_by_nations(ddf, not_areas)
    
    # query pattern 2: continents + subcontinents (alias: areas) + date ...
    #     ... date filter & create rows by area  already applied
    else:
        df_not_areas = models.create_rows_by_continents(ddf, not_areas, pop_field=POP_FIELD)
    
    # in all patterns: 1 & 2, concatenate results 
    ndf = pd.concat([df_not_areas, df_areas])
    
    return ndf

@bp.route('/graph/<context>/<ids>/<fields>/<normalize>/<overlap>/<first>/<last>/<remember>')
def draw_graph(context, ids, fields='cases', normalize=False, overlap=False, first=None, last=None, remember=False):
    '''show countries trend
       
    params: 
        - context       str - nations | continents
        - ids           str - string of concat nation ids or continents;
                           e.g. it-fr-nl or  asia-europe
        - fields        str - string of concat fields to show; e.g. cases-deaths
        - normalize     bool - if true values are normalized on population (NOT SUPPORTED by now)  #<
        - overlap       bool - if true we align lines to a common start date
        - first         str - start of time interval to draw, str format: aaaa-mm-dd
        - last          str - end of time interval to draw, str format: aaaa-mm-dd
    
    functions:
        - draw nations cases
        - draw nations deaths
        - draw continents cases
        - draw continents deaths
        - N.A. draw normalized values
       '''

    fname = 'draw_graph'
    current_app.logger.debug('{}({}, {}, {}, {}, {}, {}, {})'.format(fname, context, ids, fields, normalize, overlap, first, last))
    
    # START parameters check
    normalize = True if normalize in {'True', 'true',} else False
    overlap   = True if overlap   in {'True', 'true',} else False
    remember  = True if remember  in {'True', 'true',} else False
    
    if normalize and overlap:
        raise ValueError(_('%(function)s: got normalize and overlap both True; this is not acceptable', function=fname))
    
    if len(fields.split("-")) > 1 and overlap:
        raise ValueError(_('%(function)s: got overlap and more than one field, this is not acceptable. Fields are %(fields)s', function=fname, fields=fields))

    first = datetime.strptime(first, '%Y-%m-%d').date() if first is not None else FIRST
    last  = datetime.strptime(last, '%Y-%m-%d').date() if last is not None else LAST
    
    #   args to return here
    kwargs={'context':  context,
           'ids':       ids,
           'fields':    fields,
           'normalize': normalize,
           'overlap':   overlap,
           'first':     first,
           'last':      last,
           'remember':  remember,
           }
    
    #   check request context
    if not context in models.CONTEXT_SELECT:
        raise ValueError(_('%(function)s: context %(context)s is not allowed', function=fname, context=context))
        
    # END   parameters checks
    
    # here "new dataframe" (ndf) has (only) the necessary rows with daily data of cases and deaths
    ddf = query_patterns(g.df, context, ids, first, last, remember)
    
    # managing fields: transforms field sids (from http get) to field names
    fields  = forms.fields_from_sids_to_names(fields)         # str to str
    columns = fields.split("-")                               # and this is the list of field names
    used_delta_fields     = get_used_delta_fields(columns)              # => cases/day, '\N{Greek Capital Letter Delta}cases/day'
    used_not_delta_fields = list(set(columns) - set(used_delta_fields)) # => cases, deaths
    
    # here we define (only) the necessary fields in dataframe and accordingly
    #     we cut (or create) the columns in ndf
    flds = ['dateRep', 'countriesAndTerritories']
    if normalize: flds.append(POP_FIELD)
    flds.extend(used_not_delta_fields)
    
    # ddf:
    #     |       dateRep  cases countriesAndTerritories
    #     |0   2020-04-30    122             Afghanistan
    #     |...
    #     |5   2020-04-25     70             Afghanistan
    #     |6   2020-04-24    105             Afghanistan
    #     |7   2020-04-30     16                 Albania
    #     |...
    #     |12  2020-04-25     15                 Albania
    #     |13  2020-04-24     29                 Albania
    ddf = models.add_cols(ddf, used_delta_fields)          # add columns for used delta fields
    flds.extend(used_delta_fields)
    ddf = models.subset_cols(ddf, flds)                    # drop unused columns
    
    # Getting names of contries (|continents|areas) to draw.                                                                                          Note: ids are identifiers ...
    l_ids = ids.split('-')
    # - ldfa, 2020-09-27 passing to GeoEntities
    #country_names = models.get_geographic_names(l_ids, g.nations)     # ... while these are names
    #country_names_dict = models.get_geographic_characteristics(l_ids, g.nations)     # ... while these are names
    country_names_dict = models.GeoEntities(ids=l_ids)
    country_names = [v['name'] for v in country_names_dict.values()]                   # ... while these are names
    
    # getting continents composition
    #? substitute with function of models.py?
    
    # continents_composition is a dict of dict:
    #     {'Asia':          {'AF': 'Afghanistan', 'BH': '' ...},
    #      'North_America': { "CA": "Canada", "US": "United_States_of_America", "AG": "Antigua_and_Barbuda", ...}
    #     }
    continents_composition = None
    if context=='continents':
        continents_composition = dict()
        # - ldfa,2020-09-27 passing to GeoEntities,
        #       note: nations is {nation_id: nation_name, ...}
        #       while country_names_dict[continent]['nations'] is: [nation_id, nation_id, ...]
        #       so we need to build nations ...
        #for continent in country_names:
        #    if continent in g.nations:
        #        continents_composition[continent] = g.nations[continent].copy()
        #    else:                                      # + ldfa,2020-05-11 get nations from areas
        #        continents_composition[continent] = models.AREAS[continent]['nations'].copy() 
        for continent in country_names_dict.keys():
            nations = {id: models.GeoEntities.get_entity_att(id, 'name') for id in country_names_dict[continent]['nations']}
            continents_composition[continent] = nations   
    
    # managing the overlap status. Here ndf will be:
    #     |                                    cases
    #     |dateRep    countriesAndTerritories
    #     |2020-04-24 Afghanistan                105
    #     |           Albania                     29
    #     |2020-04-25 Afghanistan                 70
    #     |           Albania                     15
    #     |...
    #     |2020-04-30 Afghanistan                122
    #     |           Albania                     16
    #     note: cases are daily cases
    #     note: sum() is not useful in case of nations. BUT it serves in case of continents and/or areas
    ndf = ddf.groupby(['dateRep', 'countriesAndTerritories']).sum()
    
    if not overlap:
        threshold = 0
        # here ndf will become:
        #     |                              cases
        #     |countriesAndTerritories Afghanistan Albania
        #     |dateRep
        #     |2020-04-24                      105      29
        #     |2020-04-25                      175      44
        #     |...
        #     |2020-04-30                      773     132
        #     Note: cases in output ndf become cumulative cases
        ndf = models.calculate_cumulative_sum(ndf, used_not_delta_fields, normalize=normalize)  # pivot and calculate cumulative sum of used fields (not the delta fields)
        # if normalize==True, we divided cases by population
    else:
        # here ndf will become:
        #     |       cases
        #     |  Afghanistan Albania
        #     |0         105      29
        #     |1         175      44
        #     |2         287      78
        #     |3         355      92
        #     |4         527     102
        #     |5         651     116
        #     |6         773     132    
        threshold = models.suggest_threshold(ndf, column=used_not_delta_fields[0], ratio=THRESHOLD_RATIO)
        ndf = models.calculate_cumulative_sum_with_overlap(ndf, column=used_not_delta_fields[0], threshold=threshold, normalize=normalize)
        # if normalize==True, we divided cases by population
    
    if ndf is None:
        raise ValueError(_('%(function)s: got an empty dataframe from pivot; overlap is: %(overlap)s', function=fname, overlap=overlap))

    img_data, mc  = draw_nations(ndf, country_names, columns, normalize=normalize, overlap=overlap)  # image data, mc is missing countries
    country_names = [country for country in country_names if country not in mc]
    html_table = table_nations(ddf, country_names, columns, normalize=normalize)
    html_table_last_values = table_last_values(ddf, country_names, columns, normalize=normalize)

    title = _('overlap') if overlap else _('plot')
    kwargs['overlap'] = False if overlap else True    # ready to switch from overlap to not overlap, and vice versa
    
    return render_template('plot.html',
                           title=title,
                           time_interval=(first, last,),
                           columns=columns,
                           all_fields=forms.FIELDS,
                           countries=country_names,
                           continents_composition=continents_composition,
                           normalize=normalize,
                           overlap=overlap,
                           threshold=threshold,
                           img_data = img_data,
                           html_table_last_values=html_table_last_values,
                           html_table=html_table,
                           kwargs=kwargs,
                           last_day=last
                          )


def get_used_delta_fields(fields):
    return   list(set(fields) & set(forms.list_delta_fields()))

#def draw_nations(df, country_name_field, country_names, fields, normalize=False, overlap=False):
def draw_nations(df, country_names, fields, normalize=False, overlap=False):
    '''prepare data to draw chosen observations and make it
    
    parameters:
        - df            pandas dataframe - ready to be drawn
        - country_name_field          -str - no more used (drop it)
        - fields        list of str - name of variables to draw
        - normalize     bool - ~~True~~|False
        - overlap       bool - ~~True~~|False
    '''
    fname = 'draw_nations'
    #current_app.logger.debug('> {}({}, {}, {}, {}, {})'.format(fname, df, country_names, fields, normalize, overlap))
    
    delta_fields = forms.list_delta_fields()
    used_delta_fields = get_used_delta_fields(fields)
    
    tmpfields = [field for field in fields if not field in used_delta_fields]
    #if '\N{Greek Capital Letter Delta}cases/day' in fields:
    #    tmpfields.remove('\N{Greek Capital Letter Delta}cases/day')
    #if 'cases/day' in fields:
    #    tmpfields.remove('cases/day')
    #for field in tmpfields:
    #    sdf[field] = sdf[field].cumsum()
    #if normalize:
    #    for field in tmpfields:
    #        df[field] = df[field]/df[POP_FIELD]
    #    del df[POP_FIELD]
    
    # fighting for a good picture
    fig = Figure(figsize=(9,7))
    
    if set(fields).isdisjoint(delta_fields):               # fields has not delta_fields
        ax = fig.subplots()
    else:
        ax = fig.add_axes([0.1,0.35,0.8,0.6])  # left, bottom, width, height
        ax2 = fig.add_axes([0.1,0.20,0.8,0.15], sharex=ax)
    
    xlabelrot = 80
    title  = _l('Observations about Covid-19 outbreak')
    ylabel = _l('number of cases') if not normalize else _l('rate to population')
    y2label = _l('n.of cases')
    xlabel = _l('date') if not overlap else _l('days from overlap point')
    
    fig, mc = generate_figure(ax, df, country_names, columns=tmpfields)      # figure, missing countries
    
    ax.grid(True, linestyle='--')
    ax.legend()
    ax.set_title (title)
    ax.set_ylabel(ylabel)
    if set(fields).isdisjoint(delta_fields):               # fields has not delta_fields
        ax.tick_params(axis='x', labelrotation=xlabelrot)
        ax.set_xlabel(xlabel)
        fig.subplots_adjust(bottom=0.2)
    
    if not set(fields).isdisjoint(delta_fields):               # fields has delta_fields
        fig, mc = generate_figure(ax2, df, country_names, columns=used_delta_fields)    # figure, missing countries
        ax2.set_ylabel(y2label)
        ax2.tick_params(axis='x', labelrotation=xlabelrot)
        ax2.grid(True, linestyle='--')
        ax2.legend()
        ax2.set_xlabel(xlabel)
    
    # Save it to a temporary buffer.
    buf = StringIO()
    fig.savefig(buf, format="svg")
    soup = bs.BeautifulSoup(buf.getvalue(),'lxml')          # parse image
    img_data = soup.find('svg')                             # get image data only (<svg ...> ... </svg>)
    return img_data, mc


def generate_figure(ax, df, countries, columns=None):
    '''# Generate the figure **without using pyplot**.'''
    if columns is None: columns = ['cases']
    
    # ldfa,2020-10-03 how going over 20 colors (needed to represent EU: 26 countries), see:
    # https://stackoverflow.com/questions/8389636/creating-over-20-unique-legend-colors-using-matplotlib
    # and here colormaps examples:
    # https://matplotlib.org/examples/color/colormaps_reference.html
    num_colors = len(countries)           # how many colors we need
    cm = plt.get_cmap('tab20')     # color map to use: max 20 countries
    ax.set_prop_cycle(color=[cm(1.*i/num_colors) for i in range(num_colors)])
    
    missing_countries = []
    
    for column, ltype in zip(columns, ['-', '--', '-.', ':'][0:len(columns)]):
        #for country, color in zip(countries, COLORS[0:len(countries)]):
        for country in countries:
            try:
                ax.plot(df.index.values,          # x
                        df[column][country],         # y
                        ltype,
                        #color=color,
                        label=_('%(column)s of %(country)s', column=column, country=country)         # label in legend
                       )
            except:
                missing_countries.append(country)
        
    fig = ax.get_figure()

    return fig, missing_countries

# +- ldfa,2020-09-18 modified, using a modeled dataframe
# + ldfa,2020-05-17 to show a summary table of chosen observations
def table_nations(df, country_names, fields, normalize=False):
    '''summary table of daily and observations
    
    remarks: 
        - summary is by converting daily data to mean onto week data
        - here df is a dataframe with daily data, NOT the cumulative ones
    '''
    fname = 'table_nations'
    #current_app.logger.debug(fname)
    
    ndf = df.copy(deep=True)
    nfields = fields[:]
    
    if 'cases/day' in fields and 'cases' in fields:
        nfields.remove('cases/day')
        del ndf['cases/day']

    if POP_FIELD in df.columns:
        del ndf[POP_FIELD]
    
    if not 'dateRep' in ndf.columns:
        ndf.reset_index(level=0, inplace=True)
    
    # now we need to translate daily dates to weeks
    ndf['dateRep'] = pd.to_datetime(ndf['dateRep'])
    ndf['week'] = ndf['dateRep'].dt.week    # adding week number
    ndf['year'] = ndf['dateRep'].dt.year    # adding year
    
    #edf = edf.rename(columns=forms.FIELDS_IN_TABLE)    # renaming columns to avoid confusioni with names in graph
    ndf = ndf.rename(columns={name: forms.FIELDS[name]['mean_tag'] for name in forms.FIELDS.keys()})    # renaming columns to avoid confusioni with names in graph
    
    ndf_avg = ndf.groupby(['year','week','countriesAndTerritories']).mean()
    
    ndf1 = pd.pivot_table(ndf_avg, index=['year','week'],columns='countriesAndTerritories')
    return ndf1.to_html(buf=None, float_format=lambda x: '%10.2f' % x)


# +- ldfa,2020-09-18 modified, using a modeled dataframe
# + ldfa,2020-05-27 to show values of observations on last day
def table_last_values0(df, country_names, fields, normalize=False):
    ''' show figures of last day about chosen observations
    '''
    fname = 'table_last_values'
    #current_app.logger.debug(fname)
    
    delta_fields = forms.list_delta_fields()

    ndf = df.copy(deep=True)
    if POP_FIELD in df.columns and not normalize:
        del ndf[POP_FIELD]
    
    ndf = ndf.groupby(['dateRep', 'countriesAndTerritories']).sum()
    ndf1 = pd.pivot_table(ndf, index='dateRep',columns='countriesAndTerritories')
    if ndf1 is None:
        raise ValueError(_('%(function)s: got an empty dataframe from pivot', function=fname))
    #tmpfields = fields[:]
    tmpfields = [field for field in fields if not field in delta_fields]
    
    #if '\N{Greek Capital Letter Delta}cases/day' in fields:
    #    tmpfields.remove('\N{Greek Capital Letter Delta}cases/day')
    #if 'cases/day' in fields:
    #    tmpfields.remove('cases/day')
    
    for field in tmpfields:
        ndf1[field] = ndf1[field].cumsum()
    ndf1 = ndf1.iloc[-1:]
    
    if normalize:
        for field in tmpfields:
            index = pd.MultiIndex.from_product([[field+'/pop.'], country_names])
            ndf2 = ndf1[field].divide(ndf1[POP_FIELD])
            ndf2.columns = index
            ndf1 = ndf1.join(ndf2)

    #return ndf1.to_html(buf=None, float_format=lambda x: '%10.4f' % x)
    return ndf1.to_html(buf=None, float_format="{:n}".format)                # a more flexible format to output numbers
    

# +- ldfa,2020-10-09 modified: countries as row index
# +- ldfa,2020-09-18 modified, using a modeled dataframe
# + ldfa,2020-05-27 to show values of observations on last day
def table_last_values(df, country_names, fields, normalize=False):
    ''' show figures of last day about chosen observations
    '''
    fname = 'table_last_values'
    #current_app.logger.debug(fname)
    
    delta_fields = forms.list_delta_fields()

    ndf = df.copy(deep=True)
    if POP_FIELD in df.columns and not normalize:
        del ndf[POP_FIELD]
        
    ndf = ndf.groupby(['dateRep', 'countriesAndTerritories']).sum()
    ndf1 = pd.pivot_table(ndf, index='dateRep',columns='countriesAndTerritories')
    if ndf1 is None:
        raise ValueError(_('%(function)s: got an empty dataframe from pivot', function=fname))
    tmpfields = [field for field in fields if not field in delta_fields]
    
    for field in tmpfields:
        ndf1[field] = ndf1[field].cumsum()
    ndf1 = ndf1.iloc[-1:]
    
    if normalize:
        for field in tmpfields:
            index = pd.MultiIndex.from_product([[field+'/pop.'], country_names])
            ndf2 = ndf1[field].divide(ndf1[POP_FIELD])
            ndf2.columns = index
            ndf1 = ndf1.join(ndf2)
            
    resultdf = pd.DataFrame()                               # START trasposing to get countries as row index
    for col, row in ndf1.columns.to_list():
        resultdf.at[row, col] = ndf1[(col, row)].iloc[0]    # END   trasposing to get countries as row index

    #return ndf1.to_html(buf=None, float_format=lambda x: '%10.4f' % x)
    #return ndf1.to_html(buf=None, float_format="{:n}".format)                # a more flexible format to output numbers
    return resultdf.to_html(buf=None, float_format="{:n}".format)                # a more flexible format to output numbers
    

# START section about deleted code

# - ldfa,2020.09.27
#def get_delta_fields():
#    return [name for name in forms.FIELDS.keys() if forms.FIELDS[name]['delta_field']]


# - ldfa,2010-09-19 "World" query redirected to draw_graph. code kept for future reference
#@bp.route('/query_graph/<query>/<fields>/<normalize>/<first>/<last>')
#def draw_query_graph(query, fields='cases', normalize=False, first=None, last=None):
#    '''show countries trend
#       
#    params: 
#        - query         str - type of query: "world" by now
#        - fields        str - string of concat fields to show; e.g. cases-deaths
#        - normalize     str - 'True' | 'False'
#        - first         str - start of time interval to draw, str format: aaaa-mm-dd
#        - last          str - end of time interval to draw, str format: aaaa-mm-dd
#    
#    functions:
#        - draw world cases
#        - draw world deaths
#    '''
#
#    fname = 'draw_query_graph'
#    current_app.logger.debug('{}({}, {}, {}, {})'.format(fname, query, fields, first, last))
#    
#    # START parameters check
#    normalize = True if normalize in {'True', 'true',} else False
#    overlap = False
#    
#    first = datetime.strptime(first, '%Y-%m-%d').date() if first is not None else FIRST
#    last  = datetime.strptime(last, '%Y-%m-%d').date() if last is not None else LAST
#    
#    if ( first<FIRST
#         or first > last
#         or last > LAST ):
#        raise ValueError(_('%(function)s: it must be %(FIRST)s <= %(first)s <= %(last)s <= %(LAST)s',
#                             function=fname,
#                             FIRST=FIRST.strftime('%Y-%m-%d'),
#                             first=first.strftime('%Y-%m-%d'),
#                             last=last.strftime('%Y-%m-%d'),
#                             LAST=LAST.strftime('%Y-%m-%d')))
#    
#    #   args to return here
#    kwargs={'query':  query,
#           'fields':    fields,
#           'normalize': normalize,
#           'first':     first,
#           'last':      last,
#          }
#          
#    #   check request context
#    if query=='World':
#        country_names = ['World',]
#        country_name_field = 'countriesAndTerritories'
#        g.df['countriesAndTerritories'] = 'World'
#    else:
#        raise ValueError(_('%(function)s: query %(query)s is not allowed', function=fname, query=query))
#        
#    # END   parameters checks
#    
#    # set time interval
#    g.df = g.df[(g.df['dateRep']>=first) & (g.df['dateRep']<=last)]
#    
#    threshold = 0
#    
#    fields = forms.fields_from_sids_to_names(fields)
#    
#    img_data, threshold = draw_nations(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=False)
#    html_table = table_nations(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=False)
#    html_table_last_values = table_last_values(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=overlap)
#    
#    
#    title = _('overlap') if overlap else _('plot')
#    kwargs['overlap'] = overlap
#    
#    columns = fields.split('-')
#    
#    return render_template('plot.html',
#                           title=title,
#                           time_interval=(first, last,),
#                           columns=columns,
#                           all_fields=forms.FIELDS,
#                           countries=country_names,
#                           continents_composition=None,
#                           overlap=overlap,
#                           threshold=threshold,
#                           img_data = img_data,
#                           html_table_last_values=html_table_last_values,
#                           html_table=html_table,
#                           kwargs=kwargs,
#                          )


# - ldfa,2020-09-19 developed a completely new version
#@bp.route('/graph/<contest>/<ids>/<fields>/<normalize>/<overlap>/<first>/<last>')
#def draw_graph_0(contest, ids, fields='cases', normalize=False, overlap=False, first=None, last=None):


# - ldfa,2020-09-19 developed a completely new version
#def draw_nations0(df, country_name_field, country_names, fields, normalize=False, overlap=False):


# - ldfa,2020-09-19 no more used
#def prepare_target(df, country_name_field, country_names, fields, normalize=False, overlap=False):


# - ldfa,2020-09-19 developed a completely new version
# + ldfa,2020-05-17 to show a summary table of chosen observations
#def table_nations0(df, country_name_field, country_names, fields, normalize=False, overlap=False):


# - ldfa,2020-09-19 developed a completely new version
# + ldfa,2020-05-27 to show values of observations on last day
#def table_last_values0(df, country_name_field, country_names, fields, normalize=False, overlap=False):


# - ldfa,2020-09-19 developed a completely new version
#def suggest_threshold(df, country_name_field, column='cases', ratio=0.1):

    
# - ldfa,2020-09-19 developed a completely new version
#def pivot_with_overlap(df, country_name_field, column= 'cases', threshold=THRESHOLD):


# END   section about deleted code
