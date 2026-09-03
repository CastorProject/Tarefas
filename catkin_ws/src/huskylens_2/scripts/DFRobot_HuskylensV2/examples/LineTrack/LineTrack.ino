/***************************************************
 HUSKYLENS V2 An Easy-to-use AI Machine Vision Sensor
 <https://www.dfrobot.com/product-1922.html>

 ***************************************************
 This example demonstrates the line tracking functionality of HUSKYLENS V2 via
 I2C interface. It initializes the device, detects lines and paths, and prints
 detailed tracking information including line ID, level, vector coordinates,
 angle, and length, which can be used for robot navigation and path following
 applications.

 Created 2025-07-04
 By [Ouki Wang](ouki.wang@dfrobot.com)

 GNU Lesser General Public License.
 See <http://www.gnu.org/licenses/> for details.
 All above must be included in any redistribution
 ****************************************************/

/***********Notice and Trouble shooting***************
 1.Connection and Diagram can be found here
 <https://wiki.dfrobot.com/HUSKYLENS_V1.0_SKU_SEN0305_SEN0336#target_23>
 2.This code is tested on Arduino Uno, Leonardo, Mega boards.
 ****************************************************/

#include <DFRobot_HuskylensV2.h>

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
  huskylens.switchAlgorithm(ALGORITHM_LINE_TRACKING);
  delay(5000);
}

void loop() {
  while (!huskylens.getResult(ALGORITHM_LINE_TRACKING)) {
    delay(100);
  }
  Serial.println("\n\n\n\n");
  while (huskylens.available(ALGORITHM_LINE_TRACKING)) {
    Result *result = static_cast<Result *>(
        huskylens.popCachedResult(ALGORITHM_LINE_TRACKING));
    Serial.println("------------------------------");
    Serial.print("result->ID=0x");
    Serial.println(result->ID);

    Serial.print("result->level=");
    Serial.println(result->level);

    Serial.print("vector=(");
    Serial.print(result->xTarget);
    Serial.print(",");
    Serial.print(result->yCenter);
    Serial.println(")");

    Serial.print("result->angle=");
    Serial.println(result->angle);

    Serial.print("result->length=");
    Serial.println(result->length);
  }
  delay(1000);
}