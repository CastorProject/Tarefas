#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from utils import remove_emojis
from flask import request

def get_activities():
    activities_html = {
        "Atividade 1 - A batalha 👮‍♂️": "Activities/A1",
        "Atividade 2 - Histórias de José 👦": "Activities/A2",
        "Atividade 3 - Dança 💃": "Activities/A3",
        "Atividade 4 - Cantar 🎵": "Activities/A4",
        "Atividade 5 - Histórias narrativas 📢": "Activities/A5",
        "Atividade 6 - Conversação 🤪": "Activities/A6",
        "Atividade 7 - Abraços 💕": "Activities/A7"
    }
    # Preprocess activities_html keys
    activities_html_processed = {remove_emojis(key): value for key, value in activities_html.items()}
    #print(f"Activities processed: {activities_html_processed}")
    
    selected_items = request.json.get('selected_items', []) if request.json else []
    #print(f"Received selected items: {selected_items}")  # Debugging line
    activities_paths = []
    
    for item in selected_items:
        # Remove emojis from item
        trimmed_item = remove_emojis(item)
        #print(f"Trimmed item: {trimmed_item}")
        
        # Verificar si el texto limpio contiene la clave procesada en activities_html
        matched_key = next((key for key in activities_html_processed if key in trimmed_item), None)
        
        if (matched_key):
            file_path = activities_html_processed[matched_key]
            #print(f"Processing item: {trimmed_item}, file_path: {file_path}")  # Línea de depuración
            activities_paths.append(file_path)

        #else:
            #print(f"Item not found in activities_html: {trimmed_item}")  # Debugging line
       
    #print(f"Activities content: {activities_paths}")  # Debugging line
    return activities_paths