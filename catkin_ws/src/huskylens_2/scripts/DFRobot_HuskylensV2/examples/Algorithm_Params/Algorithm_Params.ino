/***************************************************
 HUSKYLENS V2 An Easy-to-use AI Machine Vision Sensor
 <https://www.dfrobot.com/product-1922.html>

 This example demonstrates how to get and set algorithm parameters for HUSKYLENS
 V2 via I2C interface. It shows how to retrieve boolean parameters (like
 "show_name") and floating-point parameters (like "det_thres") from the face
 recognition algorithm, and then modify these parameters to customize the
 sensor's behavior.
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

// HUSKYLENS green line >> SDA; blue line >> SCL
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
  float det_thres =
      huskylens.getAlgoParamFloat(ALGORITHM_FACE_RECOGNITION, "det_thres");

  Serial.println(det_thres);
}

void loop() {
  huskylens.setAlgoParamBool(ALGORITHM_TAG_RECOGNITION, "show_name", false);
  huskylens.setAlgoParamString(ALGORITHM_TAG_RECOGNITION, "dict_type", "36h10");
  huskylens.updateAlgoParams(ALGORITHM_TAG_RECOGNITION);
  bool ret = huskylens.getAlgoParamBool(ALGORITHM_TAG_RECOGNITION, "show_name");
  String dict_type =
      huskylens.getAlgoParamString(ALGORITHM_TAG_RECOGNITION, "dict_type");
  Serial.println(ret);
  Serial.println(dict_type);
  delay(8000);
  huskylens.setAlgoParamBool(ALGORITHM_TAG_RECOGNITION, "show_name", true);
  huskylens.setAlgoParamString(ALGORITHM_TAG_RECOGNITION, "dict_type", "36h11");
  huskylens.updateAlgoParams(ALGORITHM_TAG_RECOGNITION);
  ret = huskylens.getAlgoParamBool(ALGORITHM_TAG_RECOGNITION, "show_name");
  dict_type =
      huskylens.getAlgoParamString(ALGORITHM_TAG_RECOGNITION, "dict_type");
  Serial.println(ret);
  Serial.println(dict_type);
  delay(8000);
}