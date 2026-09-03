import apertium
def pt_en(texto):
    return(apertium.translate('es','en', apertium.translate('pt', 'es', texto)))
def es_en(texto):
    return(apertium.translate('es','en', texto))
