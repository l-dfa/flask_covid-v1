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

FIRST = ''     # this placeholder to register the 1st day available ...
LAST  = ''     #   ... and this to hold the last day available


@bp.before_request
def before_request():
    '''open data when request starts'''
    global FIRST
    global LAST
    current_app.logger.debug('> before_request()')
    g.locale = str(get_locale())
    df = models.open_df(current_app.config['DATA_DIR']+'/'+current_app.config['DATA_FILE'],
                        pd.read_csv,
                        models.world_shape)                     # stores dataframe in g.df
    FIRST, LAST = (df['dateRep'].min(), df['dateRep'].max(),)
    g.nations = models.Nations(dataframe=df)


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


@bp.route('/select', methods=['GET', 'POST'])
def select():
    '''select what country's trend to show'''
    
    fname = 'select'
    current_app.logger.debug('> {}() by {} http method'.format(fname, request.method))
    form = forms.SelectForm()
    form.fields.choices = list(zip([forms.FIELDS[key]['id'] for key in forms.FIELDS.keys()], forms.FIELDS.keys()))
    # to set a default, the following does not work; we need to use the "default" parameter in the class, or set data (see below)
    #form.fields.default = ['1',]
    
    form.contest.choices = [('nations','nations',), ('continents', 'continents',),]
    
    form.continents.choices = [ (c, c, ) for c in g.nations.keys()]
    form.continents.choices.extend( [ (c, c, ) for c in models.AREAS.keys() if models.AREAS[c]['contest']=='continents'] )
    form.continents.choices.sort(key=lambda x: x[1])            # sort by name
    
    form.countries.choices = g.nations.get_for_select()
    form.countries.choices.extend( [ (v['geoId'], c, ) for c, v in models.AREAS.items() if models.AREAS[c]['contest']=='nations'] )
    form.countries.choices.sort(key=lambda x: x[1])            # sort by name

    time_range = forms.TimeRange(FIRST, LAST)   #+- ldfa fix bug #1 initializing TimeRange for GET AND FOR POST
    form.first.validators.append(time_range)    #+-
    form.last.validators.append(time_range)     #+-
    
    if form.validate_on_submit():

        # check contest: nations or continents
        contest = form.contest.data[:]
        if contest == 'nations':
            ids = '-'.join(form.countries.data)             # here build string with nations ids: e.g. it-fr-nl
        elif contest == 'continents':
            ids = '-'.join(form.continents.data)             # here build string with continents ids: e.g. Asia-Europe
        else:
            raise ValueError(_('%(function)s: %(contest)s is not a valid contest', function='select', contest=contest))
            
        # chaining names of fields to plot
        #columns = [name for code, name in FIELDS_CHOICES if code in form.fields.data ]
        columns = [name for name in forms.FIELDS.keys() if forms.FIELDS[name]['id'] in form.fields.data ]
        columns = '-'.join(columns)
        
        first = form.first.data
        last  = form.last.data
        
        # type of values: normal or normalized
        normalize = False                       #< CHANGE, is going this to be from form?
        overlap   = False                       #< CHANGE, this will be from form?
        
        ## TEST #<
        #contest = 'nations'
        #ids = 'EU'
        #contest = 'continents'
        #ids = 'Europe-America'
        
        return redirect(url_for('views.draw_graph', 
                                contest=contest, 
                                ids=ids, 
                                fields=columns, 
                                normalize=normalize, 
                                overlap=overlap,
                                first=first,
                                last=last
                               )
                       )

    #breakpoint() #<
    
    #form.fields.data = ['1']                            # this sets a default value
    form.first.data = FIRST # and this sets a default date
    form.last.data  = LAST
    current_app.logger.debug('= {} - form.first.data: {}'.format(fname, form.first.data))
    current_app.logger.debug('= {} - form.last.data: {}'.format(fname, form.last.data))
    return render_template('select.html', 
                           title=_('Select country'), 
                           all_fields=forms.FIELDS,
                           form=form,
                           nations=g.nations.get_for_list()
                          )



