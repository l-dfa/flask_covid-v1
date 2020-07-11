# :filename: tests/functional_tests.py

# import std libs
import unittest

# import 3rd parties libs
from selenium import webdriver

class VisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()
        
    def test_can_start_index(self):
        # Edith has heard about a cool new online covid app.
        #  She goes to check out its homepage
        self.browser.get('http://localhost:5000/')

        # She notices the page title and header mention Covid
        self.assertIn('Covid', self.browser.title)

    def test_can_start_select(self):
        # She is invited to select one (or more) nation(s)
        self.browser.get('http://localhost:5000/select')

        # She notices the page title and header mention Covid
        self.assertIn('Select country', self.browser.title)
        
    def test_remainder_to_finish_the_test(self):
        self.fail('Finish the test')
        
        # She go to select "Italy" and "United States"
        # When she hits enter, the page updates, and now the page shows
        # the diagram of total cases for these nations
        # Satisfied, she goes back to sleep


if __name__ == '__main__':
    unittest.main()