#import libraries to access firestore database
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

import pandas as pd 
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.metrics.pairwise import cosine_similarity 

import pandas as pd

# Initialize connection to firebase
cred = credentials.Certificate("./config/keeper-hr-test-key.json")
firebase_admin.initialize_app(cred)
database = firestore.client()

#getting user profiles whose profiles are complete
users_query = database.collection("users").where(
    filter=FieldFilter("profiles.default.isComplete", "==", True)
)

users = users_query.stream()

user_list = []

#columns for data frame - softSkillsAnswers
categories = ["doc_id", "fullName", "company_id", "Role", "Birthday", "Curiosity","Hobby", "Happy Place", "Perception", "Power To Change", "Workplace"]

#appending users to list 
for user in users: 
    user_data = user.to_dict()

    #ignoring users who have missing fields in softSkillsAnswers
    try: 
       company_id = user_data['company'].get('id', None)
       if len(user_data['profiles']['default']['softSkillsAnswers']) >= 6 and company_id != None:
         user_data['doc_id'] = user.id
         user_list.append(user_data)


       user_data['doc_id'] = user.id
    except: 
       continue




#creating a dataframe 
user_df = pd.DataFrame(index=range(len(user_list)), columns=categories, dtype=object)

#user_df = user_df.astype({'doc_id' : 'str', 'fullName' : 'str', 'company_id' : 'str'})

#getting user data and putting it into df
for i in range(len(user_list)):
    doc_id = user_list[i]['doc_id']
    fullName = user_list[i]['profiles']['default']['fullName']

    try:
      company_id = user_list[i]['company']['id']
    except:
      continue

    #getting user roles & birthdays
    role = user_list[i]['profiles']['default'].get('myRole', None)

    birthday = user_list[i]['profiles']['default'].get('myBirthday', None)

  
    softSkillsAnswers = user_list[i]['profiles']['default']['softSkillsAnswers']
    
    #accessing each field in softSkillsAnswers - if the field is empty, replace value with None

    #creating seperate elements in each field (answer, content[image])
    curiosity_answer, curiosity_content = softSkillsAnswers.get('curiosity', {}).get('answer', None), softSkillsAnswers.get('curiosity', {}).get('content', None)
    hobby_answer, hobby_content = softSkillsAnswers.get('favorite_hobby', {}).get('answer', None), softSkillsAnswers.get('favorite_hobby', {}).get('content', None)
    happy_place_answer, happy_place_content = softSkillsAnswers.get('happy_place', {}).get('answer', None), softSkillsAnswers.get('happy_place', {}).get('content', None)
    perception_answer, perception_content =  softSkillsAnswers.get('perception', {}).get('answer', None), softSkillsAnswers.get('perception', {}).get('content', None)
    power_to_change_answer, power_to_change_content =  softSkillsAnswers.get('power_to_change', {}).get('answer', None), softSkillsAnswers.get('power_to_change', {}).get('content', None)
    workplace_answer, workplace_content = softSkillsAnswers.get('workplace', {}).get('answer', None), softSkillsAnswers.get('workplace', {}).get('content', None)

    #creating a tuple for each field (using answer, content)
    curiosity = (curiosity_answer, curiosity_content)
    hobby = (hobby_answer, hobby_content)
    happy_place = (happy_place_answer, happy_place_content)
    perception = (perception_answer, perception_content)
    power_to_change = (power_to_change_answer, power_to_change_content)
    workplace = (workplace_answer, workplace_content)

 
    #only inputting user data into df that is completely filled out
    if all(data is not None for data in curiosity) and all(data is not None for data in hobby) and all(data is not None for data in happy_place) and all(data is not None for data in perception) and all(data is not None for data in power_to_change) and all(data is not None for data in workplace):
      user_df.loc[i, categories] = (doc_id, fullName, company_id, role, birthday, curiosity, hobby, happy_place, perception, power_to_change, workplace)

#dropping nan rows
user_df = user_df.dropna()
user_df = user_df.reset_index(drop=True)


#converting to csv file
user_df.to_csv("./softSkillAnswers.csv")


# Load the soft skills answers CSV 
# users = pd.read_csv('./softSkillAnswers.csv') 
# Function to recommend profiles based on any soft skill answer (e.g., "curiosity") 

def get_rec_for_all_users(skill_column: str, users: pd.DataFrame) -> dict: 

  """
   Get recommendations for all users based on a specific soft skill column. 
   :param skill_column: The column name in the dataset corresponding to the soft skill (e.g., 'Curiosity'). 
   :param users: The pandas DataFrame containing user data and soft skill answers. 
   :return: A dictionary with user IDs as keys and recommended profiles as values. 
  """

   # Extract the answers and content (image link) for the selected soft skill 
  users[[f'{skill_column.lower()}_answer', f'{skill_column.lower()}_content']] = users[skill_column].str.strip("()").str.split(", '", n=1, expand=True) 

   # Get all skill answers for similarity comparison 
  score_rows = users[f'{skill_column.lower()}_answer'].tolist() 

   # Create a TF-IDF vectorizer and compute similarity scores for all users 
  vectorizer = TfidfVectorizer() 

  vector_matrix = vectorizer.fit_transform(score_rows) 
   # Dictionary to store recommendations for each user 
  recommendations = {} 
   # Iterate over each user 
  for idx, user_row in users.iterrows(): 

   # Get the vector for the current user 
    user_vec = vector_matrix[idx:idx + 1] 
    score_vectors = vector_matrix 
    # Compute cosine similarity between the current user and all others 
    cos_sim_scores = cosine_similarity(user_vec, score_vectors) 

    # Generate recommendations based on similarity scores 
    rec_profiles = [] 

  for rec_idx, score in sorted(enumerate(cos_sim_scores[0]), key=lambda x: x[1], reverse=True): 
       
    # Skip the current user 
    if rec_idx == idx: 
      continue 

    # Get profile details for the recommended user 
    profile_name = users.loc[rec_idx, 'fullName'] 
    skill_answer = users.loc[rec_idx, f'{skill_column.lower()}_answer'] 
    skill_content = users.loc[rec_idx, f'{skill_column.lower()}_content'] 
    rec_profiles.append({ "profile_name": profile_name, "skill_answer": skill_answer, "skill_content": skill_content, "similarity_score": score }) 

       # Limit to top 5 recommendations 
    if len(rec_profiles) == 5: 
      break 

    # Store recommendations for the current user 
    user_id = users.loc[idx, 'doc_id'] 
    recommendations[user_id] = rec_profiles 

    return recommendations 
    
    # Example usage: Get recommendations for all users based on the "Curiosity" soft skill recommendations = get_rec_for_all_users('Curiosity', users) 
    # # Print the recommendations for each user 

  for user_id, recs in recommendations.items(): 
    print(f"Recommendations for user {user_id}:") 
    
  for rec in recs: 
    print(f"- {rec['profile_name']} (Similarity: {rec['similarity_score']:.2f})") 
    print(f" Answer: {rec['skill_answer']}") 
    print(f" Content: {rec['skill_content']}\n")