@bp.route('/other_select', methods=['GET', 'POST'])
def other_select():
    '''other_select address: shows some precostituited queries to selct from a form'''
    
    fname = 'other_select'
    current_app.logger.debug('{}() using {} http method'.format(fname, request.method))
    
    # NOT READY
    #return 'Sorry. World select is not implemented yet. We will fix it soon.'

    # SHUNT to view
    #query = 'World'
    #columns = 'cases-deaths-d²cases_dt²'
    #first = FIRST
    #last  = LAST
    #return redirect(url_for('views.draw_query_graph', 
    #                        query=query, 
    #                        fields=columns, 
    #                        normalize=False,
    #                        first=first,
    #                        last=last
    #                       )
    #               )
    
    # FROM HERE we go
    form = forms.OtherSelectForm()
    form.fields.choices = list(zip([forms.FIELDS[key]['id'] for key in forms.FIELDS.keys()], forms.FIELDS.keys()))
    
    form.query.choices = [('World','World',), ]

    time_range = forms.TimeRange(FIRST, LAST)
    form.first.validators.append(time_range)
    form.last.validators.append(time_range)
    
    if form.validate_on_submit():
    
        # check query type
        query = form.query.data[:]
        if query == 'World':
            pass
        else:
            raise ValueError(_('%(function)s: %(query)s is not a valid query', function=fname, query=query))
            
        # chaining names of fields to plot
        #columns = [name for code, name in FIELDS_CHOICES if code in form.fields.data ]
        columns = [name for name in forms.FIELDS.keys() if forms.FIELDS[name]['id'] in form.fields.data ]
        columns = '-'.join(columns)
        
        first = form.first.data
        last  = form.last.data
        
        return redirect(url_for('views.draw_query_graph', 
                                query=query, 
                                fields=columns, 
                                normalize=False,
                                first=first,
                                last=last
                               )
                       )
    
    form.first.data = FIRST # and this sets a default date
    form.last.data  = LAST
    return render_template('select_other.html', 
                           title=_('Select a query'), 
                           all_fields=forms.FIELDS,
                           form=form,
                          )


@bp.route('/query_graph/<query>/<fields>/<normalize>/<first>/<last>')
def draw_query_graph(query, fields='cases', normalize=False, first=None, last=None):
    '''show countries trend
       
    params: 
        - query         str - type of query: "world" by now
        - fields        str - string of concat fields to show; e.g. cases-deaths
        - first         str - start of time interval to draw, str format: aaaa-mm-dd
        - last          str - end of time interval to draw, str format: aaaa-mm-dd
    
    functions:
        - draw world cases
        - draw world deaths
    '''

    fname = 'draw_query_graph'
    current_app.logger.debug('{}({}, {}, {}, {})'.format(fname, query, fields, first, last))
    
    # START parameters check
    normalize = True if normalize in {'True', 'true',} else False
    overlap = False
    
    first = datetime.strptime(first, '%Y-%m-%d').date() if first is not None else FIRST
    last  = datetime.strptime(last, '%Y-%m-%d').date() if last is not None else LAST
    
    #   args to return here
    kwargs={'query':  query,
           'fields':    fields,
           'normalize': normalize,
           'first':     first,
           'last':      last,
          }
          
    #   check request contest
    if query=='World':
        country_names = ['World',]
        country_name_field = 'countriesAndTerritories'
        g.df[country_name_field] = 'World'
    else:
        raise ValueError(_('%(function)s: query %(query)s is not allowed', function=fname, query=query))
        
    # END   parameters checks
    
    # set time interval
    g.df = g.df[(g.df['dateRep']>=first) & (g.df['dateRep']<=last)]
    
    threshold = 0
    
    img_data, threshold = draw_nations(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=False)
    html_table = table_nations(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=False)
    html_table_last_values = table_last_values(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=overlap)
    
    
    title = _('overlap') if overlap else _('plot')
    kwargs['overlap'] = overlap
    
    columns = fields.split('-')
    
    return render_template('plot.html',
                           title=title,
                           time_interval=(first, last,),
                           columns=columns,
                           all_fields=forms.FIELDS,
                           countries=country_names,
                           continents_composition=None,
                           overlap=overlap,
                           threshold=threshold,
                           img_data = img_data,
                           html_table_last_values=html_table_last_values,
                           html_table=html_table,
                           kwargs=kwargs,
                          )



