# -*- coding: utf-8 -*-
"""Gerador offline de respostas do Castor.

O LLM entra como AUTOR, nao como respondedor: roda agora, sem pressa, gera
variacoes ancoradas num banco existente, filtra automaticamente o que viola
as regras do projeto e deixa em respostas/pendentes/ para revisao humana.

Nada gerado aqui chega na crianca sem passar por voce.
Roda 100% local: nao usa internet, so o llama-server em 127.0.0.1.

    python3 gerar_respostas.py animais perguntas 20
    python3 gerar_respostas.py --todos
"""

import os
import re
import sys
import json

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, "..", "respostas")
PENDENTES = os.path.join(PASTA, "pendentes")
MAX_PALAVRAS = 18

CATEGORIAS = ["reacoes", "convites", "curiosidades", "perguntas"]

DESCRICAO = {
    "reacoes":      u"reacoes curtas de entusiasmo ao que a crianca acabou de contar",
    "convites":     u"convites para a crianca ENSINAR o Castor sobre o assunto",
    "curiosidades": u"fatos verdadeiros, simples e checaveis sobre o assunto",
    "perguntas":    u"perguntas abertas sobre a experiencia da crianca",
}

# Regras do projeto aplicadas automaticamente. O que casar aqui e descartado
# antes de chegar na revisao humana.
PROIBIDO = [
    (u"familia", r"\b(m[ãa]es?|pais?|papai|mam[ãa]e|av[óoô]s?|vov[óô]|"
                 r"irm[ãa]os?|irm[ãa]s?|fam[íi]lia)\b"),
    (u"amigos",  r"\b(amig[ao]s?|amiguinh[ao]s?|coleg[ao]s?|turma)\b"),
    (u"robo",    r"(sou um rob[ôo]|sou uma ia|sou um programa|rob[ôo] n[ãa]o|"
                 r"n[ãa]o tenho m[ãa]os|nunca fiz|sou um assistente)"),
    (u"escola",  r"\b(professor[ao]?|dever de casa)\b"),
    # SEGURANCA INFANTIL. Esta lista existe porque o modelo local gerou
    # "Ele gosta de fazer o amor?" num banco para criancas. Conteudo adulto
    # nunca chega nem a revisao humana.
    # Casamento por RADICAL, nao por forma exata: verbo em portugues conjuga
    # demais ("matar/matou/mataram"). Bloquear demais aqui custa barato -
    # so perde uma frase candidata. Deixar passar custa caro.
    (u"sexual",  r"\b(sex\w*|amor|beij(?!a-flor)\w*|namor\w*|transar|pelad\w*|"
                 r"casa(r|mento)|[íi]ntim\w*|nu[ao]s?)\b"),
    (u"violencia", r"\b(mat(ar|ou|a|am|ei|aram|ando)\w*|morr\w*|mort\w*|"
                   r"sangue|arma\w*|faca|tiro|machuc\w*|apanh\w*|"
                   r"brig\w*|guerra|bater em|bateu em)\b"),
    (u"substancia", r"\b(bebid\w*|[áa]lcool|cerveja|vinho|cigarro|fum\w*|"
                    r"drog\w*)\b"),
    (u"religiao", r"\b(deus|igreja|rez\w*|ora[çc][ãa]o|b[íi]blia|pecado|"
                  r"cren[çc]a)\b"),
    # Moldura de deficit: o robo nunca avalia ou compara a crianca.
    # Gerado pelo modelo local: "Voce e mais atento ou se sente menos atento?"
    (u"avaliacao", r"(n[ãa]o [ée] t[ãa]o|\b(mais|menos) (atent|segur|calm|"
                   r"espert|quiet|nervos|t[íi]mid|agitad|capaz|intelig)\w*)"),
    # Sondagem emocional: o robo acolhe emocao trazida pela crianca,
    # nunca inicia o assunto.
    (u"sondagem", r"\b(medo|saudade?s?|triste\w*|nervos\w*|ansios\w*|"
                  r"deprimi\w*|chor\w*|sofr\w*|solid[ãa]o|sozinh\w*|"
                  r"sua cabe[çc]a|se sente|sentindo)\b"),
    # Adjetivo com genero em qualquer posicao, nao so apos "voce e".
    (u"genero2", r"\b(nervos[oa]|cansad[oa]|content[e]|calm[oa]|quiet[oa]|"
                 r"agitad[oa]|t[íi]mid[oa]|atent[oa]|segur[oa]|acolhedor[a]?)\b"),
    # Nao-avaliacao de atributos identitarios: nenhuma frase pode julgar
    # arranjo familiar, genero, cor, origem ou religiao da crianca.
    (u"juizo",   r"(é errado|e errado|o certo é|o certo e|n[ãa]o pode ser|"
                 r"menin[oa] n[ãa]o|de menin[oa]|coisa de menin|"
                 r"normal [ée] )"),
    # Adjetivo com genero dirigido a crianca.
    (u"genero",  r"\bvoc[êe] (é|e) (bom|boa|lindo|linda|bonito|bonita|"
                 r"esperto|esperta|quieto|quieta)\b|\bsozinh[oa]\b|"
                 r"\bobrigad[oa]\b"),
]

