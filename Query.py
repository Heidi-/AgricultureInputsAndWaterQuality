"""Funciontality to query data from the NASS quickstats and NAWQA APIs.
   Includes functions to simplify and clean the data.
"""

import urllib
import locale
import pandas as pd

class QueryNASS:
    """ Query the NASS quickstats API and return data in pandas dataframe.
        Requires API key from NASS.
    """
    link = 'http://quickstats.nass.usda.gov/api/api_GET/?key={key}&format=CSV'
   
    def __init__(self, key):
    # key is string - either the key or path to file containing the key
        # save the link template in case this fails
        linktemplate = self.link
        # try to read the key from file or use "key" directly
        try:
            self.read_key(key)
        except:
            self.set_api(key) 
        # attempt query to check that key is set
        try:
            self.query()
        except urllib.error.HTTPError as err:
            if err.code == 401:
                self.link = linktemplate
                mes = '"{k}" is not a valid key or file containing a valid key'
                raise ValueError(mes.format(k=key))
            if err.code == 408:
                pass
        return 
         
    def set_api(self, key):
        """ Set API link template with key """
        self.link = self.link.format(key=key)
        return
    
    def read_key(self, filename):
        """ Read API key from filename and set key in instance """
        kfile = open(filename)
        key = kfile.read().strip()
        self.set_api(key)
        return
    
    def query(self, **args):
        """ Query API according with following filters, return dataframe.
            Filters must include the operator (e.g. "=CENSUS" or "__LIKE=LAND")
            source_desc = "CENSUS" or "SURVEY"
            sector_desc = "CROPS", "ANIMALS & PRODUCTS", "ECONOMICS",
                          "DEMOGRAPHICS", or "ENVIRONMENTAL"
            year = Census year, integer
            state_alpha = Two letter abbreviation
            agg_level_desc = Aggregation level: "STATE", "AG DISTRICT", "COUNTY",
                             "REGION", "ZIP CODE"
            freq_desc = Length of time covered: "ANNUAL", "SEASON", "MONTHLY",
                        "WEEKLY", "POINT IN TIME"
        link = link
        """
        if "{key}" in self.link:
            raise NameError("API key not set. Call set_api(key) before query.")
        for k, v in args.items():
            self.link += '&' + k + v
        print("API link is:", self.link) #for debugging
        data = pd.read_csv(self.link)
        return data


class QueryNAWQA:
    """ Query the NAWQA and return data in pandas dataframe. """
    def __init__(self):
        self.link = "http://cida.usgs.gov/nawqa_queries_public/service/surfacewater/csv/serial/read?state={state}&minimumValue={minval}&detect={detect}&parameterCode={chem}&waterYearStart={start}&waterYearEnd={end}"
        self.paramkeys = ["state", "minval", "detect", "start", "end", "chem"]

    def get_param_keys(self):
        return self.paramkeys

    def get_param_dict(self):
        return dict([(k, "") for k in nawqa.paramkeys])

    def query(self, **args):
        print( self.link.format(**args))
        return pd.read_csv(self.link.format(**args))

         
# Functions to clean and simplify data
   
def scrub_missing_data(data):
    """ NASS supresses data for a variety of reasons, including insignifiantly
        small values and anonymity concerns. This function changes the
        supression codes to None and casts the Value column to numerical values.
    """
    supcodes = [' (D)', ' (H)', ' (Z)', ' (NA)']
    for s in supcodes:
        data.replace({"Value":{s:None}}, inplace=True)
    locale.setlocale(locale.LC_NUMERIC, '')
    data.Value = data.Value.apply(lambda x: locale.atoi(x) 
                                            if isinstance(x, str) 
                                            else None) 
    return data

def drop_columns(dataframe, list_columns):
    """ Drop list_columns from the dataframe df """
    for c in list_columns:
        dataframe = dataframe.drop(c, 1)
    return dataframe

def write_data(data, filename):
    """ Write dataframe data to filename as csv. """
    data.to_csv(filename, index=False)
    return

def dicts_to_dataframe(colnames, *ds):
    """ All dictiories passed should have the same keys, which will become
        the index of the dataframe. Column names are in a list colnames.
    """
    df = pd.DataFrame.from_dict(ds[0], orient='index')
    df.columns = [colnames[0]]
    for d,n in zip(ds[1:], colnames[1:]):
        df[n] = df.index.map(d.get)
    return df