@bp.route('/graph/<contest>/<ids>/<fields>/<normalize>/<overlap>/<first>/<last>')
def draw_graph(contest, ids, fields='cases', normalize=False, overlap=False, first=None, last=None):
    '''show countries trend
       
    params: 
        - contest       str - nations | continents
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
    current_app.logger.debug('{}({}, {}, {}, {}, {}, {}, {})'.format(fname, contest, ids, fields, normalize, overlap, first, last))
    
    # START parameters check
    normalize = True if normalize in {'True', 'true',} else False
    overlap   = True if overlap   in {'True', 'true',} else False
    
    # START TEST <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    #first = '2020-03-01'
    #last  = '2020-03-31'
    # END   TEST
    
    first = datetime.strptime(first, '%Y-%m-%d').date() if first is not None else FIRST
    last  = datetime.strptime(last, '%Y-%m-%d').date() if last is not None else LAST
    #breakpoint() #<
    
    #   args to return here
    kwargs={'contest':  contest,
           'ids':       ids,
           'fields':    fields,
           'normalize': normalize,
           'overlap':   overlap,
           'first':     first,
           'last':      last,
          }
          
    #   check request contest
    if contest=='nations':
        country_field = 'geoId'
        country_name_field = 'countriesAndTerritories'
    elif contest=='continents':
        country_field = 'continentExp'
        country_name_field = 'continentExp'
    else:
        raise ValueError(_('%(function)s: contest %(contest)s is not allowed', function=fname, contest=contest))
        
    #   countries: list of ids of countries or continents
    countries = ids.split('-')                         # list of ids of nations or continents
    
    #   regular_countries vs not_regular_countries: select regular countries/continents vs areas items # + ldfa,2020-05-15
    if contest=='nations':                             # +- ldfa,2020-05-11 added nations from AREAS
        regular_countries = [ country  for country in countries if g.nations.get_nation_name(country)]
    else:
        regular_countries = [ country  for country in countries if g.nations.get(country)]
    not_regular_countries =  list(set(countries) - set(regular_countries))
    
    #   country_names: getting names from ids
    if contest=='nations':                             # +- ldfa,2020-05-11 added nations from AREAS
        country_names = [ g.nations.get_nation_name(country) if g.nations.get_nation_name(country) is not None else models.areas_get_nation_name(country, contest, models.AREAS)  for country in countries]
    else:
        country_names = countries         # in case of continents, country_names and identifiers are equals
        
    #df = open_data(current_app.config['DATA_FILE'], pd.read_csv, world_shape)
    checklist = g.df[country_name_field].drop_duplicates()
    
    other_names = models.areas_get_names(contest, models.AREAS)       # + ldfa,2020-05-14 added names from AREAS
    if len(other_names) > 0:
        other_names = pd.Series(other_names)
        checklist = checklist.append(other_names, ignore_index=True)
    if set(country_names)-set(checklist):    # some countries aren't in checklist: not good
        unknown = set(country_names)-set(checklist)
        raise ValueError(_('%(function)s: these countries/continents are unknown: %(unknown)s', function=fname, unknown=unknown))
        
    # set time interval
    g.df = g.df[(g.df['dateRep']>=first) & (g.df['dateRep']<=last)]

    # END   parameters checks
    
    continents_composition = None
    if contest=='continents':
        continents_composition = dict()
        for continent in country_names:
            if continent in g.nations:
                continents_composition[continent] = g.nations[continent].copy()
            else:                                      # + ldfa,2020-05-11 get nations from areas
                continents_composition[continent] = models.AREAS[continent]['nations'].copy() 
    threshold = 0
    
    # now, if we have areas items, we need to grow dataframe copying and appending data of that items
    # remark: areas items ids are listed in not_regular_countries
    for not_regular_country in not_regular_countries:
        # building a df to aggregate data from component nations ...
        df_tmp = pd.DataFrame()
        # ... get component nations ids
        not_regular_name = models.areas_get_nation_name(not_regular_country, contest, models.AREAS)  # area item name: key to access AREA dict
        localities = [ k for k in models.AREAS[not_regular_name]['nations'].keys()]           # ids of countries forming item of area
        # ... calculating area population
        df_nrc  = g.df[g.df['geoId'].isin(localities)]           
        population = df_nrc[['countriesAndTerritories', 'popData2019']].drop_duplicates().sum()['popData2019']
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
        
        df_tmp['countriesAndTerritories'] = not_regular_name[:]
        df_tmp['geoId']                   = models.AREAS[not_regular_name]['geoId']
        df_tmp['countryterritoryCode']    = models.AREAS[not_regular_name]['countryterritoryCode']
        df_tmp['popData2019']             = population
        df_tmp['continentExp']            = models.AREAS[not_regular_name]['continentExp']
        # ... new df ready, now we append it to the original df
        g.df = pd.concat([g.df, df_tmp])

    img_data, threshold = draw_nations(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=overlap)
    html_table = table_nations(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=overlap)
    html_table_last_values = table_last_values(g.df, country_name_field, country_names, fields, normalize=normalize, overlap=overlap)
    
    title = _('overlap') if overlap else _('plot')
    kwargs['overlap'] = False if overlap else True    # ready to switch from overlap to not overlap, and vice versa
    
    columns = fields.split('-')
    
    return render_template('plot.html',
                           title=title,
                           time_interval=(first, last,),
                           columns=columns,
                           all_fields=forms.FIELDS,
                           countries=country_names,
                           continents_composition=continents_composition,
                           overlap=overlap,
                           threshold=threshold,
                           img_data = img_data,
                           html_table_last_values=html_table_last_values,
                           html_table=html_table,
                           kwargs=kwargs,
                          )


def draw_nations(df, country_name_field, country_names, fields, normalize=False, overlap=False):
    '''prepare data to draw chosen observations and make it
    '''
    fname = 'draw_nations'
    current_app.logger.debug('> {}({}, {}, {}, {}, {}, {})'.format(fname, df, country_name_field, country_names, fields, normalize, overlap))
    
    # build the target dataframe (only wantend fields and nations)
    edf = prepare_target(df, country_name_field, country_names, fields, normalize=False, overlap=False)
    fields = fields.split('-')                         # list of fields to plot
    
    edf = edf.groupby(['dateRep', country_name_field]).sum()

    if not overlap:
        threshold = 0
        sdf1 = pd.pivot_table(edf, index='dateRep',columns=country_name_field)
    else:
        threshold = suggest_threshold(edf, country_name_field, column=fields[0], ratio=THRESHOLD_RATIO)
        sdf1 = pivot_with_overlap(edf, country_name_field, column=fields[0], threshold=threshold)
    if sdf1 is None:
        raise ValueError(_('%(function)s: got an empty dataframe from pivot', function=fname))
    
    #sdf1 = sdf1.cumsum()
    tmpfields = fields[:]
    if 'd²cases_dt²' in fields:
        tmpfields.remove('d²cases_dt²')
    for field in tmpfields:
        sdf1[field] = sdf1[field].cumsum()
    
    # fighting for a good picture
    fig = Figure(figsize=(9,7))
    if 'd²cases_dt²' in fields:
        ax = fig.add_axes([0.1,0.35,0.8,0.6])  # left, bottom, width, height
        ax2 = fig.add_axes([0.1,0.20,0.8,0.15], sharex=ax)
    else:
        ax = fig.subplots()
    
    xlabelrot = 80
    title  = _l('Observations about Covid-19 outbreak')
    ylabel = _l('number of cases') if not normalize else _l('rate to population')
    y2label = _l('n.of cases')
    xlabel = _l('date') if not overlap else _l('days from overlap point')
    
    fig = generate_figure(ax, sdf1, country_names, columns=tmpfields)
    
    ax.grid(True, linestyle='--')
    ax.legend()
    ax.set_title (title)
    ax.set_ylabel(ylabel)
    if 'd²cases_dt²' not in fields:
        ax.tick_params(axis='x', labelrotation=xlabelrot)
        ax.set_xlabel(xlabel)
        fig.subplots_adjust(bottom=0.2)
    
    if 'd²cases_dt²' in fields:
        fig = generate_figure(ax2, sdf1, country_names, columns=['d²cases_dt²'])
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
    return (img_data, threshold,)

def prepare_target(df, country_name_field, country_names, fields, normalize=False, overlap=False):
    '''prepare target dataframe: check arguments and build a very specialized dataframe
    composed only by wanted nations and fields
    '''
    fname = 'prepare_target'
    current_app.logger.debug(fname)
    
    
    fields = fields.split('-')                         # list of fields to plot
    allowed = set(list(forms.FIELDS.keys()))
    if set(fields) - allowed:                          # some fields aren't allowed
        notallowed = set(fields)-allowed
        raise ValueError(_('%(function)s: these fields are not allowed: %(notallowed)s', function=fname, notallowed=notallowed))

    # adding d2cases_dt2
    if 'd²cases_dt²' in fields:
        df['d²cases_dt²'] = df['cases'] - df['cases'].shift(-1)

    if type(normalize) is not type(True):
        raise ValueError(_('%(function)s: on parameter <normalize>', function=fname))
        
    
    if ( type(overlap) is not type(True)
         or (overlap and len(fields)>1)
       ):
        raise ValueError(_('%(function)s: on parameter <overlap>', function=fname))
    
    if country_names==['World']:
        flds = ['dateRep']
        flds.extend(fields)
        target  = g.df[flds].groupby(by='dateRep').sum()
        target['countriesAndTerritories'] = 'World'
        return target.copy()
    else:
        sdf = df[(df[country_name_field].isin(country_names))]                # selected dataframe
    
    # building a dataframe with the necessary data
    target = pd.DataFrame()                                                  # empty dataframe
    
    # temporary series to build dates; here as str 'yyyy-mm-dd'
    stemp = (sdf['year'].apply(lambda x:"{:04d}-".format(x)) +
                      sdf['month'].apply(lambda x:"{:02d}-".format(x)) +
                      sdf['day'].apply(lambda x:"{:02d}".format(x))
                     )
    
    target['dateRep'] = stemp.map(lambda x: datetime.strptime(x, '%Y-%m-%d').date()) # date from str to date
    
    for field in fields:                                                  # adding fields cases&|deaths
        target[field]  = sdf[field]
    
    if country_name_field=='world':
        target[country_name_field] = 'world'                     # adding 'world'
    else:
        target[country_name_field] = sdf[country_name_field]                     # adding names of countries|continents
    
    # + ldfa,2020-05-17 fix bug #3
    if country_name_field=='continentExp':
        target = target.groupby(['dateRep', 'continentExp']).sum()
        target = target.reset_index()
    
    return target.copy()


def generate_figure(ax, df, countries, columns=None):
    '''# Generate the figure **without using pyplot**.'''
    if columns is None: columns = ['cases']
    
    for column, ltype in zip(columns, ['-', '--', '-.', ':'][0:len(columns)]):
        for country, color in zip(countries, COLORS[0:len(countries)]):
            ax.plot(df.index.values,          # x
                    df[column][country],         # y
                    ltype,
                    color=color,
                    label=_('%(column)s of %(country)s', column=column, country=country)         # label in legend
                   )
        
    fig = ax.get_figure()

    return fig

