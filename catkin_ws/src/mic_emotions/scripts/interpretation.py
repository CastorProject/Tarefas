def solve_emotion(raw_emotion_scores):
    all_emotions = {'fear':             0,
                    'anger':            0,
                    'anticipation':     0,
                    'trust':            0,
                    'surprise':         0,
                    'positive':         0,
                    'negative':         0,
                    'sadness':          0,
                    'disgust':          0,
                    'joy':              0}
    for clave in raw_emotion_scores.keys():
        all_emotions[clave] = raw_emotion_scores[clave]

    highFreq_Arr=list(set(list(all_emotions.values())))[-2:]    #pos 1 = max, pos 0 = max_1
    count_max = 0
    count_max_1 = 0
    if len(highFreq_Arr) == 1:
        return('neutre')
    else:
        for clave, valor in all_emotions.items():
            if (valor == highFreq_Arr[1]) and (clave != 'positive') and (clave != 'negative'):
                count_max = count_max + 1
        
        if count_max == 0:
            for clave, valor in all_emotions.items():
                if (valor == highFreq_Arr[0]) and (clave != 'positive') and (clave != 'negative'):
                    count_max_1 = count_max_1 + 1
                
        if count_max == 1:
            for clave, valor in all_emotions.items():
                if (valor == highFreq_Arr[1]) and (clave != 'positive') and (clave != 'negative'):
                    return (clave)
                    
        elif count_max_1 == 1:
            for clave, valor in all_emotions.items():
                if (valor == highFreq_Arr[0]) and (clave != 'positive') and (clave != 'negative'):
                    return (clave)
        else:
            if all_emotions.get('positive') > all_emotions.get('negative'):
                return ('positive')
            elif all_emotions.get('positive') < all_emotions.get('negative'):
                return ('negative')
            else:
                return ('neutre') # no existe
