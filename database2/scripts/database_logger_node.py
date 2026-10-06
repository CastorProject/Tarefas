#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import pandas as pd
import json
import os
import unicodedata
import re
from datetime import datetime
from geometry_msgs.msg import Point
from std_msgs.msg import String

class DatabaseLoggerNode(object):
    def __init__(self):
        rospy.init_node('database_logger_node', disable_signals=True)
        
        # --- TRAVAS DE ESTADO ---
        self.gravando = False
        self.solicitou_salvamento = False  # Avisa ao terminal que a web pediu pra parar
        # ------------------------

        self.tempo_inicio_sessao = rospy.get_time()
        self.current_id = "Desconhecido"
        
        self.lista_eventos = []
        self.lista_metricas = []
        self.pasta_destino = '/home/pi/catkin_ws/src/database/scripts/data'
        
        self.shutdown_executado = False
        
        # Escuta os comandos da interface web
        rospy.Subscriber('/record_data', String, self.callback_record)

        # Escuta os sensores
        rospy.Subscriber('/moveEyes', Point, self.callback_olhos)
        rospy.Subscriber('/persona', String, self.callback_persona)
        rospy.Subscriber('/motor_pescoco', String, self.callback_pescoco)
        rospy.Subscriber('/emotions', String, self.callback_emocoes)
        rospy.Subscriber('/speaker', String, self.callback_speaker)
        rospy.Subscriber('/mic', String, self.callback_mic)
        rospy.Subscriber('/movements', String, self.callback_movements)
        rospy.Subscriber('/sensor_prox_laser', String, self.callback_laser)

        rospy.loginfo("🟡 SISTEMA EM STANDBY: Aguardando o primeiro clique da terapeuta...")
        rospy.loginfo("👉 Para salvar a sessão, clique em 'Menu' na interface ou pressione [Ctrl+C].")

    def callback_record(self, msg):
        if msg.data == "iniciar" and not self.gravando:
            self.gravando = True
            self.tempo_inicio_sessao = rospy.get_time()
            rospy.loginfo("🟢 GRAVAÇÃO INICIADA! Marco Zero estabelecido.")
            
        elif msg.data == "parar" and self.gravando:
            self.gravando = False
            self.solicitou_salvamento = True  # Dispara a pergunta no terminal
            rospy.loginfo("⏸️ GRAVAÇÃO PAUSADA VIA WEB.")

    def registrar_evento(self, categoria, comando):
        if not self.gravando:
            return
            
        tempo_decorrido = rospy.get_time() - self.tempo_inicio_sessao
        self.lista_eventos.append({
            'start_time_sec': round(tempo_decorrido, 3),
            'categoria': categoria,
            'label': comando
        })

    def callback_laser(self, msg):
        if not self.gravando:
            return
            
        tempo_decorrido = rospy.get_time() - self.tempo_inicio_sessao
        try:
            distancia_mm = float(msg.data)
        except ValueError:
            rospy.logwarn("⚠️ Leitura corrompida recebida no sensor laser. Pulando frame.")
            return
            
        self.lista_metricas.append({
            'time_sec': round(tempo_decorrido, 3),
            'min_person_to_castor_px': distancia_mm,
            'id_persona': self.current_id,
            'x': 0.0, 'y': 0.0, 'z': 0.0
        })

    def callback_olhos(self, msg):
        pass

    def callback_persona(self, msg):
        self.current_id = msg.data

    def callback_pescoco(self, msg):
        self.registrar_evento('Pescoco', f"Posicao_{msg.data}")

    def callback_emocoes(self, msg):
        self.registrar_evento('Emocao', msg.data)

    def callback_speaker(self, msg):
        self.registrar_evento('Atividade_Audio', msg.data)

    def callback_mic(self, msg):
        self.registrar_evento('Controle_Mic', msg.data)

    def callback_movements(self, msg):
        self.registrar_evento('Movimento_Web', msg.data)

    def _sanitizar_nome(self, nome_bruto: str) -> str:
        string_normalizada = unicodedata.normalize('NFD', nome_bruto.strip())
        nome_limpo = "".join(c for c in string_normalizada if unicodedata.category(c) != 'Mn')
        nome_limpo = nome_limpo.replace(" ", "_").replace("ç", "c").replace("Ç", "C")
        nome_limpo = re.sub(r'[^A-Za-z0-9_]', '', nome_limpo)
        return nome_limpo

    def processar_desligamento(self):
        if self.shutdown_executado:
            return
        self.shutdown_executado = True
        
        duracao_final = rospy.get_time() - self.tempo_inicio_sessao
        
        print("\n" + "="*60)
        print("🛑 FIM DE SESSÃO DETECTADO (Botão Menu ou Ctrl+C)")
        print(f"⏱️ Tempo total de atividade gravada: {duracao_final:.1f} segundos")
        print("="*60)
        
        escolha = input("Deseja SALVAR a tríade de arquivos desta sessão? (s/n): ").strip().lower()
        
        if escolha == 's':
            nome_entrada = input("Digite o nome do paciente: ")
            nome_sanitizado = self._sanitizar_nome(nome_entrada)
            
            if not nome_sanitizado:
                nome_sanitizado = "Paciente_Anonimo"
                
            self._gerar_arquivos_exportacao(nome_sanitizado, duracao_final)
        else:
            print("🗑️ Memória RAM liberada. Dados clínicos descartados com sucesso.")

        # --- AUTO-RESET ---
        # Limpa as listas para a próxima criança e volta para o modo standby
        self.lista_eventos.clear()
        self.lista_metricas.clear()
        self.shutdown_executado = False
        self.solicitou_salvamento = False
        print("\n🟡 SISTEMA EM STANDBY: Pronto para uma nova sessão.\n")

    def _gerar_arquivos_exportacao(self, nome_paciente, duracao_final):
        os.makedirs(self.pasta_destino, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sufixo = f"_{nome_paciente}_{timestamp}"
        
        caminho_json = os.path.join(self.pasta_destino, f"session_summary{sufixo}.json")
        resumo = {
            "version": "1.0",
            "session_label": nome_paciente,
            "duration_sec": duracao_final,
            "metadata": {
                "id_crianca": nome_paciente,
                "data": datetime.now().strftime("%d/%m/%Y"),
                "tempo_total_s": duracao_final
            }
        }
        
        try:
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(resumo, f, indent=4, ensure_ascii=False)
        except Exception as e:
            rospy.logerr(f"Falha ao gravar metadados: {e}")

        if self.lista_metricas:
            caminho_metricas = os.path.join(self.pasta_destino, f"frames_metrics{sufixo}.csv")
            try:
                pd.DataFrame(self.lista_metricas).to_csv(caminho_metricas, index=False, encoding='utf-8')
            except Exception as e:
                rospy.logerr(f"Erro ao gerar CSV de métricas: {e}")

        if self.lista_eventos:
            caminho_eventos = os.path.join(self.pasta_destino, f"interaction_events{sufixo}.csv")
            try:
                pd.DataFrame(self.lista_eventos).to_csv(caminho_eventos, index=False, encoding='utf-8')
            except Exception as e:
                rospy.logerr(f"Erro ao gerar CSV de eventos: {e}")
                
        print(f"✅ Arquivos salvos com sucesso na pasta data/ (Sufixo: {sufixo})")


# ARQUITETURA PRINCIPAL
if __name__ == '__main__':
    node = DatabaseLoggerNode()
    try:
        rate = rospy.Rate(10) # Roda 10 vezes por segundo
        while not rospy.is_shutdown():
            # Fica vigiando se a interface web pediu para salvar os dados
            if node.solicitou_salvamento:
                node.processar_desligamento()
            rate.sleep()
    except KeyboardInterrupt:
        # Se alguém apertar Ctrl+C, também salva antes de fechar de vez
        pass
    finally:
        node.processar_desligamento()