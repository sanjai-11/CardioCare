import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

# Load the heart disease dataset
data = pd.read_csv('heart_data.csv')
print(data.columns)
# Preprocess the data
# Convert categorical columns into numerical values (Label Encoding)
label_encoder = LabelEncoder()
data['Gender'] = label_encoder.fit_transform(data['Gender'])
data['cp'] = label_encoder.fit_transform(data['cp'])
data['restecg'] = label_encoder.fit_transform(data['restecg'])
data['slope'] = label_encoder.fit_transform(data['slope'])
data['thal'] = label_encoder.fit_transform(data['thal'])

# Handle missing values (if any)
data = data.fillna(data.mean())

# Define features and target variable
X = data[['age', 'Gender', 'cp', 'trestbps', 'Chol Level', 'FBS','restecg', 'Heart Rate', 'Exang', 'Oldpeak', 'CA', 'slope', 'thal']]
y = data['num']  # Target variable (1 for heart disease, 0 for no heart disease)

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# Save the model for future use in the web application
import joblib
joblib.dump(model, 'heart_disease_model.pkl')