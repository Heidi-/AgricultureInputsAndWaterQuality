import Query

def main():
    """Print the top 20 chemical inputs by weight used in Oregon agriculture"""
    nass = Query.QueryNASS("key.txt")
    # Start by grabbing all the environmental sector data
    env = nass.query(state_alpha="=OR", sector_desc="=ENVIRONMENTAL")
    # limit to amount of chemical inputs
    chems = env[env.unit_desc == "LB"]
    # save this for later
    Query.write_data(chems, "data/ChemicalInputAmounts.csv")
    # clean it up
    chems = Query.scrub_missing_data(chems)
    # groupby input to find the chemical with largest cumulative application
    #   over all years, crops, and locations for which there is data
    cumchems = chems.groupby("domaincat_desc").sum()
    print("domain category                 weight of chemical applied (lb)")
    print(cumchems.Value.sort(inplace=False, na_position='first').tail(20))
    return
   

if __name__ == "__main__":
    main()
