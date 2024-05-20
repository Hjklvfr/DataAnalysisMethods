import json
import os
import csv

DATA_LOCATION = "I:\\curlybrackets\\raw"

def convert_to_csv():
    dataddd = []
    for file in os.listdir(DATA_LOCATION):
        ppp = os.path.join(DATA_LOCATION, file)
        if os.path.isfile(ppp):
            with open(ppp, 'r') as f:
                data = json.load(f)
                print(file)
                dataddd.extend(data)

    keys = dataddd[0].keys()
    with open('trades.csv', 'w', newline='') as ccccc:
        writer = csv.DictWriter(ccccc, keys)
        writer.writeheader()
        writer.writerows(dataddd)



convert_to_csv()
