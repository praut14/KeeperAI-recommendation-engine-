# Create randomized dataset for profile recommendation engine
import numpy as np
import pandas as pd
from faker import Faker

NUM_ROWS = 500
MIN_SCORE = 0 + np.finfo('float64').eps # scores must be greater than 0
MAX_SCORE = 100
# probability for user to be in any given affinity group
GROUP_PROB = 0.25

fake = Faker()
rng = np.random.default_rng()

scores = ['O_score', 'C_score', 'E_score', 'A_score', 'N_score']
groups = []
with open("./config/groups.txt") as file:
  for line in file:
    groups.append(line.strip())
    
# a value of group_score for an affinity group column means that the user is in the affinity group, otherwise it will be 0 
# the intention behind this equation is to make total affinity group membership have equal weighting with OCEAN score
group_score = (len(scores) * MAX_SCORE) / len(groups)
cols = ['name'] + scores + groups

data = pd.DataFrame(np.nan, index=range(NUM_ROWS), columns=cols)

data['name'] = [fake.name() for i in range(NUM_ROWS)]
for col in data.columns:
    if col in scores:  
      data[col] = rng.uniform(low=MIN_SCORE, high=MAX_SCORE, size=NUM_ROWS)
    if col in groups:
      data[col] = rng.choice([0, group_score], p=[1-GROUP_PROB, GROUP_PROB], size=NUM_ROWS)
data.to_excel("./data/random_user_data.xlsx")
