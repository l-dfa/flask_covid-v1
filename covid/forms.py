# :filename: covid/forms.py
#   forms of flask_covid project / covid application
#
# marks:   #?      something to discover
#          #<      make attention; maybe we need to remove this line

# std libs import
from datetime import date


# 3rd parties libs import
from flask_wtf   import FlaskForm
from flask_babel import _
from flask_babel import lazy_gettext as _l
#from wtforms     import SelectField
from wtforms     import SelectMultipleField, SubmitField, RadioField
#from wtforms     import DateField
from wtforms.fields.html5     import DateField
#from wtforms.validators import DataRequired
from wtforms.validators import InputRequired, ValidationError

# application libs import


#FIELDS_CHOICES = [('1', 'cases'), ('2', 'deaths'),('3','d²cases/dt²')]
FIELDS = {
    'cases':  {'id': '1',
               'explanation': _l('are the cumulative  cases positive to the infection'),
               'short': _('cumulative positive cases'),
              },
    'deaths': {'id': '2', 
               'explanation': _l('are the cumulative number of persons deceased due to the infection'),
               'short': _('cumulative number of deaths'),
              },
    'd²cases_dt²': {'id': '3', 
                    'explanation': _l('is the second derivative of cumulative positive cases; this indicates if the cases curve has upward or downward concavity'),
                    'short': _l("concavity's orientation of cumulative positive cases"),
                   },
}


# + ldfa,2020-05-17 to show a summary table of chosen fields
FIELDS_IN_TABLE = {
    'cases': 'mean_daily_cases',
    'deaths': 'mean_daily_deaths',
    'd²cases_dt²': 'mean_daily_concavity',
}


class TimeRange(object):
    '''validate  time range set at init time, or later
    note. it uses datetime.date as internal data
    '''
    def __init__(self, first=None, last=None, message=None):
        if not first:
            first = date.today()
        if not last:
            last = date.today()
        self.first = first
        self.last  = last
        if not message:
            message = _l('Field must be between %s and %s') % (first.strftime('%Y-%m-%d'), last.strftime('%Y-%m-%d'),)
        self.message = message
        
    def set_first(self, first):
        self.first = first

    def set_last(self, last):
        self.last = last

    def __call__(self, form, field):
        f = field.data and field.data<self.first
        l = field.data and field.data>self.last
        if f or l:
            raise ValidationError(self.message)


class SelectForm(FlaskForm):
    fields  = SelectMultipleField( _l('Type_of_fields'), validators=[InputRequired()], default=['1'])
    first   = DateField(_l('from'), validators=[InputRequired()], format='%Y-%m-%d')
    last    = DateField(_l('to'),   validators=[InputRequired()], format='%Y-%m-%d')
    contest = RadioField( _l('Type_of_entity'), validators=[InputRequired()], default='nations')
    continents = SelectMultipleField( _l('Countries'))
    countries  = SelectMultipleField( _l('Countries'))
    submit  = SubmitField( _l('plot'))
    
    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False
        
        if(self.contest.data == 'nations' and self.countries.data == []):
            self.countries.errors.append(_l('please select at least a country'))
            return False
        elif(self.contest.data == 'continents' and self.continents.data == []):
            self.continents.errors.append(_l('please select at least a continent'))
            return False
        
        return True
    
    
#def build_select_form(nations):
#    d = dict()
#    for nation in nations:
#        d[nation] = BooleanField(nation)
#    d['submit'] = SubmitField( _l('plot'))
#    return type('SForm', (FlaskForm,), d)