# + ldfa,2020-05-17 to show a summary table of chosen observations
def table_nations(df, country_name_field, country_names, fields, normalize=False, overlap=False):
    '''summary table of chosen observations
    
    remarks: summary is by converting daily data to mean onto week data
    '''
    fname = 'table_nations'
    current_app.logger.debug(fname)
    
    # get specialized dataframe: only request fields and nations|continents
    edf = prepare_target(df, country_name_field, country_names, fields, normalize=False, overlap=False)
    
    if not 'dateRep' in edf.columns:
        edf.reset_index(level=0, inplace=True)
    fields = fields.split('-')                         # list of fields to manage
    
    # now we need to translate daily dates to weeks
    edf['dateRep'] = pd.to_datetime(edf['dateRep'])
    edf['week'] = edf['dateRep'].dt.week    # adding week number
    edf['year'] = edf['dateRep'].dt.year    # adding year
    edf = edf.rename(columns=forms.FIELDS_IN_TABLE)    # renaming columns to avoid confusioni with names in graph
    edf_avg = edf.groupby(['year','week',country_name_field]).mean()
    
    sdf1 = pd.pivot_table(edf_avg, index=['year','week'],columns=country_name_field)
    return sdf1.to_html(buf=None, float_format=lambda x: '%10.2f' % x)


