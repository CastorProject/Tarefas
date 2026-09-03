# -*- coding: utf-8 -*
"""
    I2C PN7150近场通讯NFC模块
"""
import time
from pinpong.board import gboard, I2C


## i2c address
PN7150_I2C_ADDR = 0x28

_STATUS_OK = 0x00

PROT_UNDETERMINED = 0x0
PROT_T1T = 0x1
PROT_T2T = 0x2
PROT_T3T = 0x3
PROT_ISODEP = 0x4
PROT_NFCDEP = 0x5
PROT_T5T = 0x6
PROT_MIFARE = 0x80

_status = {
    # Status
    0x00: "OK",
    0x01: "REJECTED",
    0x02: "RF_FRAME_CORRUPTED",
    0x03: "FAILED",
    0x04: "NOT_INITIALIZED",
    0x05: "SYNTAX_ERROR",
    0x06: "SEMANTIC_ERROR",
    0x09: "INVALID_PARAM",
    0x0A: "MESSAGE_SIZE_EXCEEDED",
    # Discovery
    0xA0: "ALREADY_STARTED",
    0xA1: "TARGET_ACTIVATION_FAILED",
    0xA2: "TEAR_DOWN",
    # RF
    0xB0: "TRANSMISSION_ERROR",
    0xB1: "PROTOCOL_ERROR",
    0xB2: "TIMEOUT_ERROR",
}


def status(val):
    """!
    @brief Function for status
    @param val - status code
    """
    return _status.get(val, None) or "0x{:02x}".format(val)


# pylint: disable=too-many-branches
def dump_package(buf, end, prefix=""):
    """!
    @brief Function dump_package.
    @param buf - Unparsed data
    @param end - Length
    @param prefix - Prefix code
    """
    fst, snd = buf[0], buf[1]
    if fst & 0xE0 == 0:
        print(
            "{}Data packet to/from {} length {}".format(prefix, buf[0] & 0x0F, buf[2])
        )
    elif fst == 0x20 and snd == 0x00:
        print(
            "{}CORE_RESET_CMD({}) Reset Configuration: {}".format(prefix, end, buf[3])
        )
    elif fst == 0x40 and snd == 0x00:
        # pylint: disable=line-too-long
        print(
            "{}CORE_RESET_RSP({}) Status: {} NCI Version: 0x{:02x} Configuration Status: 0x{:02x}".format(
                prefix, end, status(buf[3]), buf[4], buf[5]
            )
        )
    elif fst == 0x20 and snd == 0x01:
        print("{}CORE_INIT_CMD({})".format(prefix, end))
    elif fst == 0x40 and snd == 0x01:
        # 3    Status
        # 4    NFCC Features
        #      ..
        # 8    #RF Interfaces
        #      RF Interfaces
        # 9+n  Max Logical Connections
        # 10+n Max Routing Table
        #      ..
        # 12+n Max Control Packet Payload Size
        # 13+n Max Size for Large Parameters
        #      ..
        # 15+n Manufacturer ID
        # 16+n Manufacturer Specific Information
        n = buf[8]
        print(
            "{}CORE_INIT_RSP({}) Status: {} #RF Interfaces: {} Max Payload Size: {}".format(
                prefix, end, status(buf[3]), n, buf[12 + n]
            )
        )
    elif fst == 0x60 and snd == 0x06:
        print("{}CORE_CONN_CREDITS_NTF({}) #Entries: {}".format(prefix, end, buf[3]))
    elif fst == 0x60 and snd == 0x07:
        print(
            "{}CORE_GENERIC_ERROR_NTF({}) Status: {}".format(
                prefix, end, status(buf[3])
            )
        )
    elif fst == 0x60 and snd == 0x08:
        print(
            "{}CORE_INTERFACE_ERROR_NTF({}) Status: {} ConnID: {}".format(
                prefix, end, status(buf[3]), buf[4]
            )
        )
    elif fst == 0x21 and snd == 0x00:
        print(
            "{}RF_DISCOVER_MAP_CMD({}) #Mapping Configurations: {}".format(
                prefix, end, buf[3]
            )
        )
    elif fst == 0x41 and snd == 0x00:
        print(
            "{}RF_DISCOVER_MAP_RSP({}) Status: {}".format(prefix, end, status(buf[3]))
        )
    elif fst == 0x21 and snd == 0x03:
        print("{}RF_DISCOVER_CMD({}) #Configurations: {}".format(prefix, end, buf[3]))
    elif fst == 0x41 and snd == 0x03:
        print("{}RF_DISCOVER_RSP({}) Status: {}".format(prefix, end, status(buf[3])))
    elif fst == 0x21 and snd == 0x06:
        print("{}RF_DEACTIVATE_CMD({}) Mode: {}".format(prefix, end, buf[3]))
    elif fst == 0x41 and snd == 0x06:
        print("{}RF_DEACTIVATE_RSP({}) Status: {}".format(prefix, end, status(buf[3])))
    elif fst == 0x61 and snd == 0x06:
        print(
            "{}RF_DEACTIVATE_NTF({}) Type: {} Reason: {}".format(
                prefix, end, buf[3], buf[4]
            )
        )
    elif fst == 0x61 and snd == 0x05:
        # 3    RF Discovery ID
        # 4    RF Interface
        # 5    RF Protocol
        # 6    Activation RF Technology and Mode
        # 7    Max Data Packet Payload Size
        # 8    Initial Number of Credits
        # 9    #RF Technology Specific Parameters
        #      RF Technology Specific Parameters
        # 10+n Data Exchange RF Technology and Mode
        # 11+n Data Exchange Transmit Bit Rate
        # 12+n Data Exchange Receive Bit Rate
        # 13+n #Activation Parameters
        #      Activation Parameters
        print(
            "{}RF_INTF_ACTIVATED_NTF({}) ID: {} Interface: {} Protocol: {} Mode: 0x{:02x} #RFparams: {}".format(
                prefix, end, buf[3], buf[4], buf[5], buf[6], buf[9]
            )
        )
    elif fst == 0x2F and snd == 0x02:
        print("{}PROPRIETARY_ACT_CMD({})".format(prefix, end))
    elif fst == 0x4F and snd == 0x02:
        print(
            "{}PROPRIETARY_ACT_RSP({}) Status: {}".format(prefix, end, status(buf[3]))
        )
    else:
        print("{}{:02x}:{:02x} {} bytes".format(prefix, buf[0], buf[1], end))


