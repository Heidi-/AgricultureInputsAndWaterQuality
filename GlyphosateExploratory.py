import Query
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def nass_chem_input_data(filename):
    """Query NASS quickstats for chemical input amounts and save to filename"""
    nass = Query.QueryNASS("key.txt")
    # Start by grabbing all the environmental sector data
    env = nass.query(state_alpha="=OR", sector_desc="=ENVIRONMENTAL")
    # limit to amount of chemical inputs
    chems = env[env.unit_desc == "LB"]
    # clean it up
    chems = Query.scrub_missing_data(chems)
    # save this for later
    Query.write_data(chems, "data/ChemicalInputAmounts.csv")
    return chems


#TODO write function to parse chemical formula and return molar mass

def glyphosate_in_oregon_waterways():
    nawqa = Query.QueryNAWQA()
    parameters = nawqa.get_param_dict()
    parameters['chem'] = 62722
    parameters['state'] = "OREGON"
    return nawqa.query(**parameters)

def glyphosate_mass_multipliers():
    """ Glyphosphate is applied in multiple chemical forms. This function
        will provide the proportion of the mass of the glyphosphate salt
        that is the glypohsphate anion.
    """
    #molar mass of each atom
    mm = {'O':15.9994, 'N': 14.0067, 'H':1.0079, 'P':30.9738, 'C':12.011}
    mm['K'] = 39.0983
    #glyphosate anion formula: C3H7NO5P-
    mm_gly_anion = 3*mm['C'] + 7*mm['H'] + mm['N'] + 5*mm['O'] + mm['P']
    # "glyphosate iso. salt" has isopropylamineH+ (C3H10N+) as cation
    mm_isopropylamine =  3*mm['C'] + 10*mm['H'] + mm['N']
    # "glyphosate pot. salt" has potassium as cation
    mm_potasium = mm['K']
    # "glyphosate amm salt" has ammonium (NH4+) as cation
    mm_ammonium = mm['N'] + 4*mm['H']
    # glyphosate has H+ as cation (at least we can consider it this way)
    mm_hydrogen = mm['H']
    # find molar mass for each salt
    mm_glyphosate_iso_salt = mm_gly_anion + mm_isopropylamine
    mm_glyphosate_pot_salt = mm_gly_anion + mm_potasium
    mm_glyphosate_amm_salt = mm_gly_anion + mm_ammonium
    mm_glyphosate = mm_gly_anion + mm_hydrogen
    prop = {}
    prop['GLYPHOSATE ISO. SALT = 103601'] = mm_gly_anion/mm_glyphosate_iso_salt
    prop['GLYPHOSATE POT. SALT = 103613'] = mm_gly_anion/mm_glyphosate_pot_salt
    prop['GLYPHOSATE AMM. SALT = 103604'] = mm_gly_anion/mm_glyphosate_amm_salt
    prop['GLYPHOSATE = 417300'] = mm_gly_anion/mm_glyphosate
    return prop

def mass_multiplier_from_dataframe(data):
    """ create multiplier series from data.domaincat_desc """
    prop = glyphosate_mass_multipliers()
    for k,v in prop.items():
        if k in data['domaincat_desc']:
            return v
    return None

def graph_usage_and_water_qualty(application, waterquality):
    xmin = min(min(application.index), min(waterquality.year))
    xmax = max(max(application.index), max(waterquality.year))
    fig = plt.figure(figsize=(8,8))
    g = fig.add_subplot(211)
    g.plot(application.index, application.values/1000, color='k',  marker='.')
    g.set_xlim(xmin, xmax)
    g.set_title("Application of Glyphosate in Oregon Farms")
    g.set_ylabel("Glyphosate Application (1000 lb)")
    h = fig.add_subplot(212)
    h.plot(waterquality.year, waterquality.concentration_ug_per_L, marker='.')
    h.set_xlim(xmin, xmax)
    h.set_title("Glyphosate Measured in Water Samples")
    h.set_ylabel("Average Concentration (ug/L)")
    h.set_xlabel("Year")
    fig.savefig("GlyphosphateApplicationAndWaterQuality.png")
    fig.clear()
    return 
       
def graph_glyphosate_form(data):

    forms = data.columns
    years = data.index

    # define bar properties
    barx = [np.arange(len(years))]
    barwidth = 0.25
    for f in forms[1:]:
        barx.append(barx[-1] + barwidth)
    colors = iter(plt.cm.gist_earth(np.linspace(0,1,len(forms))))
    
    fig = plt.figure()
    g = fig.add_subplot(111)
    for i, f in enumerate(forms):
        color = next(colors)
        bars = data[f]
        flabel = f.lstrip("CHEMICAL, HERBICIDE: (").rstrip(")")
        g.bar(barx[i], bars/1000, barwidth, color=color, label=flabel)
    g.legend(fontsize=10, loc="upper left")
    g.set_xlim(0, barx[0][-1]+1)
    g.set_xlabel("Year")
    g.set_ylabel("Glyphosate Application (1000 lb)")
    g.set_xticks(barx[0])
    g.set_xticklabels(years, rotation=30, size="small")
    g.set_title("Glyphosate Application in Oregon Agriculture by Chemical Form")
    fig.savefig("GlyphosateByChemicalForm.png")
    fig.clear()
    return
    
def main():
    filename_nass_inputs = "data/ChemicalInputAmounts.csv"
    filename_nawqa_glyphosate = "data/NAWQA_glyphosate.csv"
    # read chemical input data from file, or query api for data and write file
    try:
        chems = pd.read_csv(filename_nass_inputs)
    except:
        chems = nass_chem_input_data(filename_nass_inputs)
    # select glyphosate data
    glyphosate = chems[chems.domaincat_desc.str.contains("GLYPHOSATE")]
    # select only relevant columns
    glyphosate = glyphosate[['year', 'domaincat_desc', 'Value']]
    # create new column of lbs glyphosate ion weight, so different forms
    #   of the pesticide are comparable
    mass_proportion = glyphosate.apply(mass_multiplier_from_dataframe, axis=1)
    glyphosate['glyphosate_lb'] = mass_proportion * glyphosate.Value
    # calculate amount of glyphosate applied each year
    annual = glyphosate.groupby('year').sum()
    annual_application = annual.glyphosate_lb
    # investigate how the form of application chemical changed over time
    form = glyphosate.groupby(['year', 'domaincat_desc']).sum().reset_index()
    form = pd.pivot_table(form, 
                          values='glyphosate_lb', 
                          index='year', 
                          columns='domaincat_desc')
    # graph application by form
    graph_glyphosate_form(form)
    
    # now load in the water testing data
    try:
        wq = pd.read_csv(filename_nawqa_glyphosate)
    except:
        glyphosate_in_oregon_waterways(filename_nawqa_glyphosate)
    # for values that are only recorded as "less than", estimate value as 
    #   half the less than value
    wq["value"] = np.where(wq.remarkCode == "<", wq.value * 0.5, wq.value)
    wq["dates"] = pd.to_datetime(wq.resultDateTime)
    water_gly = pd.DataFrame({"site":wq["placeName"], 
                              "year":wq["dates"].apply(lambda x: x.year),
                              "concentration_ug_per_L":wq["value"]}) 
    # group by year and site and take average of all measurements
    water_annual_mean = water_gly.groupby(["year"]).mean().reset_index()
   
    # create graph showing application and water quality measurements
    graph_usage_and_water_qualty(annual_application, water_annual_mean)
    return 

if __name__ == "__main__":
    main()