# + ldfa,2020-05-27 to show values of observations on last day
def table_last_values(df, country_name_field, country_names, fields, normalize=False, overlap=False):
    ''' show figures of last day about chosen observations
    '''
    fname = 'table_last_values'
    current_app.logger.debug(fname)
    
    # get specialized dataframe: only request fields and nations|continents
    edf = prepare_target(df, country_name_field, country_names, fields, normalize=False, overlap=False)
    fields = fields.split('-')                         # list of fields to manage
    
    edf = edf.groupby(['dateRep', country_name_field]).sum()
    sdf1 = pd.pivot_table(edf, index='dateRep',columns=country_name_field)
    if sdf1 is None:
        raise ValueError(_('%(function)s: got an empty dataframe from pivot', function=fname))
    tmpfields = fields[:]
    if 'd²cases_dt²' in fields:
        tmpfields.remove('d²cases_dt²')
    for field in tmpfields:
        sdf1[field] = sdf1[field].cumsum()
    sdf1 = sdf1.iloc[-1:]
    return sdf1.to_html(buf=None, float_format=lambda x: '%10.2f' % x)

def suggest_threshold(df, country_name_field, column='cases', ratio=0.1):
    '''ratio of the more little between the max cases of the countries
    
    params:
        - df                     pandas dataframe MultiIndex: dateRep+country_name_field (countries | continents)
        - country_name_field     str - coutriesAndTerritories|continentExp
        - column                 str - column with values to check: cases|deaths
        - ratio                  float - ratio to apply default is 10%
        
    return threshold      int 
    '''

    countries = df.index.get_level_values(country_name_field).drop_duplicates().values.tolist()
    little_country, little_cases = (countries[0], df.xs(countries[0], level=country_name_field)[column].max(), )
    
    for country in countries[1:]:
        max_cases =  df.xs(country, level=country_name_field)[column].max()
        if max_cases < little_cases:
            little_country, little_cases = (country, max_cases,)
    return ceil(little_cases * ratio)
    
    
