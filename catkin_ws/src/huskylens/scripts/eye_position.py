import random
import time
import subprocess
import json
from huskylib import HuskyLensLibrary

huskylens = HuskyLensLibrary("I2C","", address=0x50)

def eye_tracking():
            while True:
                try:
                    block = huskylens.blocks()
                    id_husky = block.ID
                    x_husky, y_husky = block.x, block.y      
                    z=1 #flag para colocar os olhos do robo em modo de seguir o objeto
                    #Superior e Inferior
                    if (140 <= x_husky <= 180):
                        # Superior
                        if( 0 <= y_husky <= 100):                            
                            x = 0
                            y = 28  # 8 meio + 20 de abaixo
                            return x,y,z,str(id_husky) 
                        # Inferior
                        if (140 <= y_husky <= 240):
                            x=0
                            y=-20# -20 abaixo 
                            return x,y,z,str(id_husky)                        
                    #Lateral Direita (superior,meio,inferior)
                    if(180 <= x_husky <= 340):
                        # Lateral Superior Direita
                        if(0<=y_husky<=100):
                            x=14
                            y=28
                            return x,y,z,str(id_husky)                        
                        # Lateral Inferior Direita
                        if(140<=y_husky<=240):
                            x=14
                            y=-20
                            return x,y,z,str(id_husky)                        
                        #Lateral Meio Direita
                        else:
                            x=14
                            y=8
                            return x,y,z,str(id_husky)                      
                    #Lateral Esquerda (superior,meio,inferior)
                    if(0 <= x_husky <= 140):
                        # Lateral Superior Esquerda
                        if(0<=y_husky<=100):
                            x=-28
                            y=28
                            return x,y,z,str(id_husky)                       
                        # Lateral Inferior Direita
                        if(140<=y_husky<=240):
                            x=-28
                            y=-20       
                            return x,y,z,str(id_husky)                
                        #Lateral Meio Direita                     
                        else:
                            x=-28
                            y=8
                            return x,y,z,str(id_husky)                                  
                    else:
                        x=0
                        y=8
                        return x,y,z,str(id_husky)          
                except Exception as e:
                    #continue
                    x=0
                    y=0
                    z=0  #flag para colocar os olhos do robo em modo aleatorio
                    id_husky=0
                    return x, y, z, str(id_husky)              
                except KeyboardInterrupt:
                    print("\nQUITING")
                    break
                    quit()
