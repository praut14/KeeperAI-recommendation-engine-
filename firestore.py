import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

import pandas as pd

#MAX_SCORE = 5

# Initialize connection to firebase
cred = credentials.Certificate("./config/keeper-hr-test-key.json")
firebase_admin.initialize_app(cred)
database = firestore.client()

# Get affinity group collection
affinityGroups = database.collection("AffinityGroups").stream()

# Store groups in array and write the list to groups.txt
groups = []
with open("./config/groups.txt", 'w') as file:
   for group in affinityGroups:    #checking fivefactorscores like cooperativeness ,sociability etc
      groups.append(group.id)
      file.write(f'{group.id}\n')

#group_score = (5 * MAX_SCORE) / len(groups) 

# Get the documents in user collection
users_query = database.collection("users").where(
    filter=FieldFilter("profiles.default.isComplete", "==", True)
)

# Stream the results
users = users_query.stream()

user_list = []
# Compile relevant user data
for user in users:
   user_data = user.to_dict()
   try:
      # Check if the user has a complete fiveFactorsScores field. Ignore them otherwise
      if len(user_data['profiles']['default']['insights']['fiveFactorsScores']) > 0:
         user_data['doc_id'] = user.id
         user_list.append(user_data)
   except:
      continue

# Create dataframe
common_cols = ['doc_id', 'fullName', 'company_id', 'Cooperativeness', 'Creativity', 'Persistence', 'Sociability', 'Steadiness']
cols = common_cols + groups   # putting affinity groups (groups.txt) and commoncols (five factor) together
user_df = pd.DataFrame(0.0, index=range(len(user_list)), columns=cols)

user_df = user_df.astype({'doc_id' : 'str', 'fullName' : 'str', 'company_id' : 'str'})

# Add users to dataframe
for i in range(len(user_list)):
   # Ignore users that don't have an affinity group field
   try:      
      user_groups = user_list[i]['profiles']['default']['insights']['affinityGroups']
      user_df.loc[i, user_groups] = group_score
   except:
         continue

   doc_id = user_list[i]['doc_id']
   fullName = user_list[i]['profiles']['default']['fullName']
   # ignore users that aren't in any company
   try:
      company_id = user_list[i]['company']['id']
   except:
      continue
   
   fiveFactorDict = user_list[i]['profiles']['default']['insights']['fiveFactorsScores']
   
   Cooperativeness = fiveFactorDict['Cooperativeness']
   Creativity = fiveFactorDict['Creativity']
   Persistence = fiveFactorDict['Persistence']
   Sociability = fiveFactorDict['Sociability']
   Steadiness = fiveFactorDict['Steadiness']

   user_df.loc[i, common_cols] = (doc_id, fullName, company_id, Cooperativeness, Creativity, Persistence, Sociability, Steadiness)
     
# get rid of any users with no affinity group field
user_df = user_df[user_df['doc_id'] != '0.0']

user_df = user_df.reset_index(drop=True)


#user_df.to_csv("./data/firestore_users.csv", index=False)
user_df.to_csv("./firestore_users.csv", index=False)