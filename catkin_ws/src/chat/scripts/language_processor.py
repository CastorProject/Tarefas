#!/usr/bin/python3
import json
import numpy
from numpy import max
import random
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

data_path = '/home/pi/catkin_ws/src/chat/scripts/es_data.json'

# Función para cargar los datos desde un archivo JSON
def load_intents_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Función para preprocesar texto
def preprocess_text(text):
    # Agregando lematización, manejo de sinónimos, etc.
    text = text.lower()
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

data = load_intents_from_json(data_path)

# Preparar los datos de entrenamiento
intents = [{'tag': tag, 'patterns': keywords, 'response': [text]}
           for tag, keywords in data['INTENT_KEYWORDS'].items()
           for tag_resp, text in data['RESPONSES'].items() if tag == tag_resp]


# Función para clasificar la intención y obtener la respuesta
def classify_intent(text, threshold=0.007): #INPORTANTE DEFINE QUE PASA O QUE NO
    preprocessed_text = preprocess_text(text)
    probabilities = model.predict_proba([preprocessed_text])[0]
    max_prob = max(probabilities)
    predicted_tag = model.classes_[probabilities.argmax()]

    if max_prob >= threshold:
        return predicted_tag
    else:
        return None  # Retorna None si la confianza es baja

def get_dynamic_response(intent_tag):
    responses = next((intent['response'] for intent in intents if intent['tag'] == intent_tag), None)
    if responses:
        return random.choice(responses)  # Selecciona una respuesta al azar si hay varias opciones
    return None                           # Si no hay match retorna None, se pueden agregar cosas como "no entendi"

model = Pipeline([
    ('vectorizer', TfidfVectorizer()),
    ('classifier', MultinomialNB())
])

# Entrenar el modelo
X_train = [' '.join(preprocess_text(pattern) for pattern in intent['patterns']) for intent in intents]
y_train = [intent['tag'] for intent in intents]
model.fit(X_train, y_train)

# Loop principal de conversación
def output(text_input):
    text_input = text_input.strip()
    if not text_input:
        return None, None

    predicted_intent = classify_intent(text_input)
    response = get_dynamic_response(predicted_intent)
    return predicted_intent, response

# while True:
    # entrada = input("di algo: ")
    # inten, response = output(entrada)
    # print(f"{inten}, {response}")