REGRAS = (
    u"REGRAS OBRIGATORIAS:\n"
    u"- Nunca suponha que a crianca tem mae, pai, avo ou qualquer familiar.\n"
    u"- Nunca suponha que a crianca tem amigos ou gosta de estar com gente.\n"
    u"- Nunca suponha o arranjo familiar nem o genero da crianca.\n"
    u"- Nunca use adjetivo com genero para a crianca (nada de 'voce e bom',\n"
    u"  'sozinho', 'obrigado'). Use forma neutra: 'voce entende disso', 'so voce'.\n"
    u"- Nunca escreva frase que avalie familia, genero, cor, origem ou\n"
    u"  religiao como certo, errado, normal ou estranho.\n"
    u"- Fale na primeira pessoa, como o proprio Castor.\n"
    u"- Nunca invente fato falso. Se nao tiver certeza, nao escreva.\n"
    u"- No maximo 15 palavras por frase.\n"
    u"- Linguagem simples, concreta, sem ironia e sem metafora.\n"
    u"- Fique estritamente dentro do tema pedido, em tom leve e cotidiano.\n\n"
    u"Responda APENAS com as frases, uma por linha, sem numerar."
)


def endpoint():
    """Le a URL do llama-server direto do interaction.py, sem importar nada."""
    try:
        with open(os.path.join(AQUI, "interaction.py")) as f:
            m = re.search(r"https?://[\w\.:]+/[\w/\.]*completions", f.read())
            if m:
                return m.group(0)
    except Exception:
        pass
    return "http://127.0.0.1:8080/v1/chat/completions"


def perguntar_ao_llm(prompt, n_tokens=700):
    """Fala com o servidor de geracao.

    Por padrao usa o llama-server da propria Rasp. Definindo as variaveis
    de ambiente, usa uma maquina mais forte na rede local, que e o modo
    recomendado: aqui a lentidao nao importa, ninguem esta esperando.

        CASTOR_GERADOR_URL=http://10.0.0.18:11434/v1/chat/completions
        CASTOR_GERADOR_MODELO=llama3.2:3b
    """
    url = os.environ.get("CASTOR_GERADOR_URL") or endpoint()
    corpo = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "top_p": 0.95,
        "max_tokens": n_tokens,
    }
    modelo = os.environ.get("CASTOR_GERADOR_MODELO")
    if modelo:
        corpo["model"] = modelo      # o Ollama exige, o llama-server ignora
    payload = json.dumps(corpo).encode("utf-8")
    req = Request(url, data=payload,
                  headers={"Content-Type": "application/json"})
    bruto = urlopen(req, timeout=900).read().decode("utf-8")
    return json.loads(bruto)["choices"][0]["message"]["content"]


