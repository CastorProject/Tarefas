# Atividade 9 — Jogo das Emoções

A partida tem dez rodadas. Cinco são para a pessoa adivinhar a expressão do
CASTOR e cinco para o CASTOR reconhecer a expressão da pessoa. A ordem dos
turnos é embaralhada a cada partida. As emoções do jogo são alegria, tristeza,
raiva e surpresa. Cada participante tem um placar de até cinco estrelas.
No turno da pessoa, o CASTOR fala **Sua vez! Adivinhe qual é a minha emoção.**
O aviso toca uma vez ao iniciar cada turno, sem repetir ao recarregar a página.

No turno do CASTOR, a pessoa escolhe mentalmente uma expressão, olha para a
câmera e pressiona **Pronto! Pode adivinhar**. O reconhecimento aceita uma
expressão estável por um segundo, mostra o palpite e pergunta **Acertei?**.
A confirmação **Sim** soma uma estrela ao CASTOR; **Não** avança sem ponto.
Uma leitura sem rosto ou sem expressão válida permite tentar novamente,
sem avançar a rodada ou alterar a pontuação.

## Integração com o robô

O `face_recognition.py` existente continua sendo o único processo que controla
a HuskyLens por I2C. No início da partida, a atividade solicita
`setMultiAlgorithm([FACE, EMOTION])` e `setMultiAlgorithmRatio([1, 1])`, como no
teste `multi_test.py` disponível neste checkout. O modo multi permanece
carregado durante toda a partida, inclusive quando a pessoa está adivinhando.
Cada captura limpa o palpite anterior sem trocar ou recarregar os modelos.
Não é necessário iniciar
`multi.py`, `multi_test.py` ou `emotion_recognition.py` separadamente.

O pedido via `/activity9/request` contém `mode` (`emotion` ou `face`) e um
`token` exclusivo por partida, mais `capture_token` exclusivo por tentativa
(ou `null` quando não estiver capturando). O nó publica `/activity9/status`
com os mesmos tokens, estado, mensagem e emoção. A interface ignora respostas de tentativas
anteriores. O cadastro facial e a captura de emoções não usam a câmera
simultaneamente.

Ao finalizar a partida, sair ou navegar para outra página,
a interface solicita o retorno ao modo facial. O nó executa
`switchAlgorithm(FACE)` e recarrega o conhecimento facial de ID 1, utilizado
pelo cadastro existente. Se o navegador fechar ou o servidor desaparecer,
a autorização de uso do modo de emoções expira após 15 segundos sem pedidos.
Todas as telas da partida renovam essa autorização a cada segundo; as
transições internas entre turnos mantêm o multi ativo. Fechar a página
interrompe a renovação e aciona o retorno automático. Um palpite ou o tempo
limite de uma captura apenas pausa a leitura até a próxima tentativa.
Na inicialização, o nó aguarda cinco segundos após selecionar o modelo,
conforme a orientação do fabricante para a [HuskyLens 2](https://www.dfrobot.com/forum/topic/401208).
A troca de volta aguarda dez segundos para o modelo facial carregar antes de
recarregar os rostos; durante essa espera, a câmera já está voltando ao modo
facial.
A restauração também é tentada no encerramento normal do nó. Falhas de
restauração são registradas e o laço tenta novamente.

O reconhecimento utiliza os nomes enviados pelo modelo, normalizados em
português/inglês. Não presume uma tabela de IDs de emoções. Se a câmera
retornar outros nomes, ajuste `normalize_emotion` após conferir a saída real.

A explicação inicial, o aviso da vez da pessoa e o palpite são falados pelo Piper existente em
`castor_aac/src/piper_castor_tts.py`, usando seu cache de WAV e `aplay`.
O robô precisa manter o contêiner `castor-piper`, a voz e o diretório de cache
configurados como no reconhecimento facial. O primeiro uso de uma frase gera
o áudio em segundo plano. Entrar no jogo ou encerrar a atividade cancela a fala
da atividade que ainda estiver sendo reproduzida. Falhas de áudio são
registradas; as instruções continuam disponíveis na tela.

## Atualização no CASTOR

Atualize as pastas do projeto nos mesmos caminhos usados pelo robô:

- `web_interface/scripts/`: `web_interface_portuguese.py`, `activity9.py` e
  `activity9_voice.py`.
- `web_interface/scripts/templates/`: os três templates `Act9_1_emocoes.html`,
  `Act9_2_emocoes.html` e `Act9_3_emocoes.html`.
- `web_interface/scripts/static/`: `activity9.css` e `activity9.js`.
- `huskylens_2/scripts/castor_aac/src/`: `face_recognition.py` e
  `activity9_recognition.py`.

Reinicie a interface web e o nó facial que já é iniciado no CASTOR. Preserve
seu mecanismo de inicialização atual: não inicie um segundo nó de câmera.
Abra `/Activities/A9` para jogar.

## Validação

Com Flask disponível, execute a partir da raiz do repositório:

```sh
python -m unittest discover -s catkin_ws/src/web_interface/tests -v
```

Os testes usam uma câmera simulada e cobrem a partida completa, pontos dos
dois participantes, envios duplicados, comandos antigos, erros, cadastro
ocupado, perda de conexão e restauração do modo facial. A interface também
foi verificada no navegador em 1366 × 900 e 390 × 844, com captura simulada.

No robô, valide a leitura das quatro expressões, a reprodução da explicação
e do palpite e o retorno das saudações/cadastro facial após sair, terminar
uma partida ou fechar a página durante uma captura. Os testes locais usam uma câmera simulada. O script de validação na Raspi verifica também
a troca real de modelos e a restauração após falta de comunicação;
a identificação das quatro expressões e a qualidade audível da voz dependem
da conferência com uma pessoa diante do robô.