def pivot_with_overlap(df, country_name_field, column= 'cases', threshold=THRESHOLD):
    '''pivot a dataframe iterating over columns and dates traslating values to start at the same date
    
    params 
        - df                     pandas dataframe MultiIndex: dateRep+country_name_field (countries | continents)
        - country_name_field     str - coutriesAndTerritories|continentExp
        - column                 str - column with values to check: cases|deaths
        - threshold              int - value to overcome for two consecutive days
    
    return
        - sdf       pandas dataframe
        - None      in case of empty dataframe
    
    remark.
      given a (MultiIndex) df as   date+country cases death with:
        - date       a date
        - country    a country
        - cases      the total cases on the day (i.e, 
                       - if march 01 2020 cases is 100 @ Italy and we have 10 new cases in Italy that day,
                       -  then: march 02 2020 cases value is 110 @ Italy)
        - death      the total number of deceased on the day (same consideration as above) 
      example                        cases death 
                 date ...   country  
                 2020-03-01 country1  0     0     
                 2020-03-01 country2  80    8     
                 2020-03-02 country1  10    0     
                 2020-03-02 country2  20    8     
                 2020-03-03 country1  20    1     
                 2020-03-03 countryN  100   11    
                 ...
      this function builds a dataframe as
                 country1 country2 ... countryN
            row
            01   10       80           100
            02   20       20           ...
            03   ...      ...          ...
      where values in countryI are the cases in that country
      
      Warning: this function is pretty slow because iterate over rows
      
      Again: to align, seach a couple of adjacent days that exceed the indicated threshold
    '''
    fname = 'pivot_with_overlap'

    # building an empty df ...
    dates = df.index.get_level_values('dateRep').drop_duplicates().values.tolist()
    countries = df.index.get_level_values(country_name_field).drop_duplicates().values.tolist()

    sdf = pd.DataFrame(columns=[[],[]])                          # empty df, hierachical columns (two levels)
    #    ... iterating over countries ...
    for country in countries:
        #acountry = df[df[country_name_field]==country]
        acountry = df.xs(country, level=country_name_field)
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
    return sdf



def stretch(df, height):
    '''raise the height of a dataframe to the requested size'''
    if df.shape[0] >= height:
        return df
    
    for ndx in range(df.shape[0], height):
        df.loc[ndx] = np.NaN * df.shape[1]
    return df

