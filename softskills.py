import pandas as pd
from datetime import datetime

# Load your dataset
#file_path = 'your_dataset.csv'  # Replace with the path to your CSV
data = pd.read_csv('softSkillAnswers.csv')

# Remove unnecessary columns
data_cleaned = data.drop(columns=['Unnamed: 0'])

# Function to extract text from tuple-like strings
def extract_text(data_column):
    return data_column.str.extract(r"\('(.*?)',")[0]

# Function to extract URLs from tuple-like strings
def extract_url(data_column):
    return data_column.str.extract(r"',\s*'(.*?)'\)")[0]

# Apply the extraction to relevant columns
for column in ['Curiosity', 'Hobby', 'Happy Place', 'Perception', 'Power To Change', 'Workplace']:
    data_cleaned[column + '_Text'] = extract_text(data_cleaned[column])
    data_cleaned[column + '_URL'] = extract_url(data_cleaned[column])
    data_cleaned.drop(columns=[column], inplace=True)

# Remove rows with invalid Birthday entries
data_cleaned = data_cleaned[data_cleaned['Birthday'] != 'Month/Day']

# Convert valid Birthday entries to Age
current_year = datetime.now().year
data_cleaned['Age'] = current_year - pd.to_datetime(data_cleaned['Birthday']).dt.year

# Drop the original Birthday column
data_cleaned.drop(columns=['Birthday'], inplace=True)

# Save the cleaned dataset
data_cleaned.to_csv('cleaned_dataset.csv', index=False)

print("Dataset cleaned and saved as 'cleaned_dataset.csv'.")
