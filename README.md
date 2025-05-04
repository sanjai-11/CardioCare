# Heart Disease Management System

## 1. Raw Content
We used raw CSV files to simulate initial patient data for testing and populating the database.

Dataset link: [Heart Disease Dataset](https://www.kaggle.com/datasets/abdmental01/heart-disease-dataset)

This file includes sample rows for:
- Patient ID
- Age
- Gender
- Heart Rate
- Blood Pressure
- Cholesterol
- and more...

## 2. Database Structure
We used **SQLite** as our database.

The schema includes the following tables:

- **admin**: Stores admin credentials
- **doctor**: Stores doctor credentials
- **patient**: Stores patient details (linked to doctor_id)
- **heart_record**: Stores heart-related data (linked to patient_id)
- **risk_analysis**: Stores prediction results for each patient

The database is initialized via SQL scripts, and relationships are enforced using foreign keys. Data can also be imported/exported using **.csv** or **.json** format if needed.

## 3. Application Interface Code
The application was developed using:
- **Backend**: Python (Flask)
- **Frontend**: HTML, CSS, JavaScript (for interactive UI)

### File Structure:

- **`app.py`**: This is the main Python file that handles backend logic with Flask.
- **`/templates/`**: Contains HTML files used by Flask (rendered with Jinja2).
- **`/static/`**: This directory contains the static assets such as CSS and JavaScript files.
- **`/database/`**: The SQLite database file `health_records.db` which contains the various tables such as `admin`, `doctor`, `patient`, `heart_record`, and `risk_analysis`.
- **`train_model.py`**: Python script for training the machine learning model using the dataset.
- **`heart_disease_model.pkl`**: The saved model file (using `joblib`) that is used for predicting the risk score.

## 4. Interaction Logic
- Interactions with the database are done using Python’s `sqlite3` module.
- We use raw SQL queries within Python for:
  - `SELECT`, `INSERT`, `UPDATE`, `DELETE`
  - `JOIN`s for linking patients with heart records and analysis results.


