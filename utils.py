import pandas as pd


def create_lookup_table(config, debugmode):

    lookup_table = pd.DataFrame(columns=["instrument","filters"])
    list_filter, list_instruments = [],[]
    for instrument in config.keys():
        for filter in config[instrument]["filter"]:
            list_filter.append(filter)
            list_instruments.append(instrument)
    lookup_table["instrument"] = list_instruments
    lookup_table["filters"] = list_filter

    # Print lookup_table
    if debugmode: print(lookup_table)

    return lookup_table