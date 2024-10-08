# -*- coding: utf-8 -*-
"""Untitled20.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1paDwd18OecjnWhztwTNec__Mi9DPTGVC
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from fpdf import FPDF
import streamlit as st
import os

import warnings
warnings.filterwarnings('ignore')

# Load and preprocess the data
data = pd.read_csv('dataset.csv')
description_data = pd.read_csv('symptom_Description.csv')
precaution_data = pd.read_csv('symptom_precaution.csv')

data.fillna('unknown', inplace=True)

# Lowercase, strip, and replace underscores for consistency
for col in data.columns[1:]:
    data[col] = data[col].str.lower().str.strip().str.replace('_', ' ')

# Preprocessing for disease and symptom encoding
encoded_data = data.copy()
label_encoder = LabelEncoder()
for col in encoded_data.columns:
    encoded_data[col] = label_encoder.fit_transform(encoded_data[col])

# Symptom columns identification
symptom_columns = data.columns[1:]

# Gather unique symptoms
unique_symptoms = pd.Series(data[symptom_columns].values.ravel()).dropna().unique()
symptom_to_number = {symptom: num for num, symptom in enumerate(unique_symptoms, start=101)}

for col in symptom_columns:
    data[col] = data[col].map(symptom_to_number).fillna(0).astype(int)

data['Disease'] = label_encoder.fit_transform(data['Disease'])

# Split the data
X = data[data.columns[1:]]
y = data['Disease']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# GridSearchCV for RandomForest parameter tuning
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'bootstrap': [True, False]
}

rf = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=5, n_jobs=-1, verbose=2)
grid_search.fit(X_train, y_train)

# Best parameters
best_params = grid_search.best_params_

# Train Random Forest with best params
best_rf_model = RandomForestClassifier(**best_params, random_state=42)
best_rf_model.fit(X_train, y_train)

# Confidence Score
def get_confidence_score(symptoms_encoded):
    proba = best_rf_model.predict_proba(symptoms_encoded)
    confidence_score = round(max(proba[0]) * 100, 2)
    return confidence_score

# PDF export
def export_to_pdf(symptoms, prediction, confidence_score, description, precaution):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Disease Prediction Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Symptoms: {symptoms}", ln=True)
    pdf.cell(200, 10, txt=f"Predicted Disease: {prediction}", ln=True)
    pdf.cell(200, 10, txt=f"Confidence Score: {confidence_score}%", ln=True)
    pdf.cell(200, 10, txt=f"Disease Description: {description}", ln=True)
    pdf.cell(200, 10, txt=f"Precaution: {precaution}", ln=True)

    pdf_output = "disease_prediction_report.pdf"
    pdf.output(pdf_output)
    return pdf_output

# Dictionaries for descriptions and precautions
disease_descriptions = dict(zip(description_data['Disease'].str.lower(), description_data['Description']))
disease_precautions = dict(zip(precaution_data['Disease'].str.lower(), precaution_data[['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']].apply(lambda x: ', '.join(x.fillna('')), axis=1)))

def get_disease_description(disease):
    return disease_descriptions.get(disease.lower(), "No description available.")

def get_disease_precaution(disease):
    return disease_precautions.get(disease.lower(), "No precaution available.")

# Disease prediction function
def predict_disease(symptoms_input):
    symptoms = symptoms_input.lower().split(",")
    symptoms = [symptom.strip() for symptom in symptoms]

    max_symptoms = 17
    symptoms = symptoms[:max_symptoms] + ["unknown"] * (max_symptoms - len(symptoms))

    symptoms_encoded = pd.DataFrame(0, index=[0], columns=X.columns)
    for i, symptom in enumerate(symptoms):
        if symptom in symptom_to_number:
            symptoms_encoded.iloc[0, i] = symptom_to_number[symptom]

    prediction = best_rf_model.predict(symptoms_encoded)[0]
    disease = label_encoder.inverse_transform([prediction])[0]

    confidence_score = get_confidence_score(symptoms_encoded)
    disease_description = get_disease_description(disease)
    disease_precaution = get_disease_precaution(disease)

    pdf_file = export_to_pdf(symptoms_input, disease, confidence_score, disease_description, disease_precaution)
    return disease, confidence_score, disease_description, disease_precaution, pdf_file

# Streamlit UI setup
st.title("Illness Intel: Disease Prediction System")
st.write("Enter your symptoms to predict the disease and get precautionary measures.")

symptoms_input = st.text_input("Enter symptoms (separated by commas)", "e.g., cough, fever, headache")

if st.button("Submit"):
    if symptoms_input:
        disease, confidence_score, description, precaution, pdf_file = predict_disease(symptoms_input)
        st.write(f"**Predicted Disease**: {disease}")
        st.write(f"**Confidence Score**: {confidence_score}%")
        st.write(f"**Disease Description**: {description}")
        st.write(f"**Precaution**: {precaution}")

        # Download the PDF file
        with open(pdf_file, "rb") as file:
            btn = st.download_button(
                label="Download Prediction Report",
                data=file,
                file_name="disease_prediction_report.pdf",
                mime="application/octet-stream"
            )

if st.button("Clear"):
    st.text_input("Enter symptoms (separated by commas)", "e.g., cough, fever, headache", key="clear_input")