# Keeper Recommendation Engine
The recommendation engine is currently a form that provides a recommendation of the top 5 users that are similar to the provided user. It currently uses the five factor scores of a user as well as the affinity groups they are in to rank similar profiles using cosine similarity.

## Starting the engine
1. Run `pip install -r ./config/requirements.txt` to import the necessary dependencies.
2. Create a folder named `data` and then run `firestore.py` to save a csv file of user data available from Firestore Database. This requires a Firebase API key in the config folder. Rename it to `keeper-hr-test-key.json`
3. Run `engine.py`. When the debugger PIN appears in the terminal, follow the link or go to `localhost:5000`

## Running the engine demo
1. Open `./data/firestore_users.xlsx` and record document IDs for some users. Enter one of the IDs in the form provided.
2. Press enter or click the "Get Recommendation" button. The results show the document IDs of the recommended users, their names, and the affinity groups that they have in common with the input user. 