# MT=1 GID=0 OID=0 PL=1 ResetType=1 (Reset Configuration)
NCI_CORE_RESET_CMD = b"\x20\x00\x01\x01"
# MT=1 GID=0 OID=1 PL=0
NCI_CORE_INIT_CMD = b"\x20\x01\x00"
# MT=1 GID=f OID=2 PL=0
NCI_PROP_ACT_CMD = b"\x2f\x02\x00"
# MT=1 GID=1 OID=0
NCI_RF_DISCOVER_MAP_RW = (
    b"\x21\x00\x10\x05\x01\x01\x01\x02\x01\x01\x03\x01\x01\x04\x01\x02\x80\x01\x80"
)
# MT=1 GID=1 OID=3
NCI_RF_DISCOVER_CMD_RW = b"\x21\x03\x09\x04\x00\x01\x02\x01\x01\x01\x06\x01"
# MODE_POLL | TECH_PASSIVE_NFCA,
# MODE_POLL | TECH_PASSIVE_NFCF,
# MODE_POLL | TECH_PASSIVE_NFCB,
# MODE_POLL | TECH_PASSIVE_15693,
NCI_RF_DEACTIVATE_CMD = b"\x21\x06\x01\x00"


class Card:
    """!
    @brief Class card.
    """

    def __init__(self, buf, end):
        """!
        @brief Card structure init
        """
        self.card_id = buf[3]
        self.interface = buf[4]
        self.protocol = buf[5]
        self.modetech = buf[6]
        self.maxpayload = buf[7]
        self.credits = buf[8]
        self.nrfparams = buf[9]
        self.rest = buf[10:end]

    def nfcid1(self):
        """!
        @brief Function decode NFCID1 of rfts for NFC_A_PASSIVE_POLL_MODE
        """
        if self.modetech != 0x00:
            return None

        id_length = self.rest[2]

        return ":".join("{:02x}".format(x) for x in self.rest[3 : 3 + id_length])


