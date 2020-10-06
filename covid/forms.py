# :filename: covid/forms.py
#   forms of flask_covid project / covid application
#
# marks:   #?      something to discover
#          #<      make attention; maybe we need to remove this line

# std libs import
from datetime import date
#import copy

# 3rd parties libs import
from flask       import current_app, g
from flask_wtf   import FlaskForm
from flask_babel import _
from flask_babel import lazy_gettext as _l
#from wtforms     import SelectField
#from wtforms     import DateField
from wtforms     import (
     SelectMultipleField, SubmitField, RadioField, BooleanField, IntegerField
)
from wtforms.fields.html5     import DateField
#from wtforms.validators import DataRequired
from wtforms.validators import InputRequired, ValidationError

# application libs import


#FIELDS_CHOICES = [('1', 'cases'), ('2', 'deaths'),('3','d²cases/dt²')]
FIELDS = {
    'cases':  {'id': '1',
               'explanation': _l('are the cumulative  cases positive to the infection'),
               'short': _('cumulative positive cases'),
               'sid': 'cases',                                 # symbolic id, to use in url
               'delta_field': False,                           # this will be a cumulative value
               'mean_tag': 'mean cases/day'                    # summary table column tag
              },
    'deaths': {'id': '2', 
               'explanation': _l('are the cumulative number of persons deceased due to the infection'),
               'short': _('cumulative number of deaths'),
               'sid': 'deaths',
               'delta_field': False,
               'mean_tag': 'mean deaths/day'
              },
    'cases/day': {'id': '3', 
                  'explanation': _l('you can think this as the derivative of the cumulative number of cases positive to the infection; this is the steepness of the cumulative curve'),
                  'short': _('positive cases per day'),
                  'sid': 'cases_day',
                  'delta_field': True,                          # this is every day value
                  'mean_tag': 'mean cases/day'
              },
    '\N{Greek Capital Letter Delta}cases/day': {'id': '4', 
                    'explanation': _l('it is the second derivative of cumulative positive cases; this indicates if the cases curve has upward (if > 0) or downward (if < 0) concavity'),
                    'short': _l("\N{Greek Capital Letter Delta}cases per day"),
                    'sid': '\N{Greek Capital Letter Delta}cases_day',
                    'delta_field': True,
                    'mean_tag': 'mean \N{Greek Capital Letter Delta}cases/day'
                   },
}

OTHER_CHOICES = [('World', 'World',), ('Worst_World', 'Worst World',), ('Worst_EU', 'Worst EU',)]

def dict_delta_fields(direct=True):
    '''dict delta fields from FIELDS
    
    parameters:
        - direct    bool - if True returns delta fields, otherwise not delta fields
    
    return:
        - result    dict of delta_fields 
    
    remarks: see list_delta_fields
    '''
    if direct:
        return {name: vals for name, vals in FIELDS.items() if FIELDS[name]['delta_field']}
    else:
        return {name: vals for name, vals in FIELDS.items() if not FIELDS[name]['delta_field']}
    

def list_delta_fields(direct=True):
    '''list delta fields from FIELDS
    
    parameters:
        - direct    bool - if True returns delta fields, otherwise not delta fields
    
    return:
        - result        list of delta_fields names
    
    remarks
        - FIELDS    dict - with record struct:
                        {field_name: {id: id_num,
                                      explanation: explanation_string,
                                      short:       short_explanation_string,
                                      delta_field: True|False,
                                      mean_tag:    summary_table_column_tag,
                                     }
                        } 
    '''
    if direct:
        return [name for name in FIELDS.keys() if FIELDS[name]['delta_field']]
    else:
        return [name for name in FIELDS.keys() if not FIELDS[name]['delta_field']]

def fields_from_names_to_sids(fields):        # + ldfa@2020.09.09 getting from views.py
    '''converts form.FIELD names to form.FIELD symbolic ids
    
    param: field           str - of form.FIELD names separated by '-'
    
    return: str - of form.FIELD symbolic ids separated by '-'
    '''
    columns = fields.split('-')
    sids = [FIELDS[name]['sid'] for name in FIELDS.keys() if name in columns ]
    return '-'.join(sids)


def fields_from_sids_to_names(fields):       # + ldfa@2020.09.09 getting from views.py
    '''converts form.FIELD symbolic ids to form.FIELD symbolic names
    
    param: field           str - of form.FIELD symbolic ids separated by '-'
    
    return: str - of form.FIELD names separated by '-'
    
    remark the acronyms:
      - ids       identities
      - sid       symbolic identity
    '''
    columns = fields.split('-')
    names =  [name for name in FIELDS.keys() if FIELDS[name]['sid'] in columns ]
    return '-'.join(names)


