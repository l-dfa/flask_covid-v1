# :filename: tests/unit_tests.py
# to use: "cd tests; python unit_tests.py"


# import std libs
from datetime import datetime, date, timedelta
import os
import sys
import unittest

# import 3rd parties libs
import pandas as pd
from flask              import current_app, g, request, url_for
from flask_wtf          import FlaskForm
from wtforms.validators import ValidationError
from werkzeug.routing   import Map, Rule, NotFound, RequestRedirect



class URLsTest(unittest.TestCase):
    '''testing URLs of views'''
    
    def setUp(self):
        self.app = create_app({ 'TESTING': True, })
        
    def tearDown(self):
        pass
        
    def test_root_url_resolves_to_home_page_view(self):
        ''' /      -> views.index'''
        with self.app.test_request_context('/'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/', 'GET')
        self.assertEqual(endpoint, 'views.index')
        #'''/index -> views.index'''
        with self.app.test_request_context('/index'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/index', 'GET')
        self.assertEqual(endpoint, 'views.index')
        #'''/index.html -> views.index'''
        with self.app.test_request_context('/index.html'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/index.html', 'GET')
        self.assertEqual(endpoint, 'views.index')
        
    def test_select_url_resolves_to_select_nations_page_view(self):
        ''' /select  -> views.select'''
        with self.app.test_request_context('/select'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/select', 'GET')
        self.assertEqual(endpoint, 'views.select')
        with self.app.test_request_context('/select'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/select', 'POST')
        self.assertEqual(endpoint, 'views.select')
        
    def test_other_select_url_resolves_to_other_select_page_view(self):
        ''' /other_select  -> views.other_select'''
        with self.app.test_request_context('/other_select'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/other_select', 'GET')
        self.assertEqual(endpoint, 'views.other_select')
        with self.app.test_request_context('/other_select'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/other_select', 'POST')
        self.assertEqual(endpoint, 'views.other_select')

    def test_draw_url_resolves_to_draw_graph_page_view(self):
        ''' /graph/<contest>/<ids>/<fields>/<normalize>/<overlap>/<first>/<last>  -> views.draw_graph'''
        with self.app.test_request_context('/graph/nations/it-fr/cases/false/false/2020-01-01/2020-03-31/false'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/graph/nations/it-fr/cases/false/false/2020-01-01/2020-03-31/false', 'GET')
        self.assertEqual(endpoint, 'views.draw_graph')
        self.assertEqual(arguments['context'], 'nations')
        self.assertEqual(arguments['ids'], 'it-fr')
        self.assertEqual(arguments['fields'], 'cases')
        self.assertEqual(arguments['normalize'], 'false')
        self.assertEqual(arguments['overlap'], 'false')
        self.assertEqual(arguments['first'], '2020-01-01')
        self.assertEqual(arguments['last'], '2020-03-31')


class GeoEntitiesTest(unittest.TestCase):
    '''testing models.GeoEntities'''
    
    def setUp(self):
        self.app = create_app({ 'TESTING': True, 'DATA_FILE': 'covid_data_test.csv'})
        
    def tearDown(self):
        pass
        
    def test_init_app(self):
        self.assertEqual(models.POP_FIELD, 'popData2019')
        self.assertTrue(len(models.GeoEntities) > 0)
    
    def test_set_entity(self):
        length = len(models.GeoEntities)
        models.GeoEntities.set_entity('g', {'type': 'person', 'name': 'goofy'})
        self.assertEqual(len(models.GeoEntities), length+1)
        e = models.GeoEntities.get_entity('g')
        self.assertEqual(e['name'], 'goofy')
        models.GeoEntities.del_entity('g')
        self.assertEqual(len(models.GeoEntities), length)

    def test_set_entity_att(self):
        models.GeoEntities.set_entity_att('AF', 'name', 'AFGHANISTAN')
        n = models.GeoEntities.get_entity_att('AF', 'name')
        self.assertEqual(n, 'AFGHANISTAN')
        models.GeoEntities.del_entity_att('AF', 'name')
        n = models.GeoEntities.get_entity_att('AF', 'name')
        self.assertIsNone(n)
        models.GeoEntities.set_entity_att('AF', 'name', 'Afghanistan')
        
    def test_in(self):
        self.assertTrue('AF' in models.GeoEntities)
        es = models.GeoEntities(ids=['AF', 'AL'])
        self.assertTrue('AF' in es)
        self.assertFalse('Asia' in es)
        
    def test_getitem(self):
        es = models.GeoEntities(ids=['AF', 'AL'])
        self.assertEqual(es['AF']['name'], 'Afghanistan')
        with self.assertRaises(KeyError):
            es['Asia']

    def test_keys(self):
        es = models.GeoEntities(ids=['AF', 'AL'])
        self.assertEqual(list(es.keys()), ['AF', 'AL'])

    def test_values(self):
        es = models.GeoEntities(ids=['AF', 'AL'])
        vals = list(es.values())
        self.assertEqual(len(vals), 2)
        self.assertEqual(vals[0]['name'], 'Afghanistan')

    def test_init(self):
        es = models.GeoEntities()
        self.assertEqual(es.__class__, models.GeoEntities)
        self.assertEqual(len(es), 221)
        oc = models.GeoEntities(attribute='original_country', value=True)
        self.assertEqual(len(oc), 210)
        oc = models.GeoEntities(ids=['AF', 'AL', 'Asia'])
        self.assertEqual(len(oc), 3)

    def test_get_entities_by_att(self):
        es = models.GeoEntities()
        self.assertEqual(len(es), 221)
        oc = es.get_entities_by_att('original_country', True)
        self.assertEqual(len(oc), 210)
        
    def test_get_entities_att(self):
        es = models.GeoEntities()
        noc = es.get_entities_by_att('original_country', False)
        names = noc.get_entities_att('name')
        self.assertEqual(names['Asia'], 'Asia')
        
    def test_get_list_of_keys_names(self):
        oc = models.GeoEntities(attribute='original_country', value=True)
        kn = oc.get_list_of_keys_names()
        self.assertEqual(len(kn), 210)
        self.assertEqual(len(kn[0]), 2)
        kn = oc.get_list_of_keys_names(names_only=True)
        self.assertEqual(len(kn), 210)
        self.assertEqual(kn[0], 'Afghanistan')

    def test_len(self):
        n = len(models.GeoEntities)
        self.assertEqual(n, 221)
        es = models.GeoEntities()
        es.ids = ['AF']
        self.assertEqual(len(es), 1)


class ModelsTest(unittest.TestCase):
    '''testing models'''
    
    def setUp(self):
        self.app = create_app({ 'TESTING': True, 'DATA_FILE': 'covid_data_test.csv'})
        self.df = pd.DataFrame(utd.d)
        self.df['dateRep'] = self.df['dateRep'].map(lambda x: datetime.strptime(x, '%d/%m/%Y').date()) # from str to date
        
    def tearDown(self):
        pass
        
    def test_init_app(self):
        self.assertEqual(models.POP_FIELD, 'popData2019')
        self.assertTrue(len(models.GeoEntities) > 0)
    
    def test_dataframe_model(self):
        with self.app.test_request_context('/'):      # create a request context which in turn creates an application context
            df = models.open_df(self.app.config['DATA_DIR']+'/'+self.app.config['DATA_FILE'],
                                pd.read_csv,
                                models.world_shape)                     # stores dataframe in g.df
            self.assertIsInstance(df, pd.DataFrame)             # this could be outside the "with" environment
            self.assertIsInstance(g.df, pd.DataFrame)           #< g MUST be inside an application context
        #print("df shape: {}".format(df.shape))
    
    def test_get_areas(self):
        ids = models.get_areas(['IT'], direct=False)
        self.assertEqual(len(ids), 1)
        ids = models.get_areas(['North_America'], direct=True)
        self.assertEqual(len(ids), 1)
        
    def test_subset_rows_by_nations(self):
        ndf = models.subset_rows_by_nations(self.df, ['AF'])               # test one item
        self.assertEqual(ndf.shape, (2, 11))
        ndf = models.subset_rows_by_nations(self.df, ['AF', 'AL'])         # test two items
        self.assertEqual(ndf.shape, (4, 11))
        ndf = models.subset_rows_by_nations(self.df, ['AF', 'AL', 'PP'])   # test for not existing code ('PP')
        self.assertEqual(ndf.shape, (4, 11))

    def test_create_rows_by_areas(self):
        ndf = models.create_rows_by_areas(self.df, ['EU'], 'nations', 'popData2019')         # test one item
        self.assertEqual(ndf.shape, (2, 11))
        ndf = models.create_rows_by_areas(self.df, ['EU', 'PP'], 'nations', 'popData2019')   # test for not existing code ('PP')
        self.assertEqual(ndf.shape, (2, 11))
        #models.AREAS['Big_Russia'] = {'context': 'nations',
        #                              'geoId':   'Big_Russia', 
        #                              'countryterritoryCode': 'Big_Russia',
        #                              'continentExp': 'Big_Rusiia', 
        #                              'nations': { "BY": "Belarus",
        #                                           "RU": "Russia",
        #                                         },
        #                             }
        models.GeoEntities.set_entity('Big_Russia', {'context': 'nations',
                                                     'name':    'Big_Russia', 
                                                     'population': 100000000,
                                                     'countryterritoryCode': 'Big_Russia',
                                                     'continentExp': 'Big_Russia', 
                                                     'nations':      ["BY", "RU"],
                                                    })
        ndf = models.create_rows_by_areas(self.df, ['EU', 'Big_Russia'], 'nations', 'popData2019')   # test two items
        self.assertEqual(ndf.shape, (4, 11))
        models.GeoEntities.del_entity('Big_Russia')
        
    def test_select_rows_by_dates(self):
        '''test select_row_by_dates'''
        ndf = models.select_rows_by_dates(self.df, date(2020, 3, 1), date(2020, 3, 31))
        self.assertEqual(ndf.shape, (8,11))
        ndf = models.select_rows_by_dates(self.df, date(2020, 3, 26), date(2020, 4, 30), remember=True)
        self.assertEqual(ndf.shape, (10,11))
        #cases = ndf[ndf['countriesAndTerritories']=='Austria']['cases'].values.item()
        cases = ndf[ndf['countriesAndTerritories']=='Austria'].iloc[0]['cases']
        self.assertEqual(cases, 100)

    def test_subset_cols(self):
        ndf = models.subset_cols(self.df, ['dateRep', 'countriesAndTerritories', 'cases'])
        self.assertEqual(len(ndf.columns), 3)
        ndf = models.subset_cols(self.df, ['dateRep', 'countriesAndTerritories', 'cases'], direct=False)
        self.assertEqual(len(ndf.columns), 11-3)
        
    def test_calculate_cumulative_sum(self):
        ndf = models.calculate_cumulative_sum(self.df, ['cases','deaths'])
        self.assertEqual(ndf.shape, (4,42))
     
    def test_suggest_threshold(self):
        ndf = self.df.groupby(['dateRep', 'countriesAndTerritories']).sum()
        threshold = models.suggest_threshold(ndf, column='cases', ratio=0.1)
        self.assertEqual(threshold, 1)
        
    def test_calculate_cumulative_sum_with_overlap(self):
        ndf = self.df.set_index(['dateRep', 'countriesAndTerritories'])
        ndf = models.calculate_cumulative_sum_with_overlap(ndf, column='cases', threshold=1)
        self.assertEqual(ndf.shape, (2, 3))

        with self.app.test_request_context('/'):      # create a request context which in turn creates an application context
            df = models.open_df(self.app.config['DATA_DIR']+'/'+self.app.config['DATA_FILE'],
                                pd.read_csv,
                                models.world_shape)                     # stores dataframe in g.df
            ddf = models.subset_cols(g.df, ['dateRep', 'cases', 'countriesAndTerritories', 'popData2019'])
            ndf = ddf.groupby(['dateRep', 'countriesAndTerritories']).sum()
            threshold = models.suggest_threshold(ndf, column='cases', ratio=0.05)
            ndf = models.calculate_cumulative_sum_with_overlap(ndf, column='cases', threshold=threshold, normalize=True)

            self.assertIsInstance(df, pd.DataFrame)             # this could be outside the "with" environment
            self.assertIsInstance(g.df, pd.DataFrame)           #< g MUST be inside an application context
        #print("df shape: {}".format(df.shape))

    def test_stretch(self):
        adf = pd.DataFrame({'A': ['A0', 'A1'], 'B': ['B0', 'B1'],})
        ndf = models.stretch(adf, 3)
        self.assertEqual(ndf.shape, (3, 2))

    def test_worst_countries(self):
        l = models.worst_countries(self.df, 'cases', ['AF', 'AL'], 1, 1)
        self.assertEqual(l, ['AF'])
        l = models.worst_countries(self.df, 'cases', ['AF', 'AL'], 1, 1, normalize=True)
        self.assertEqual(l, ['AL'])
        with self.assertRaises(ValueError):
            models.worst_countries(self.df, 'cases', ['AF', 'AL'], -1, 1)
        with self.assertRaises(ValueError):
            models.worst_countries(self.df, 'cases', ['AF', 'AL'], 1, -1)
        with self.assertRaises(ValueError):
            models.worst_countries(self.df, 'cases', ['AF', 'AL'], 2, 1)


class ViewsTest(unittest.TestCase):
    '''this is to test views'''
    
    def setUp(self):
        #< without <'WTF_CSRF_ENABLED': False>, we are going to receive a csrf token error
        #      when testing for forms, i.e. /select and /other_select URLs using POST
        self.app = create_app({ 'TESTING': True,
                                'DATA_FILE': 'covid_data_test.csv',
                                'WTF_CSRF_ENABLED': False, })
        self.df = pd.DataFrame(utd.d)
        self.df['dateRep'] = self.df['dateRep'].map(lambda x: datetime.strptime(x, '%d/%m/%Y').date()) # from str to date
        
    def tearDown(self):
        pass
        
    def test_root_view(self):
        ''' /      -> views.index'''
        with self.app.test_client() as client:
            response = client.get('/')
            html = response.data.decode('utf8')          # type(html) == type(str)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')
        self.assertTrue(html.startswith('<html '))
        self.assertIn('<title>Covid: time trend analysis</title>', html)
        self.assertTrue(html.endswith('</html>'))
        
    def test_select_view_by_get(self):
        ''' /select by GET      -> views.select'''
        with self.app.test_client() as client:
            response = client.get('/select')
            html = response.data.decode('utf8')          # type(html) == type(str)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')
        self.assertTrue(html.startswith('<html '))
        self.assertIn('<title>Select country</title>', html)
        self.assertTrue(html.endswith('</html>'))
        
    def test_select_view_by_post(self):
        ''' /select by POST     -> views.select'''
        with self.app.test_client() as client:
            #breakpoint()             #<
            response = client.post( '/select',
                                    data={'mfields': '1',
                                          'first':  '2020-04-24',
                                          'last':   '2020-04-24',
                                          'context': 'nations',
                                          'countries': 'AF', },
                                   )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, 
                             'http://localhost' + url_for('views.draw_graph', 
                                                           context='nations', 
                                                           ids='AF', 
                                                           fields='cases', 
                                                           normalize='False', 
                                                           overlap='False',
                                                           first='2020-04-24',
                                                           last='2020-04-24',
                                                           remember=False
                                                          )
                             )
    
    def test_draw_graph_view(self):
        #@bp.route('/graph/<context>/<ids>/<fields>/<normalize>/<overlap>/<first>/<last>')

        #''' //graph/nations/AF-AL/cases/False/False/2020-04-24/2020-04-30      -> views.draw_graph'''
        #with self.app.test_client() as client:
        #    response = client.get('/graph/nations/AF-AL/cases/False/False/2020-04-24/2020-04-30')
        #    html = response.data.decode('utf8')          # type(html) == type(str)
        #self.assertEqual(response.content_type, 'text/html; charset=utf-8')
        #self.assertTrue(html.startswith('<html '))
        #self.assertIn('<title>plot</title>', html)
        #self.assertTrue(html.endswith('</html>'))
    
        #''' //graph/nations/AF-AL/cases/False/True/2020-04-24/2020-04-30      -> views.draw_graph'''
        #with self.app.test_client() as client:
        #    response = client.get('/graph/nations/AF-AL/cases/False/True/2020-04-24/2020-04-30')
        #    html = response.data.decode('utf8')          # type(html) == type(str)
        #self.assertEqual(response.content_type, 'text/html; charset=utf-8')
        #self.assertTrue(html.startswith('<html '))
        #self.assertIn('<title>overlap</title>', html)
        #self.assertTrue(html.endswith('</html>'))
    
        ''' //graph/nations/AF-AL/cases/True/True/2020-04-24/2020-04-30      -> views.draw_graph'''
        with self.assertRaises(ValueError):
            with self.app.test_client() as client:
                response = client.get('/graph/nations/AF-AL/cases/True/True/2020-04-24/2020-04-30/False')

    def test_query_patterns(self):
        # 1. test canonical nations
        ndf = views.query_patterns(self.df, 'nations', 'BY-RU', date(2020, 3, 1), date(2020, 3, 31))
        self.assertEqual(ndf.shape, (4,11))
        # 2. test nations areas
        ndf = views.query_patterns(self.df, 'nations', 'EU-RU', date(2020, 3, 1), date(2020, 3, 31))
        self.assertEqual(ndf.shape, (4,11))
        # 3. test canonical continents
        ndf = views.query_patterns(self.df, 'continents', 'Europe-Africa', date(2020, 3, 1), date(2020, 3, 31))
        self.assertEqual(ndf.shape, (2,11))
        # 4. test subcontinents
        models.GeoEntities.set_entity('Big_Russia', {'context': 'continent',          # ATTENTION: continents
                                                     'original_country': False,
                                                     'name':   'Big_Russia', 
                                                     'population': 100000000,
                                                     'countryterritoryCode': 'Big_Russia',
                                                     'continentExp': 'Big_Russia', 
                                                     'nations': ["BY", "RU"],
                                                    })
        ndf = views.query_patterns(self.df, 'continents', 'Europe-Big_Russia', date(2020, 3, 1), date(2020, 3, 31))
        self.assertEqual(ndf.shape, (4,11))
        models.GeoEntities.del_entity('Big_Russia')
        
    def test_table_nations(self):
        ndf = views.query_patterns(self.df, 'nations', 'AF-AL')
        columns = ['cases']
        country_names = ['Afghanistan', 'Albania']
        html_table = views.table_nations(ndf, country_names, columns)
        self.assertTrue(html_table.startswith('<table '))
        self.assertTrue(html_table.endswith('</table>'))
        
    def test_table_last_values(self):
        ndf = views.query_patterns(self.df, 'nations', 'AF-AL')
        columns = ['cases']
        country_names = ['Afghanistan', 'Albania']
        html_table = views.table_last_values(ndf, country_names, columns)
        self.assertTrue(html_table.startswith('<table '))
        self.assertTrue(html_table.endswith('</table>'))


    #def test_nothing(self):
    #    import utd
    #    
    #    self.df = pd.DataFrame(utd.d)
    #    print(self.df.head(6))

#sys.path.append('..')
#from covid.forms import TimeRange, SelForm, SelectForm, OtherSelectForm
class FormsTest(unittest.TestCase):
    '''this is to unit test the bases of forms'''
    
    def setUp(self):
        #self.app = create_app({ 'TESTING': True, })
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow  = self.today + timedelta(days=1)
        self.aftertomorrow = self.today + timedelta(days=2)
        self.tr = forms.Range(min=self.today, max=self.tomorrow)
        
    def tearDown(self):
        pass
        
        
    def test_fields_from_names_to_sids(self):
        sids = forms.fields_from_names_to_sids('cases')
        self.assertEqual(sids, 'cases')
        sids = forms.fields_from_names_to_sids('cases-cases/day')
        self.assertEqual(sids, 'cases-cases_day')

    def test_fields_from_sids_to_names(self):
        names = forms.fields_from_sids_to_names('cases')
        self.assertEqual(names, 'cases')
        names = forms.fields_from_sids_to_names('cases-cases_day')
        self.assertEqual(names, 'cases-cases/day')
        
    def test_timerange_init(self):
        self.assertEqual(self.today,    self.tr.min)
        self.assertEqual(self.tomorrow, self.tr.max )
        self.assertIn('Field must be',  self.tr.message )

    def test_timerange_in_operator(self):
        self.assertFalse( self.yesterday in self.tr )
        self.assertTrue(  self.today     in self.tr )
        self.assertTrue(  self.tomorrow  in self.tr )
        self.assertFalse( self.aftertomorrow in self.tr )
    
    def test_timerange_call_operator(self):
        fform = None
        Ac = type('Aclass', (), {})
        ffield = Ac()
        ffield.data = self.today
        self.assertIsNone( self.tr(fform, ffield) )
        with self.assertRaises(ValidationError):
            ffield.data = self.yesterday
            self.tr(fform, ffield)
    
    def test_list_delta_fields(self):
        l = forms.list_delta_fields(direct=True)
        self.assertEqual(l, ['cases/day', '\N{Greek Capital Letter Delta}cases/day'])
        l = forms.list_delta_fields(direct=False)
        self.assertEqual(l, ['cases', 'deaths'])


if __name__ == '__main__':
    # we need to add the project directory to pythonpath to find covid module in development PC without installing it
    basedir, _ = os.path.split(os.path.abspath(os.path.dirname(__file__)).replace('\\', '/'))
    sys.path.insert(1, basedir)              # ndx==1 because 0 is reserved for local directory
    from covid import create_app             # NOW we find covid module if we import it
    from covid import models
    from covid import forms
    from covid import views
    import utd
    unittest.main()
    
    

# START section about deleted code

    #def test_areas_data(self):
    #    self.assertEqual(len(models.AREAS.keys()), 5)
    #    self.assertEqual(models.areas_get_nation_name('EU', 'nations', models.AREAS), 'European_Union')
    #    self.assertEqual(models.areas_get_names('nations', models.AREAS), ['European_Union'])
        
    #def test_is_id_in_area(self):
    #    self.assertTrue( models.is_id_in_areas('EU', 'nations'))
    #    self.assertFalse( models.is_id_in_areas('UE', 'nations'))
    #    self.assertTrue( models.is_id_in_areas('EU'))
    #    self.assertFalse( models.is_id_in_areas('UE'))

    #def test_get_geographic_name(self):
    #    nations = models.Nations()
    #    nations['Asia'] = {'CN': 'China',
    #                       'IN': 'India',
    #                      }
    #    n = models.get_geographic_name('Asia', nations)
    #    self.assertEqual(n, 'Asia')
    #    n = models.get_geographic_name('CN', nations)
    #    self.assertEqual(n, 'China')
    #    n = models.get_geographic_name('EU', nations)
    #    self.assertEqual(n, 'European_Union')
    #    with self.assertRaises(ValueError):
    #        models.get_geographic_names('AL', nations)
        
    #def test_get_geographic_names(self):
    #    nations = models.Nations()
    #    nations['Asia'] = {'CN': 'China',
    #                       'IN': 'India',
    #                       }
    #    l = models.get_geographic_names(['Asia', 'CN', 'EU', 'North_America'], nations)
    #    self.assertEqual(l, ['Asia',
    #                         'China',
    #                         'European_Union',
    #                         'North_America'])
    #    with self.assertRaises(ValueError):
    #        models.get_geographic_names(['CN-AL'], nations)
        


# END   section about deleted code
    