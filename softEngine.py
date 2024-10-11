from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import numpy as np

from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity 

# How many users will be recommended
REC_LIST_LEN = 5

app = Flask(__name__, template_folder='templates')
CORS(app)


#accessing soft skills csv
users = pd.read_csv('./softSkillAnswers.csv')

def remove_quotes(data):
    return data.replace("'", "")


@app.route('/')
def show_version():
    return render_template('softSkills.html')


# Profile Recommendation
@app.route('/SoftSkillRec', methods=['POST']) 
def SoftSkillRecommender_CS():
    # Format doc_id input
    doc_id = request.form.get('doc_id').strip()

    if doc_id == '':
        return jsonify(["Please enter a valid document ID"])
    
    #Format softSkillAnswer input
    softSkillAnswer = request.form.get('softSkillAnswer').strip()

    # Get the list of recommended users
    similarities = get_rec(doc_id, softSkillAnswer, users)

    if similarities == [-1]:
        return jsonify(["Please enter a valid document ID"])
    
    output_scores=[]

    # Format results for frontend demo
    for s in similarities:

        # append user names & softSkillAnswers
        #output_scores.append(f"Full Name: {s[0]}  Similarity Score: {s[1]}  \nAnswer: {s[2]} \nContent: {s[3]}")
        output_scores.append(s)
     
    return jsonify(output_scores)
    
# access doc_id, softSkillAnswer column, and user dataframe
def get_rec(doc_id: str, softSkillAnswer: str, users: pd.DataFrame) -> list:
    
    #creating two new columns for the soft Skill Column (answer + content)
    users[[softSkillAnswer + "_Answer", softSkillAnswer + "_Content"]] = users[softSkillAnswer].str.strip("()").str.split(", '", n=1, expand=True)


    users[softSkillAnswer + "_Answer"] = users[softSkillAnswer + "_Answer"].apply(lambda x: x.replace("'", ""))
    users[softSkillAnswer + "_Content"] = users[softSkillAnswer + "_Content"].apply(lambda x: x.replace("'", ""))

    # Get index of row with matching doc_id
    try:
        idx = users.index[users['doc_id'] == doc_id].astype(int)[0]
    except:
        return [-1]
    
    # change df to only contain user profiles of the same company
    users = users[users['company_id'] == users.loc[idx]['company_id']]
    users = users.reset_index()
    company_idx = users.index[users['doc_id'] == doc_id].astype(int)[0]
    
   

    # Extract relevant columns from the dataframe for cosine similarity calculation
    label = [softSkillAnswer + "_Answer"] 

    # access user_row as a single string
    user_row = users.loc[company_idx, label].values[0]

    # access score_rows as a list of strings
    score_rows = users.loc[:, label].values.flatten().tolist()
    

    # Combine both rows into one vector matrix for cosine similarity calculation
    vectorizer = TfidfVectorizer()
    vector_matrix = vectorizer.fit_transform([user_row] + score_rows)

    # access first vector
    user_vec = vector_matrix[0:1]

    # rest of vectors in the matrix
    score_vectors = vector_matrix[1:]

    # Calculate cosine similarity of scores (how similar are the directions of the vectors?)
    cos_sim_scores = cosine_similarity(user_vec, score_vectors)

    # Obtain and format relevant information about users with the highest similarity scores
    rec_profiles = []
    
    
    for rec_idx, score in sorted(enumerate(cos_sim_scores[0]), key=lambda x: x[1], reverse=True):

        # access each profile's name and softSkillAnswer
        if rec_idx != company_idx:
            profile_name = users.loc[rec_idx,  'fullName']
            similarity_score = round(score, 2)
            softSkill_answer = users.loc[rec_idx, softSkillAnswer + "_Answer"]
            softSkill_content = users.loc[rec_idx, softSkillAnswer + "_Content"]

                    
            rec_profiles.append([profile_name, similarity_score, softSkill_answer, softSkill_content])

        # Only top 5 similar users will be returned
        if len(rec_profiles) == min(5, len(users)-1):
            return rec_profiles
        
    return rec_profiles

if __name__ == '__main__':
    app.run(debug=True)