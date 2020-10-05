# gn.py  get nations
#  
# create a dict of 'geoId', 'countriesAndTerritories' from covid19-worldwide.csv
#

import pandas as pd
import json
#breakpoint()

FNAME = './instance/data/covid19-worldwide.csv'
FGEOE  = './instance/data/geoentities.json'


AREAS = {'European_Union': {'context': 'nations',
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
         'Central_America':{'context': 'continents',
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
         'North_America':{'context': 'continents',
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
         'South_America':{'context': 'continents',
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
         'World':{'context': 'continents',
                 'geoId':   'World',                 # MUST be equal to name
                 'countryterritoryCode': 'World',
                 'continentExp': 'World',            # MUST be equal to name
                 'nations': {'AF': 'Afghanistan', 'AL': 'Albania', 'DZ': 'Algeria',
                             'AD': 'Andorra', 'AO': 'Angola', 'AI': 'Anguilla',
                             'AG': 'Antigua_and_Barbuda', 'AR': 'Argentina', 'AM': 'Armenia',
                             'AW': 'Aruba', 'AU': 'Australia', 'AT': 'Austria',
                             'AZ': 'Azerbaijan', 'BS': 'Bahamas', 'BH': 'Bahrain',
                             'BD': 'Bangladesh', 'BB': 'Barbados', 'BY': 'Belarus',
                             'BE': 'Belgium', 'BZ': 'Belize', 'BJ': 'Benin',
                             'BM': 'Bermuda', 'BT': 'Bhutan', 'BO': 'Bolivia',
                             'BQ': 'Bonaire, Saint Eustatius and Saba', 'BA': 'Bosnia_and_Herzegovina',
                             'BW': 'Botswana', 'BR': 'Brazil', 'VG': 'British_Virgin_Islands',
                             'BN': 'Brunei_Darussalam', 'BG': 'Bulgaria', 'BF': 'Burkina_Faso',
                             'BI': 'Burundi', 'KH': 'Cambodia', 'CM': 'Cameroon',
                             'CA': 'Canada', 'CV': 'Cape_Verde', 'JPG11668': 'Cases_on_an_international_conveyance_Japan',
                             'KY': 'Cayman_Islands', 'CF': 'Central_African_Republic', 'TD': 'Chad',
                             'CL': 'Chile', 'CN': 'China', 'CO': 'Colombia',
                             'KM': 'Comoros', 'CG': 'Congo', 'CR': 'Costa_Rica',
                             'CI': 'Cote_dIvoire', 'HR': 'Croatia', 'CU': 'Cuba',
                             'CW': 'Curaçao', 'CY': 'Cyprus', 'CZ': 'Czechia',
                             'CD': 'Democratic_Republic_of_the_Congo',
                             'DK': 'Denmark', 'DJ': 'Djibouti', 'DM': 'Dominica',
                             'DO': 'Dominican_Republic', 'EC': 'Ecuador', 'EG': 'Egypt',
                             'SV': 'El_Salvador', 'GQ': 'Equatorial_Guinea', 'ER': 'Eritrea',
                             'EE': 'Estonia', 'SZ': 'Eswatini', 'ET': 'Ethiopia',
                             'FK': 'Falkland_Islands_(Malvinas)', 'FO': 'Faroe_Islands', 'FJ': 'Fiji',
                             'FI': 'Finland', 'FR': 'France', 'PF': 'French_Polynesia',
                             'GA': 'Gabon', 'GM': 'Gambia', 'GE': 'Georgia',
                             'DE': 'Germany', 'GH': 'Ghana', 'GI': 'Gibraltar',
                             'EL': 'Greece', 'GL': 'Greenland', 'GD': 'Grenada',
                             'GU': 'Guam', 'GT': 'Guatemala', 'GG': 'Guernsey',
                             'GN': 'Guinea', 'GW': 'Guinea_Bissau', 'GY': 'Guyana',
                             'HT': 'Haiti', 'VA': 'Holy_See', 'HN': 'Honduras',
                             'HU': 'Hungary', 'IS': 'Iceland', 'IN': 'India',
                             'ID': 'Indonesia', 'IR': 'Iran', 'IQ': 'Iraq', 
                             'IE': 'Ireland', 'IM': 'Isle_of_Man', 'IL': 'Israel',
                             'IT': 'Italy', 'JM': 'Jamaica', 'JP': 'Japan',
                             'JE': 'Jersey', 'JO': 'Jordan', 'KZ': 'Kazakhstan', 
                             'KE': 'Kenya', 'XK': 'Kosovo', 'KW': 'Kuwait', 
                             'KG': 'Kyrgyzstan', 'LA': 'Laos', 'LV': 'Latvia',
                             'LB': 'Lebanon', 'LS': 'Lesotho', 'LR': 'Liberia',
                             'LY': 'Libya', 'LI': 'Liechtenstein', 'LT': 'Lithuania',
                             'LU': 'Luxembourg', 'MG': 'Madagascar', 'MW': 'Malawi',
                             'MY': 'Malaysia', 'MV': 'Maldives', 'ML': 'Mali',
                             'MT': 'Malta', 'MR': 'Mauritania', 'MU': 'Mauritius',
                             'MX': 'Mexico', 'MD': 'Moldova', 'MC': 'Monaco', 
                             'MN': 'Mongolia', 'ME': 'Montenegro', 'MS': 'Montserrat', 
                             'MA': 'Morocco', 'MZ': 'Mozambique', 'MM': 'Myanmar',
                             'NA': 'Namibia', 'NP': 'Nepal', 'NL': 'Netherlands',
                             'NC': 'New_Caledonia', 'NZ': 'New_Zealand', 'NI': 'Nicaragua',
                             'NE': 'Niger', 'NG': 'Nigeria', 'MK': 'North_Macedonia',
                             'MP': 'Northern_Mariana_Islands', 'NO': 'Norway', 'OM': 'Oman',
                             'PK': 'Pakistan', 'PS': 'Palestine', 'PA': 'Panama', 
                             'PG': 'Papua_New_Guinea', 'PY': 'Paraguay', 'PE': 'Peru', 
                             'PH': 'Philippines', 'PL': 'Poland', 'PT': 'Portugal', 
                             'PR': 'Puerto_Rico', 'QA': 'Qatar', 'RO': 'Romania', 
                             'RU': 'Russia', 'RW': 'Rwanda', 'KN': 'Saint_Kitts_and_Nevis', 
                             'LC': 'Saint_Lucia', 'VC': 'Saint_Vincent_and_the_Grenadines', 
                             'SM': 'San_Marino', 'ST': 'Sao_Tome_and_Principe', 'SA': 'Saudi_Arabia', 
                             'SN': 'Senegal', 'RS': 'Serbia', 'SC': 'Seychelles', 
                             'SL': 'Sierra_Leone', 'SG': 'Singapore', 'SX': 'Sint_Maarten', 
                             'SK': 'Slovakia', 'SI': 'Slovenia', 'SO': 'Somalia', 
                             'ZA': 'South_Africa', 'KR': 'South_Korea', 'SS': 'South_Sudan', 
                             'ES': 'Spain', 'LK': 'Sri_Lanka', 'SD': 'Sudan', 
                             'SR': 'Suriname', 'SE': 'Sweden', 'CH': 'Switzerland', 
                             'SY': 'Syria', 'TW': 'Taiwan', 'TJ': 'Tajikistan', 
                             'TH': 'Thailand', 'TL': 'Timor_Leste', 'TG': 'Togo', 
                             'TT': 'Trinidad_and_Tobago', 'TN': 'Tunisia', 'TR': 'Turkey',
                             'TC': 'Turks_and_Caicos_islands', 'UG': 'Uganda', 'UA': 'Ukraine', 
                             'AE': 'United_Arab_Emirates', 'UK': 'United_Kingdom', 'TZ': 'United_Republic_of_Tanzania', 
                             'US': 'United_States_of_America', 'VI': 'United_States_Virgin_Islands', 'UY': 'Uruguay',
                             'UZ': 'Uzbekistan', 'VE': 'Venezuela', 'VN': 'Vietnam', 
                             'EH': 'Western_Sahara', 'YE': 'Yemen', 'ZM': 'Zambia', 'ZW': 'Zimbabwe'}
                 },
        }


READ_JSON  = False
READ_CSV   = True
WRITE_JSON = True
PRINT      = False
GETS = False

class MC(type):
    def __repr__(self):
        return self.__repr__(self)
        
    def __str__(self):
        return self.__repr__(self)
        
    def __len__(self):
        return self.__len__(self)

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
        if type(value) is not type(dict()):
            raise ValueError('setting geographic entity requires a <dict> as value, not {}'.format(type(value)))
        cls._entities[id] = value
        
    @classmethod
    def get_entity(cls, id):
        return cls._entities.get(id, None)

    @classmethod
    def set_entity_att(cls, id, attribute, value):
        e = cls._entities.get(id, None)
        if e is not None:
            e[attribute] = value
        else:
            cls.set_entity(id, {attribute: value})

    @classmethod
    def get_entity_att(cls, id, attribute):
        e = cls._entities.get(id, None)
        if e is not None:
            return e.get(attribute, None)
        return None
    
    @classmethod
    def get_entities_by_att(cls, attribute, value):
        resp = dict()
        for k, v in cls._entities.items():
            vatt = v.get(attribute, None)
            if vatt and vatt==value:
                resp[k] = v
        if resp == dict():
            resp = None
        return resp
    
    @classmethod
    def get_list_of_keys_names(cls, d, names_only=False):
        ''' from dict, extract (key, name,) pairs'''
        fname = 'get_list_of_keys_and_names'
        resp = []
        assert d is not None, '{} got a None instead of a dict of geographic identities'.format(fname)
        for k, v in d.items():
            if names_only:
                resp.append(v['name'])
            else:
                resp.append((k, v['name'],))
        return tuple(resp)
    
    
    def __repr__(self):          # here the self object is the class, NOT a GeoIdentities instance
        #return str(GeoEntities._entities)   # as a memo
        return str(self._entities)
        
    def __len__(self):          # as above: here the self object is the class
        return len(self._entities)

def load_countries(df):
    ndf = df[['geoId', 'countriesAndTerritories', 'countryterritoryCode', 'popData2019', 'continentExp']].drop_duplicates()
    # from https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
    for index, row in ndf.iterrows():
        GeoEntities.set_entity(row['geoId'], {'type': 'nation',
                                              'original_country': True,
                                              'name':         row['countriesAndTerritories'],
                                              'population':   row['popData2019'],
                                              'countryterritoryCode': row['countryterritoryCode'],
                                              'continentExp': row['continentExp'],
                                              'nations': (row['geoId'],),
                                            })


def load_continents(df):
    continents = df['continentExp'].drop_duplicates()
    for continent in continents:
        ndf = df[df['continentExp']==continent]
        ndf = ndf[['geoId', 'popData2019']].drop_duplicates()
        nations = ndf['geoId'].to_list()
        population = ndf['popData2019'].sum()
        GeoEntities.set_entity(continent, {'type': 'continent',
                                           'original_country': False,
                                           'name':         continent,
                                           'population':   population,
                                           'countryterritoryCode': continent,
                                           'continentExp': continent,
                                           'nations': tuple(nations),
                                         })


def load_areas(areas):
    for k, v in areas.items():
        nations = tuple(v['nations'].keys())
        # calc population using GeoIdentities
        population = 0
        for nation in nations :
            locals = GeoEntities.get_entity_att(nation, 'population')
            population = population + locals if not pd.isnull(locals) else population
        GeoEntities.set_entity(v['geoId'], {'type': v['context'][:len(v['context'])-1],
                                            'original_country': False,
                                            'name':         k,
                                            'population':   population,
                                            'countryterritoryCode': v['countryterritoryCode'],
                                            'continentExp': v['continentExp'],
                                            'nations': nations,
                                          })


def load_from_csv(fname):
    df = pd.read_csv(fname)
    
    load_countries(df)
    load_continents(df)
    load_areas(AREAS)


def main():
    if READ_JSON:
        with open(FGEOE, 'r') as f:
            GeoEntities._entities = json.load(f)
    if READ_CSV:
        load_from_csv(FNAME)
    if PRINT:
        print('-------- GeoEntities -----------')
        print(GeoEntities)
        print('-------- ----------- -----------')
        print('num.of entities: {}'.format(len(GeoEntities)))
    if GETS:
        sel = GeoEntities.get_entities_by_att('original_country', True)
        print('len sel: {}'.format(len(sel)))
        print(GeoEntities.get_list_of_keys_names(sel))
        print(GeoEntities.get_list_of_keys_names(sel, names_only=True))
        
    if WRITE_JSON:
        with open(FGEOE, 'w') as f:
            #json.dump(GeoEntities._entities, f)
            s = json.dumps(GeoEntities._entities)
            s = s.replace(' NaN,', ' "Nan",')
            s = s.replace(' "NaN":', ' "NA":')
            s = s.replace(' [NaN]', ' ["NA"]')
            
            s = s.replace('"MZ", "Nan", "NE",', '"MZ", "NA", "NE",')
            f.write(s)
    
if __name__=='__main__':
    #import timeit
    #timeit.timeit('main()', number=10)
    main()