import pdb
from itertools import product
import numpy as np
import pandas as pd
from tqdm import tqdm

import loaders
import geography
import visualization as vis


def main(debug: ("Debug mode", 'flag', 'd')):
    if debug:
        vis.DPI = 50
        vis.QUALITY = 75

    vis.plot_cb(orientation='horizontal')
    vis.plot_cb(orientation='vertical')
    vis.plot_p_outbreak()
    print('Loading density')
    specs = loaders.load_density()

    print('calculating coordinate functions')
    specs = geography.get_coordinate_functions(specs)
    if not debug:
        vis.plot_density(specs)

    if debug:
        R0s = [3]
        regions = ['global', 'africa', 'india']
        kappas = [1]
    
    else:
        R0s = [2, 3, 4]
        regions = ['global', 'africa', 'india']
        kappas   = [1, 3, 6]


    print('loading airport data')
    airports = loaders.load_airports(specs)
    if debug:
        airports = airports.loc[vis.airport_list]

    vis.plot_airports(airports, specs['data'])
        
    
    travel = loaders.load_travel(airports)
    times = ['annual', 1, 4, 7, 10]
    travel = {k: travel[k] for k in times}

    ## Get vailid destinations for every region
    destinations = pd.read_csv('./data/airports.csv')
    valid = airports.NodeName.values
    dest_dict = {}
    dest_dict['africa'] = np.intersect1d(valid, destinations.query('continent == "AF"').iata_code.dropna().unique())
    dest_dict['india']  = np.intersect1d(valid, destinations.query('iso_country == "IN"').iata_code.dropna().unique())
    dest_dict['global'] = valid

    for region in regions:
        print()
        print('Making', region, 'plots')
        dest = dest_dict[region]
        vis.plot_geodesics(travel['annual'], destinations=dest, region=region) 

        for wuhan_R0 in R0s:
            wuhan_factor =  wuhan_R0 / airports.loc['WUH', 'density'] # R_0 / density for Wuhan
            airports['R0'] = airports.density * wuhan_factor
            vis.plot_R0(airports)
    
            for kappa in kappas:
                airports['p_no_outbreak_from_one'] = loaders.calculate_p_no_outbreaks(airports, kappa=kappa)
                airports['p_outbreak_from_one'] = 1 - airports.p_no_outbreak_from_one
                if kappa == 1 and wuhan_R0 == 3:
                    cols = ['OAGName', 'Name', 'City', 'density', 'R0', 'p_outbreak_from_one']
                    filename = f'./tables/{region}_airports_annual_wuhan{wuhan_R0}_kappa{kappa}.csv'
                    airports[cols].sort_values('p_outbreak_from_one', ascending=False).to_csv(filename, sep='\t')

                tmp_travel = {k: loaders.augment_travel(df, airports, destinations=dest) for k, df in travel.items()}
                vis.plot_annual_risks(tmp_travel['annual'], kappa=kappa, wuhan_R0=wuhan_R0, region=region)
                vis.plot_monthly_risks(tmp_travel, kappa=kappa, wuhan_R0=wuhan_R0, region=region)
                
                
    
    
if __name__ == '__main__':
    try:
        import plac; plac.call(main)
    except KeyboardInterrupt as e:
        pass
    except:
        import pdb, sys, traceback
        _, _, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)
