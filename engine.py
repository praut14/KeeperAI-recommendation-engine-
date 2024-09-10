from flask import Flask, render_template, request, jsonify
import pandas as pd

from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

# How many users will be recommended
REC_LIST_LEN = 5

app = Flask(__name__, template_folder='templates')
CORS(app)

# Generate this sheet by running firestore.py
#users = pd.read_csv('./data/firestore_users.csv')
users = pd.read_csv('./firestore_users.csv')

# List of affinity groups
groups = []
with open("./config/groups.txt") as file:
    for line in file:
        groups.append(line.strip())


@app.route('/')
def show_version():
    return render_template('recommendation.html')


# Profile Recommendation
@app.route('/ProfRec', methods=['POST']) 
def ProfileRecommender_CS():
    # Format doc_id input
    doc_id = request.form.get('doc_id').strip()
    if doc_id == '':
        return jsonify(["Please enter a valid document ID"])

    # Get the list of recommended users usinf cosine similarity 
    similarities = get_rec(doc_id)
    if similarities == [-1]:
        return jsonify(["Please enter a valid document ID"])
    
    output_scores=[]

    # Format results for frontend demo
    for s in similarities:
        s_name = users[users['doc_id'] == s[0]]['fullName'].iloc[0]
        output_scores.append(f"{s[0]} {s_name}: {s[1]}") # docid, fullname and similar profile affinity groups
     
    return jsonify(output_scores)
    
    
def get_rec(doc_id: str) -> list:
    """Returns a list of profile recommendations

    Args:
        doc_id (string): Firestore Database document ID of the user to generate recommendations for

    Returns:
        list: 
        The first value of each row is the document ID of the recommended user, or a negative number on error. 
        The second value is a list of shared affinity groups
        [doc_id, [affinity group 1, affinity group 2]]
    """
        
    # Get index of row with matching doc_id
    try:
        idx = users.index[users['doc_id'] == doc_id].astype(int)[0]
    except:
        return [-1]
    
    # Filter dataframe to users in the same company and get new index for target user
    company_users = users[users['company_id'] == users.loc[idx]['company_id']]
    company_users = company_users.reset_index()
    company_idx = company_users.index[company_users['doc_id'] == doc_id].astype(int)[0]
        
    # Extract relevant columns from the dataframe for cosine similarity calculation
    labels = ['Cooperativeness', 'Creativity', 'Persistence', 'Sociability', 'Steadiness'] + groups
    user_row = company_users.loc[company_idx, labels]
    score_rows = company_users.loc[:, labels]

    # Convert the selected columns to a numpy array
    user_vec = [user_row.to_numpy()]
    score_vectors = score_rows.to_numpy()

    # Calculate cosine similarity of scores (how similar are the directions of the vectors?)
    cos_sim_scores = cosine_similarity(user_vec, score_vectors)

    # Obtain and format relevant information about users with the highest similarity scores
    rec_profiles = []
    for rec_idx, _ in sorted(enumerate(cos_sim_scores[0]), key=lambda x: x[1], reverse=True):
        if rec_idx != company_idx:
            profile_id = company_users.loc[rec_idx,  'doc_id']

            # Affinity groups that target user and recommended user have in common
            common_groups = []
            for group in groups:
                if score_rows.loc[company_idx, group] and score_rows.loc[rec_idx, group]:
                    common_groups.append(group)
                    
            rec_profiles.append([profile_id, common_groups])

        # Only top 5 similar users
        if len(rec_profiles) == min(5, len(company_users)-1):
            return rec_profiles
        
    return rec_profiles

if __name__ == '__main__':
    app.run(debug=True)