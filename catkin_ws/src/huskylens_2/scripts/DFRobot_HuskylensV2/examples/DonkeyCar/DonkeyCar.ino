/***************************************************
 HUSKYLENS V2 An Easy-to-use AI Machine Vision Sensor
 <https://www.dfrobot.com/product-1922.html>

 This example demonstrates the face recognition functionality of HUSKYLENS V2
 via I2C interface. It shows how to initialize the sensor, detect human faces,
 and print detailed information including face ID, center coordinates,
 dimensions, name, content, and the positions of facial features (left eye,
 right eye, nose, left mouth, right mouth) using a helper macro for consistent
 output.
 ***************************************************
 Created 2025-07-04
 By [Ouki Wang](ouki.wang@dfrobot.com)

 GNU Lesser General Public License.
 See <http://www.gnu.org/licenses/> for details.
 All above must be included in any redistribution
 ****************************************************/

/***********Notice and Trouble shooting***************
 1.Connection and Diagram can be found here
 <https://wiki.dfrobot.com/HUSKYLENS_V1.0_SKU_SEN0305_SEN0336#target_23>
 2.This code is tested on Arduino Uno, Leonardo, Mega, Microbit,ESP8266,ESP32
 boards.
 ****************************************************/

#include "DFRobot_HuskylensV2.h"

// HUSKYLENS green line >> SDA/TX; blue line >> SCL/RX
HuskylensV2 huskylens;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  while (!huskylens.begin(Wire)) {
    Serial.println(F("Begin failed!"));
    Serial.println(F("1.Please recheck the \"Protocol Type\" in HUSKYLENS "
                     "(System Settings>>Protocol Type>> I2C/UART)"));
    Serial.println(F("2.Please recheck the connection."));
    Serial.println(F("\tgreen line >> SDA/TX; blue line >> SCL/RX"));
    delay(100);
  }
  huskylens.switchAlgorithm(ALGORITHM_DONKEYCAR);
  delay(5000);
}

void loop() {
  while (!huskylens.getResult(ALGORITHM_DONKEYCAR)) {
    delay(100);
  }

  while (huskylens.available(ALGORITHM_DONKEYCAR)) {
    Result *result = huskylens.popCachedResult(ALGORITHM_DONKEYCAR);

    Serial.print("result->ID=");
    Serial.println(result->ID);

    Serial.print("result->steering=");
    Serial.println(result->steering);
    Serial.print("result->throttle=");
    Serial.println(result->throttle);
  }
  delay(1000);
}