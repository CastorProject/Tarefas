#! /usr/bin/env python3
import re
def remove_emojis(text):
    # Remove emojis and non-alphanumeric characters
    return re.sub(r'[^\w\s]', '', text).strip()