class TimeRange(object):
    '''validate  time range set at init time, or later
    note. it uses datetime.date as internal data
    '''
    def __init__(self, first=None, last=None, message=None):
        #fname = 'TimeRange().__init__'
        #current_app.logger.debug('> {}(self={},first={},last={},message={})'.format(fname, self, first, last, message))
        if not first:
            first = date.today()
        if not last:
            last = date.today()
        if not message:
            message = _l('Field must be between %s and %s') % (first.strftime('%Y-%m-%d'), last.strftime('%Y-%m-%d'))
        self.first = first
        self.last  = last
        self.message = message
        
    def set_first(self, first):
        #fname = 'TimeRange().set_first'
        #current_app.logger.debug('> {}(self={},{})'.format(fname, self, first))
        self.first = first

    def set_last(self, last):
        #fname = 'TimeRange().set_last'
        #current_app.logger.debug('> {}(self={},{})'.format(fname, self, last))
        self.last = last
        
    #+ ldfa@2020-08-17 simplifying
    def __contains__(self, item):
        return self.first <= item and item <= self.last

    #+ ldfa@2020-08-17 simplifying
    def __call__(self, form, field):
        fname = 'TimeRange().__call__'
        #current_app.logger.debug('> {}(self={},form={},field={})'.format(fname, self, form, field))
        if not field.data in self:
            #current_app.logger.info('> {}(self={},form={},field={}) - < ValidationError TRIGGERED'.format(fname, self, form, field))
            raise ValidationError(self.message)


class Interval(object):
    '''validate  interval range set at init time, or later
    note. it uses n1 as left extreme point of the interval, while n2 is the right extreme point
    '''
    def __init__(self, n1=1, n2=1, message=None):
        if not message:
            message = _l('Field must be between %s and %s') % (n1, n2)
        self.n1 = n1
        self.n2 = n2
        self.message = message
        
    def set_n1(self, n1):
        self.n1 = n1

    def set_n2(self, n2):
        self.n2 = n2
        
    def __contains__(self, item):
        return self.n1 <= item and item <= self.n2

    def __call__(self, form, field):
        fname = 'TimeRange().__call__'
        if not field.data in self:
            raise ValidationError(self.message)


class SelForm(FlaskForm):
    '''this is a base form with common fields:
    
       - fields             what type of observations to show: cases, deaths, ...
       - first, last        "from" and "to" date fields
       - submit             the fateful "subit" button
    '''
    
    mfields  = SelectMultipleField( _l('Type_of_main_fields'), validators=[InputRequired()], default=['1'])
    sfields  = SelectMultipleField( _l('Type_of_secondary_fields'), validators=[])
    ratio_to_population = BooleanField( _l('Ratio to population'), default=False)
    first   = DateField(_l('from'), validators=[InputRequired()], format='%Y-%m-%d')    # note: adding TimeRange() here as a validator does not work
    last    = DateField(_l('to'),   validators=[InputRequired()], format='%Y-%m-%d')    #    'cause here we cannot get the FIRST and LAST dates to use to initialize it
                                                                                        #    so, we'll need to append it in views
    submit  = SubmitField( _l('plot'))
    
    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False
        
        if(self.last.data<self.first.data):
            self.last.errors.append(_l('it must be "from" %(first)s <= "to" %(last)s ', 
                                       first=self.first.data.strftime('%Y-%m-%d'),
                                       last=self.last.data.strftime('%Y-%m-%d')))
            return False
        
        return True


class SelectForm(SelForm):
    '''form to select nation(s) or continent(s):
    
      adds contest     will be nations or continents
      - continents     a list of
      - countries      like above
    '''
    context = RadioField( _l('Type_of_entity'), validators=[InputRequired()], default='nations')
    continents = SelectMultipleField( _l('Continents'))
    countries  = SelectMultipleField( _l('Countries'))
    
    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False
        
        if(self.context.data == 'nations' and self.countries.data == []):
            self.countries.errors.append(_l('please select at least a country'))
            return False
        elif(self.context.data == 'continents' and self.continents.data == []):
            self.continents.errors.append(_l('please select at least a continent'))
            return False
        
        return True
   
   
class OtherSelectForm(SelForm):
    '''form to select some other type of query
    
       by now: world
    '''
    query   = RadioField( _l('Type_of_query'), validators=[InputRequired()], default='World')
    n1 = IntegerField(_l('Left index'))
    n2 = IntegerField(_l('Right index'))
    
    
    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False
        
        return True
    
    


# START section about deleted code

# - ldfa,2020.09.27 converting
#def dict_delta_fields(fd=None, direct=True):
#    '''dict delta fields from field dictionary fd
#    
#    parameters:
#        - fd            dict - with record struct:{field_name: {id: id_num,
#                                                                explanation: explanation_string,
#                                                                short:       short_explanation_string,
#                                                                delta_field: True|False,
#                                                                mean_tag:    summary_table_column_tag,
#                                                               }
#                                                  }
#    
#    return:
#        - result        list of delta_fields names
#    '''
#    
#    if fd is None: fd = FIELDS
#    result = dict()
#    for k, v in fd.items():
#        if v['delta_field']: 
#            if direct:
#                result[k] = v
#        else:
#            if not direct:
#                result[k] = v
#    return result


# +- ldfa,2020.09.27 converting
#def list_delta_fields(fd=None, direct=True):
#    '''list delta fields from field dictionary fd
#    
#    parameters:
#        - fd            dict - with record struct:{field_name: {id: id_num,
#                                                                explanation: explanation_string,
#                                                                short:       short_explanation_string,
#                                                                delta_field: True|False,
#                                                                mean_tag:    summary_table_column_tag,
#                                                               }
#                                                  }
#    
#    return:
#        - result        list of delta_fields names
#    '''
#    
#    if fd is None: fd = FIELDS
#    result = []
#    for k, v in fd.items():
#        if v['delta_field']: 
#            if direct:
#                result.append(k)
#        else:
#            if not direct:
#                result.append(k)
#    return result
    
# END   section about deleted code
