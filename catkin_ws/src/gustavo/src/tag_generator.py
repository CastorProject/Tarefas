import cv2
import cv2.aruco as aruco
import numpy as np
import os

# Dicionário correspondente ao tag36h11
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_APRILTAG_36h11)

tamanho_px = 400
borda_px = 100     # margem branca ao redor

os.makedirs("assets/images", exist_ok=True)

for tag_id in range(35):
    marker_img = np.zeros((tamanho_px, tamanho_px), dtype=np.uint8)
    aruco.generateImageMarker(aruco_dict, tag_id+1, tamanho_px, marker_img, 1)

    # adiciona a margem branca em volta da tag
    marker_com_borda = cv2.copyMakeBorder(
        marker_img,
        borda_px, borda_px, borda_px, borda_px,
        cv2.BORDER_CONSTANT,
        value=255
    )

    cv2.imwrite(f"assets/images/tag36h11_id{tag_id+1}.png", marker_com_borda)

print("Tags geradas com sucesso em assets/images/")