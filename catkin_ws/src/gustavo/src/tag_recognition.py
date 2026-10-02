import sys
import time

sys.path.append("/home/pi/catkin_ws/src/huskylens_2/scripts/DFRobot_HuskylensV2/python/smbus2/")
from dfrobot_huskylensv2 import *

ALGORITHM = ALGORITHM_TAG_RECOGNITION

# Estrutura por categoria: cada uma pode reusar os mesmos IDs (1, 2, 3...)
categorias = {
    "1": {
        "nome": "Time de Futebol",
        "itens": {
            1: "Rio Branco",
            2: "Brancão",
        }
    },
    "2": {
        "nome": "Frutas",
        "itens": {
            1: "Maçã",
            2: "Banana",
        }
    },
}


def selecionar_categoria():
    print("\n=== Selecione a categoria ===")
    for chave, dados in categorias.items():
        print(f"{chave} - {dados['nome']}")

    while True:
        escolha = input("Digite o numero da categoria: ").strip()
        if escolha in categorias:
            return categorias[escolha]
        print("Opcao invalida, tente novamente.")


def main():
    categoria_escolhida = selecionar_categoria()
    print(f"\nCategoria selecionada: {categoria_escolhida['nome']}")
    print("Iniciando leitura de tags...\n")

    huskylens = HuskylensV2_I2C()
    huskylens.knock()
    huskylens.switchAlgorithm(ALGORITHM)

    itens = categoria_escolhida["itens"]
    last_tag_id = None

    while True:
        huskylens.getResult(ALGORITHM)

        if huskylens.available(ALGORITHM):
            result = huskylens.getCachedCenterResult(ALGORITHM)

            if result is not None:
                tag_id = result.ID

                if tag_id != last_tag_id:
                    nome = itens.get(tag_id, f"ID {tag_id} nao mapeado nesta categoria")
                    print(f"[{categoria_escolhida['nome']}] {nome}")
                    last_tag_id = tag_id
        else:
            last_tag_id = None

        time.sleep(0.05)


if __name__ == "__main__":
    main()