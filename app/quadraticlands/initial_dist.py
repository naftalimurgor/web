###
# Script is used to populate the initial token distribution in the DB 
# run form same directory as the initial_dist.csv file 
####

import csv
import os
from decimal import Decimal

from dashboard.models import Profile  # import profile model
from quadraticlands.models import InitialTokenDistribution  # imports the model

path = './app/quadraticlands'
os.chdir(path)

with open('test_initial_dist.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            InitialTokenDistribution.objects.all().delete() # clear the table 
            p = Profile.objects.get(handle=row['handle']) # retrieve user
            amount_in_wei = (Decimal(row['value_created_usd']) * 10**18)
            c = InitialTokenDistribution(profile=p, claim_total=amount_in_wei) # create initial dist record 
            c.save() # save record 
        except Exception as error:
            print(f"User: {row['handle']} was not added. Error: {error}")

exit()