def montar_prompt(contexto, categoria, exemplos, quantidade):
    return (
        u"Escreva %d frases novas em portugues do Brasil para um robo social\n"
        u"que conversa com criancas autistas de 6 a 12 anos sobre '%s'.\n\n"
        u"Tipo de frase: %s\n\n"
        u"Exemplos do estilo desejado:\n%s\n\n%s"
        % (quantidade, contexto, DESCRICAO[categoria],
           u"\n".join(u"- " + e for e in exemplos[:6]), REGRAS)
    )


def filtrar(linhas, ja_existem):
    aprovadas, recusadas = [], []
    vistas = set(ja_existem)
    for linha in linhas:
        frase = linha.strip().lstrip(u"-*0123456789. ").strip()
        if not frase or len(frase) < 8:
            continue
        if frase in vistas:
            recusadas.append((u"repetida", frase)); continue
        if len(frase.split()) > MAX_PALAVRAS:
            recusadas.append((u"longa", frase)); continue
        motivo = None
        baixa = frase.lower()
        if re.search(r"(nao |n\xe3o )?posso (cumprir|atender|ajudar)|desculp\w*, (mas )?nao|lamento, mas", baixa):
            recusadas.append((u"recusa_modelo", frase)); continue
        for nome, padrao in PROIBIDO:
            if re.search(padrao, baixa):
                motivo = nome; break
        if motivo:
            recusadas.append((motivo, frase)); continue
        vistas.add(frase)
        aprovadas.append(frase)
    return aprovadas, recusadas


# Registros criticos nao sao gerados por modelo, em hipotese alguma.
# Emocao, identidade e sofrimento sao escritos a mao e revisados por quem
# entende de clinica. O experimento com "amizade" mostrou o porque.
CONTEXTOS_PROIBIDOS = ["amizade", "afeto", "sentimento", "sentimentos",
                       "emocao", "emocoes", "psicologa", "sofrimento",
                       "familia", "identidade", "genero",
                       "autismo", "conversa", "sobre_castor"]


def gerar(contexto, categoria, quantidade):
    if contexto.lower() in CONTEXTOS_PROIBIDOS:
        print("  RECUSADO: '%s' e registro critico." % contexto)
        print("  Esse conteudo e escrito a mao, com revisao clinica.")
        return None

    origem = os.path.join(PASTA, contexto + ".json")
    if not os.path.exists(origem):
        print("  banco nao existe: %s" % contexto); return None
    with open(origem) as f:
        banco = json.load(f)

    print("  gerando %s/%s ..." % (contexto, categoria))
    try:
        bruto = perguntar_ao_llm(montar_prompt(
            contexto, categoria, banco.get(categoria, []), quantidade))
    except Exception as e:
        print("  ERRO ao falar com o llama-server: %s" % e)
        return None

    aprovadas, recusadas = filtrar(bruto.split("\n"), banco.get(categoria, []))
    print("  %d aprovadas, %d recusadas" % (len(aprovadas), len(recusadas)))
    for motivo, frase in recusadas:
        print("    [%s] %s" % (motivo, frase[:60]))
    return aprovadas


def main():
    if not os.path.isdir(PENDENTES):
        os.makedirs(PENDENTES)

    args = sys.argv[1:]
    if not args:
        print(__doc__); return

    if args[0] == "--todos":
        contextos = [a[:-5] for a in sorted(os.listdir(PASTA))
                     if a.endswith(".json") and a != "persona.json"]
        categorias, quantidade = CATEGORIAS, 15
    else:
        contextos = [args[0]]
        categorias = [args[1]] if len(args) > 1 else CATEGORIAS
        quantidade = int(args[2]) if len(args) > 2 else 15

    for contexto in contextos:
        saida, total = {}, 0
        for categoria in categorias:
            novas = gerar(contexto, categoria, quantidade)
            if novas:
                saida[categoria] = novas
                total += len(novas)
        if saida:
            destino = os.path.join(PENDENTES, contexto + ".json")
            with open(destino, "w") as f:
                f.write(json.dumps(saida, ensure_ascii=False, indent=2))
            print(">> %s: %d frases aguardando aprovacao\n" % (destino, total))


if __name__ == "__main__":
    main()
