# :filename: tests/unit_tests.py
# to use: "cd tests; python unit_tests.py"


# import std libs
import os
import sys
import unittest

# import 3rd parties libs
import pandas as pd
from flask            import current_app, g, request, url_for
from werkzeug.routing import Map, Rule, NotFound, RequestRedirect



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
        with self.app.test_request_context('/graph/nations/it-fr/cases/false/false/2020-01-01/2020-03-31'):
            urls = self.app.url_map.bind_to_environ(request.environ)
            endpoint, arguments = urls.match('/graph/nations/it-fr/cases/false/false/2020-01-01/2020-03-31', 'GET')
        self.assertEqual(endpoint, 'views.draw_graph')
        self.assertEqual(arguments['contest'], 'nations')
        self.assertEqual(arguments['ids'], 'it-fr')
        self.assertEqual(arguments['fields'], 'cases')
        self.assertEqual(arguments['normalize'], 'false')
        self.assertEqual(arguments['overlap'], 'false')
        self.assertEqual(arguments['first'], '2020-01-01')
        self.assertEqual(arguments['last'], '2020-03-31')


class ModelsTest(unittest.TestCase):
    '''testing models'''
    
    def setUp(self):
        self.app = create_app({ 'TESTING': True, 'DATA_FILE': 'covid_data_test.csv'})
        
    def tearDown(self):
        pass
        
    def test_dataframe_model(self):
        with self.app.test_request_context('/'):      # create a request context which in turn creates an application context
            df = models.open_df(self.app.config['DATA_DIR']+'/'+self.app.config['DATA_FILE'],
                                pd.read_csv,
                                models.world_shape)                     # stores dataframe in g.df
            self.assertIsInstance(df, pd.DataFrame)             # this could be outside the "with" environment
            self.assertIsInstance(g.df, pd.DataFrame)           #< g MUST be inside an application context
        #print("df shape: {}".format(df.shape))
    
    def test_areas_data(self):
        self.assertEqual(len(models.AREAS.keys()), 4)
        self.assertEqual(models.areas_get_nation_name('EU', 'nations', models.AREAS), 'European_Union')
        self.assertEqual(models.areas_get_names('nations', models.AREAS), ['European_Union'])
        
        
class ViewsTest(unittest.TestCase):
    '''this is to test views'''
    
    def setUp(self):
        #< without <'WTF_CSRF_ENABLED': False>, we are going to receive a csrf token error
        #      when testing for forms, i.e. /select and /other_select URLs using POST
        self.app = create_app({ 'TESTING': True,
                                'DATA_FILE': 'covid_data_test.csv',
                                'WTF_CSRF_ENABLED': False, })
        
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
                                    data={'fields': '1',
                                          'first':  '2020-04-24',
                                          'last':   '2020-04-24',
                                          'contest': 'nations',
                                          'countries': 'AF', },
                                   )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, 
                             'http://localhost' + url_for('views.draw_graph', 
                                                           contest='nations', 
                                                           ids='AF', 
                                                           fields='cases', 
                                                           normalize='False', 
                                                           overlap='False',
                                                           first='2020-04-24',
                                                           last='2020-04-24'
                                                          )
                             )
        
    def test_draw_graph_view(self):
        ''' //graph/nations/AF/cases/False/False/2020-04-24/2020-04-24      -> views.draw_graph'''
        
        with self.app.test_client() as client:
            response = client.get('/graph/nations/AF/cases/False/False/2020-04-24/2020-04-24')
            html = response.data.decode('utf8')          # type(html) == type(str)
        self.assertEqual(response.content_type, 'text/html; charset=utf-8')
        self.assertTrue(html.startswith('<html '))
        self.assertIn('<title>plot</title>', html)
        self.assertTrue(html.endswith('</html>'))
        



if __name__ == '__main__':
    # we need to add the project directory to pythonpath to find covid module in development PC without installing it
    basedir, _ = os.path.split(os.path.abspath(os.path.dirname(__file__)).replace('\\', '/'))
    sys.path.insert(1, basedir)              # ndx==1 because 0 is reserved for local directory
    from covid import create_app             # NOW we find covid module if we import it
    from covid import models
    unittest.main()