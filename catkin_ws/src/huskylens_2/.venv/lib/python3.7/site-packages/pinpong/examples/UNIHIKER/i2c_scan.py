import time
from pinpong.board import Board,I2C

Board("UNIHIKER").begin()
i2c = I2C(4)

l=i2c.scan()
print("i2c list:",l)

while(1):
	time.sleep(1)
    