class DFRobot_PN7150(object):
    """!
    @brief Define DFRobot_PN7150_I2C basic class
    """

    def __init__(self, board=None, i2c_addr=PN7150_I2C_ADDR, bus_num=1):
        """!
        @brief Module I2C communication init
        @param i2c_addr - I2C communication address
        @param bus_num - I2C bus
        """
        if isinstance(board, int):
            i2c_addr = board
            board = gboard
        elif board is None:
            board = gboard
        self._addr = i2c_addr
        # self._i2c = SMBus(bus_num)
        self._i2c = I2C(bus_num)
        self.board = board

        self._debug = False
        self._buf = bytearray(3 + 255)
        self.fw_version = self._buf[64]
        self.nfc_uid = [0]
        self.nfc_protocol = 0
        self.block_data = [0 for i in range(16)]

    def scan(self, uid=""):
        """!
        @brief Scan to determine whether there is a NFC smart card/tag.
        @param uid - UID of the NFC card.
        @return Boolean type, the result of operation
        """
        detectflag = self._scan()
        if uid == "":
            return detectflag
        else:
            if detectflag:
                if uid == self.read_uid():
                    return True
            return False

    def read_uid(self):
        """!
        @brief Obtain the UID of the card .
        @return UID of the card.
        """
        if not self._scan():
            return "no card!"
        if self.nfc_uid is None:
            return "read fail"
        else:
            return "".join([str(hex(u))[2:] for u in self.nfc_uid])

    def read_data(self, block, index=None):
        """!
        @brief Read a byte from a specified block of a MIFARE Classic NFC smart card/tag.
        @param block - The number of the block to read from.
        @param index - The offset of the block.
        @return Read from the card.
        """
        data = self._read_data(block)
        if (
            data == "no card!"
            or data == "read error!"
            or data == "read timeout!"
            or data == "wake up error!"
            or data == "false"
        ):
            return None
        if index is None:
            return data
        else:
            return self.block_data[index - 1]

    def write_index_data(self, block, index, data):
        """!
        @brief Write a byte to a MIFARE Classic NFC smart card/tag.
        @param block - The number of pages you want to writes the data.
        @param index - The offset of the data.
        @param data - The byte to be written.
        @return Boolean type, the result of operation
        """
        if isinstance(data, str):
            real_val = []
            for i in data:
                real_val.append(int(ord(i)))
            if len(real_val) < 16:
                for i in range(16 - len(real_val)):
                    real_val.append(0)
            elif len(real_val) > 16:
                return False
        if isinstance(data, list):
            real_val = []
            if len(data) < 16:
                for i in range(16 - len(data)):
                    data.append(0)
            elif len(data) > 16:
                return False
            real_val = data
        index = max(min(index, 16), 1)
        self.read_data(block)
        if isinstance(data, int):
            self.block_data[index - 1] = data
            self.write_data(block, self.block_data)
        else:
            block_data = [0 for i in range(index - 1)]
            block_data[index:] = real_val
            self.write_data(block, block_data)
        return True

    def write_data(self, block, data):
        """!
        @brief Write a block to a MIFARE Classic NFC smart card/tag.
        @param block - The number of the block to write to.
        @param data - The buffer of the data to be written.
        @return Boolean type, the result of operation
        """
        if isinstance(data, tuple):
            data = list(data)
        if isinstance(data, str):
            real_val = []
            for i in data:
                real_val.append(int(ord(i)))
            if len(real_val) < 16:
                for i in range(16 - len(real_val)):
                    real_val.append(0)
            elif len(real_val) > 16:
                return False
        if isinstance(data, list):
            real_val = []
            if len(data) < 16:
                for i in range(16 - len(data)):
                    data.append(0)
            elif len(data) > 16:
                return False
            real_val = data
        if block < 128 and ((block + 1) % 4 == 0 or block == 0):
            return False
        if block > 127 and block < 256 and (block + 1) % 16 == 0:
            return False
        if block > 255:
            return False
        if not self._scan():
            return False
        cmd_auth = [0x40, int(block / 4), 0x10, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        resp = self.tag_cmd(cmd_auth)
        if 0 == len(resp) or 0 != resp[-1]:
            return False
        cmd_write_1 = [0x10, 0xA0, block]
        resp = self.tag_cmd(cmd_write_1)
        if 0 == len(resp) or 0 != resp[-1]:
            return False
        cmd_write_2 = [0x10]
        cmd_write_2[1:] = real_val
        resp = self.tag_cmd(cmd_write_2)
        if 0 == len(resp) or 0 != resp[-1]:
            return False
        return True

    def read_protocol(self):
        if not self._scan():
            return "no card!"
        if self.nfc_protocol == PROT_T2T:
            return "T2T"
        elif self.nfc_protocol == PROT_UNDETERMINED:
            return "undetermined"
        elif self.nfc_protocol == PROT_T1T:
            return "T1T"
        elif self.nfc_protocol == PROT_T3T:
            return "T3T"
        elif self.nfc_protocol == PROT_ISODEP:
            return "isodep"
        elif self.nfc_protocol == PROT_NFCDEP:
            return "nfcdep"
        elif self.nfc_protocol == PROT_T5T:
            return "T5T"
        elif self.nfc_protocol == PROT_MIFARE:
            return "mifare"
        else:
            return "Unknow"
        
    def t2t_read(self, block, index=None):
        if index is not None:
            if index > 4:
                return "index error"
        if not self._scan():
            return "no card!"
        cmd_auth = [0x00, 0x00, 0x02, 0x30, block]
        self._write_block(cmd_auth)
        
        base = time.time() * 100
        timeout = 20
        while (time.time() * 100 - base) < timeout:
            end = self._read_wait()
            if self._buf[0] & 0xE0 == 0x00:
                break
            time.sleep(0.001)
        if end == 20:
          if index is None:
              return list(self._buf[3:7])
          else:
              #return self._buf[3+index-1]
              return self._buf[2+index]
        else:
          return None
    
    def t2t_write_index_data(self, block, index, data):
        if index > 4:
            return "index error"
        if not self._scan():
            return "write no card!"
        
        rslt = self.t2t_read(block)
        if rslt == None:
            return "write data error"
        if len(rslt) != 4:
            return "write data error"
        cmd_auth = [0x00, 0x00, 0x06, 0xA2, block] + rslt
        cmd_auth[4+index] = data
        
        self._write_block(cmd_auth)
        base = time.time() * 100
        timeout = 20
        while (time.time() * 100 - base) < timeout:
            end = self._read_wait()
            if self._buf[0] & 0xE0 == 0x00:
                break
            time.sleep(0.001)
        rslt = self.t2t_read(block)
        if rslt == None:
            return "write data error"
        if len(rslt) == 4:
            if rslt[index-1] == data:
                return "write data success"
        return "write data error"
          
        
    def t2t_write(self, block, data):
        if len(data) > 4:
            return "data error"
        if not self._scan():
            return "write no card!"
        cmd_auth = [0x00, 0x00, 0x06, 0xA2, block] + data
        self._write_block(cmd_auth)
        base = time.time() * 100
        timeout = 20
        while (time.time() * 100 - base) < timeout:
            end = self._read_wait()
            if self._buf[0] & 0xE0 == 0x00:
                break
            time.sleep(0.001)
        rslt = self.t2t_read(block)
        if rslt == None:
            return "write data error"
        if len(rslt) == 4:
            if rslt == data:
                return "write data success"
        return "write data error"
        
        
    def connect(self):
        """!
        @brief Function connect.
        @return Boolean type, the result of operation
        """
        try:
            ok = self._connect()
        finally:
            # print("finally connect")
            pass
        return ok

    def mode_rw(self):
        """!
        @brief Function mode Read/Write.
        @return Boolean type, the result of operation
        """
        self._write_block(NCI_RF_DISCOVER_MAP_RW)
        end = self._read_wait(10)
        return (
            end >= 4
            and self._buf[0] == 0x41
            and self._buf[1] == 0x00
            and self._buf[3] == _STATUS_OK
        )

    def start_discovery_rw(self):
        """!
        @brief Function Start Discovery Read/Write.
        @return Boolean type, the result of operation
        """
        self._write_block(NCI_RF_DISCOVER_CMD_RW)
        end = self._read_wait()
        return (
            end >= 4
            and self._buf[0] == 0x41
            and self._buf[1] == 0x03
            and self._buf[3] == _STATUS_OK
        )

    def stop_discovery(self):
        """!
        @brief Function stop Discovery.
        @return Boolean type, the result of operation
        """
        self._write_block(NCI_RF_DEACTIVATE_CMD)
        end = self._read_wait()
        return (
            end >= 4
            and self._buf[0] == 0x41
            and self._buf[1] == 0x06
            and self._buf[3] == _STATUS_OK
        )

    def wait_for_card(self):
        """!
        @brief Function wait for Card.
        @return Card information class
        """
        while True:
            end = 0
            while end == 0:
                end = self._read_wait()
            if self._buf[0] == 0x61 and self._buf[1] == 0x05:
                break

        return Card(self._buf, end)

    def tag_cmd(self, cmd, conn_id=0):
        """!
        @brief Function tag cmd.
        @param cmd - tag cmd
        @param conn_id - conn_id
        @return Data of the nfc module
        """
        self._buf[0] = conn_id
        self._buf[1] = 0x00
        self._buf[2] = len(cmd)
        end = 3 + len(cmd)
        self._buf[3:end] = cmd
        self._write_block(self._buf, end=end)

        base = time.time() * 100
        timeout = 5
        while (time.time() * 100 - base) < timeout:
            end = self._read_wait()
            if self._buf[0] & 0xE0 == 0x00:
                break
            time.sleep(0.001)

        return self._buf[3:end]

    def _scan(self):
        self.stop_discovery()
        self.start_discovery_rw()
        end = self._read_wait()
        if end == 0 or self._buf[0] != 0x61 or self._buf[1] != 0x05:
            return False
        # Card(self._buf, end)
        # print("ID: {}".format(card.nfcid1()))
        self.nfc_uid = self._buf[13:17]
        self.nfc_protocol = self._buf[5]
        # if not self.nfc_enable:
        #     return False
        # cmdnfc_uid = [self.COMMAND_INLISTPASSIVETARGET, 1, self.MIFARE_ISO14443A]
        # self.write_command(cmdnfc_uid, 3)
        # if not self.read_ack(25):
        #     return False
        # if len(self.receive_ACK) < 7:
        #     return False
        # self.nfc_uid = self.receive_ACK[19:23]
        # if self.receive_ACK[13] != 1:
        #     return False
        return True

    def _read_data(self, page):
        if page > 255:
            return "false"
        if not self._scan():
            return "no card!"
        cmd_auth = [0x40, int(page / 4), 0x10, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        resp = self.tag_cmd(cmd_auth)
        if 0 == len(resp) or 0 != resp[-1]:
            return "read error!"
        cmd_read = [0x10, 0x30, page]
        resp = self.tag_cmd(cmd_read)
        if 0 == len(resp) or 0 != resp[-1]:
            return "read timeout!"
        dataStr = ""
        for i in range(len(resp) - 2):
            self.block_data[i] = resp[i + 1]
            if resp[i + 1] <= 0x0F:
                # dataStr += "0"
                # dataStr += str(hex(resp[i + 1]))
                dataStr += "0x0" + format(resp[i + 1], "X")
            else:
                # dataStr += str(hex(resp[i + 1]))
                dataStr += "0x" + format(resp[i + 1], "X")
            if i < len(resp) - 3:
                dataStr += "."
        return dataStr

    def _connect(self):
        """!
        @brief Function connect.
        """
        self._write_block(NCI_CORE_RESET_CMD)
        end = self._read_wait(30)
        if (
            end < 6
            or self._buf[0] != 0x40
            or self._buf[1] != 0x00
            or self._buf[3] != _STATUS_OK
            or self._buf[5] != 0x01
        ):
            return False
        self._write_block(NCI_CORE_INIT_CMD)
        end = self._read_wait()
        if (
            end < 20
            or self._buf[0] != 0x40
            or self._buf[1] != 0x01
            or self._buf[3] != _STATUS_OK
        ):
            return False

        nrf_int = self._buf[8]
        self.fw_version = self._buf[17 + nrf_int : 20 + nrf_int]
        # print("Firmware version: 0x{:02x} 0x{:02x} 0x{:02x}".format(
        #    self.fw_version[0], self.fw_version[1], self.fw_version[2]))

        self._write_block(NCI_PROP_ACT_CMD)
        end = self._read_wait()
        if (
            end < 4
            or self._buf[0] != 0x4F
            or self._buf[1] != 0x02
            or self._buf[3] != _STATUS_OK
        ):
            return False

        # print("FW_Build_Number:", self._buf[4:8])
        return True

    def _read_wait(self, timeout=5):
        """!
        @brief read the data from the register
        @param timeout - timeout
        @return read data
        """
        base = time.time() * 100
        while (time.time() * 100 - base) < timeout:
            count = self._read_block()
            if 3 < count:
                return count
            time.sleep(0.01)
        return 0

    def _read_block(self):
        """!
        @brief read the data from the register
        @return read data
        """
        end = 0
        try:
            read_msg = self._i2c.readfrom(self._addr, 3)
            if None != read_msg:
                self._buf[0:2] = read_msg
                end = 3
                if self._buf[2] > 0:
                    read_msg = self._i2c.readfrom(self._addr, self._buf[2])
                    if len(list(read_msg)) == self._buf[2]:
                        self._buf[3:] = list(read_msg)
                        end = 3 + self._buf[2]
        except IOError as e:
            # print(f"I/O error: {e}")
            pass
        except Exception as e:
            print("An unexpected error occurred: {}".format(e))
        if self._debug:
            dump_package(self._buf, end, prefix="< ")
        return end

    def _write_block(self, cmd, end=0):
        """!
        @brief writes data to a register
        @param cmd - written data
        @param end - data len
        """
        cycle_count = 5
        self._read_block()
        if not end:
            end = len(cmd)
        if self._debug:
            dump_package(cmd, end, prefix="> ")
        while cycle_count:
            try:
                self._i2c.writeto(self._addr, list(cmd[0:end]))
                break
            except IOError as e:
                # print(f"I/O error: {e}")
                cycle_count -= 1
                self._read_block()
                time.sleep(0.01)
                # self._write_block(cmd)
            except Exception as e:
                print("An unexpected error occurred: {}".format(e))
