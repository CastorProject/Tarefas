/***************************************************
 HUSKYLENS V2 An Easy-to-use AI Machine Vision Sensor
 <https://www.dfrobot.com/product-1922.html>

 ***************************************************
 This example demonstrates the eye gaze recognition functionality of HUSKYLENS
 V2 via I2C interface. It initializes the device, detects human eye gaze
 direction using the ALGORITHM_GAZE_RECOGNITION algorithm, and prints detailed
 recognition results including ID, pitch angle, yaw angle, name, and content.

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
#define RX_PIN_P0 1
#define TX_PIN_P1 2

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
  huskylens.switchAlgorithm(ALGORITHM_GAZE_RECOGNITION);
  delay(5000);
}

void loop() {
  while (!huskylens.getResult(ALGORITHM_GAZE_RECOGNITION)) {
    delay(100);
  }

  while (huskylens.available(ALGORITHM_GAZE_RECOGNITION)) {
    Result *result = static_cast<Result *>(
        huskylens.popCachedResult(ALGORITHM_GAZE_RECOGNITION));

    Serial.print("result->ID=");
    Serial.println(result->ID);

    Serial.print("result->pitch=");
    Serial.println(result->pitch);
    Serial.print("result->yaw=");
    Serial.println(result->yaw);

    // Azimuth: the horizontal projection angle.
    // 0 degrees points to the right side of the screen, increasing
    // counterclockwise.
    Serial.print("result->azimuth=");
    Serial.println(result->azimuth);
    // The spatial unit length is 432. 'length' is the projected length.
    Serial.print("result->length=");
    Serial.println(result->length);

    Serial.print("result->name=");
    Serial.println(result->name);
    Serial.print("result->content=");
    Serial.println(result->content);
  }
  delay(1000);
}