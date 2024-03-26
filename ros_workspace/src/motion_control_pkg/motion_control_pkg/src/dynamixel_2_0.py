import sys
import DynamixelSDK.python.src.dynamixel_sdk as dxl
from dynamixel_consts import * 

# Control table values - will need to find safe values
PROF_VEL = 50           # Max speed 0-32767 * 1.374 deg/s
PROF_ACC = 50           # Max accel 0-32767 * 21.4577 deg/s^2

# Default settings for U2D2
DEVICENAME = 'COM12'  # Replace with the appropriate device name

# Initialize the U2D2 and Dynamixel motors
PACKET_HANDLER = dxl.PacketHandler(PROTOCOL_VERSION)

class Motors:
    """
    Initialise with DoF, DeviceName (ie COM Port) and Baudrate
    """
    def __init__(self, dof: int, devicename: str=DEVICENAME, baudrate: int=57600) -> None:
        self._port_handler = dxl.PortHandler(devicename)
        self.baudrate = baudrate
        self.num_motors = dof
        self.torque_status = []
        self.pos = []
        self.load = []
        self._port_open()
        self._sync_torque()
        self.motors = self._get_motors()
        self._set_profile()
        # self.torque_toggle(set=1)       # Activate motor

    # Port management    
    """
    Open port and setup baudrate
    If fails, to exit program
    Check connection and restart
    """
    def _port_open(self) -> None:   
        # Open the port
        port_attempt = 0
        print("Attempting to open the port...")
        while port_attempt < 3:
            port_attempt += 1
            try:
                self._port_handler.openPort()
                print("\tSucceeded to open the port.")
                break
            except:
                print("...")
        if port_attempt == 3:
            print("\tFailed to open the port.\nExiting program.")
            exit(1)
        
        # Set baudrate
        baud_attempt = 0
        print("Attempting to set baudrate...")
        while baud_attempt < 3:
            baud_attempt += 1
            try: 
                self._port_handler.setBaudRate(self.baudrate)
                print("\tSucceeded to set the baudrate.")
                break
            except:
                print("...")
        if baud_attempt == 3:
            print("\tFailed to set the baudrate.\nExiting program.")
            exit(1)
        return

    def port_close(self) -> None:   # Close the port and end session
        print("Closing port...")
        self.torque_toggle(set=0)
        self._port_handler.closePort()
        print("Closed.")
        return

    def _get_motors(self) -> list:   # Get motor types
        motor_types = []
        for i in range(self.num_motors):
            m_type = PACKET_HANDLER.read2ByteTxRx(self._port_handler, i+1, ADDR_MODEL_NUM)
            motor_types.append(m_type)
        return motor_types

    # Motor Functions    
    def set_goal(self, target_pos: list) -> None:
        for i in range(len(target_pos)):
            PACKET_HANDLER.write4ByteTxRx(self._port_handler, i+1, ADDR_GOAL_POS, target_pos[i]) 
        return
    
    def set_goal(self, id: int, target_pos: int) -> None:
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, id, ADDR_GOAL_POS, target_pos)
        return

    def _sync_torque(self) -> None:      # Set all torque to zero
        for i in range(self.num_motors):
            PACKET_HANDLER.write1ByteTxRx(self._port_handler, i+1, ADDR_TORQUE_ENABLE, 0) 
            self.torque_status[i] = 0
        return 
    
    """
    Limits based on dynamixel_consts.py - to edit in there
    """
    def _set_limits(self) -> None:
        """
        Assign motor id to movement
        """
        shoulder_flexex = 1
        shoulder_abad = 2
        shoulder_rot = 3
        elbow_flexex = 4
        pro_sup = 5
        
        # Write limits
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, shoulder_abad, ADDR_MAX_POS, SHOULDER_ABDUCTION["max"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, shoulder_abad, ADDR_MIN_POS, SHOULDER_ABDUCTION["min"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, shoulder_flexex, ADDR_MAX_POS, SHOULDER_FLEX_EX["max"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, shoulder_flexex, ADDR_MIN_POS, SHOULDER_FLEX_EX["min"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, shoulder_rot, ADDR_MAX_POS, SHOULDER_ROT["max"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, shoulder_rot, ADDR_MIN_POS, SHOULDER_ROT["min"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, elbow_flexex, ADDR_MAX_POS, ELBOW_FLEX_EX["max"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, elbow_flexex, ADDR_MIN_POS, ELBOW_FLEX_EX["min"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, pro_sup, ADDR_MAX_POS, PRO_SUP["max"])
        PACKET_HANDLER.write4ByteTxRx(self._port_handler, pro_sup, ADDR_MIN_POS, PRO_SUP["min"])

    def torque_toggle(self, set: int=None, id: int=None) -> None:
        if id==None:
            if set==None:
                for i in range(self.num_motors):
                    PACKET_HANDLER.write1ByteTxRx(self._port_handler, i+1, ADDR_TORQUE_ENABLE, not self.torque_status[i])
                self.torque_status[i] = not self.torque_status[i]
            else:
                for i in range(self.num_motors):
                    PACKET_HANDLER.write1ByteTxRx(self._port_handler, i+1, ADDR_TORQUE_ENABLE, set)
                self.torque_status[i] = set
        else:
            if set==None:
                PACKET_HANDLER.write1ByteTxRx(self._port_handler, id, ADDR_TORQUE_ENABLE, not self.torque_status[id-1])
                self.torque_status[id-1] = not self.torque_status[id-1]
            else:
                PACKET_HANDLER.write1ByteTxRx(self._port_handler, id, ADDR_TORQUE_ENABLE, set)
                self.torque_status[id-1] = set
        return
            
    def _set_profile(self, vel: int=PROF_VEL, accel: int=PROF_ACC, id: int=None) -> None:
        if id==None:
            for i in range(self.num_motors):
                PACKET_HANDLER.write4ByteTxRx(self._port_handler, i+1, ADDR_VELOCITY_PROF, vel)
                PACKET_HANDLER.write4ByteTxRx(self._port_handler, i+1, ADDR_ACCELERATION_PROF, accel)
        else:
            PACKET_HANDLER.write4ByteTxRx(self._port_handler, id, ADDR_VELOCITY_PROF, vel)
            PACKET_HANDLER.write4ByteTxRx(self._port_handler, id, ADDR_ACCELERATION_PROF, accel)
        return

    # Read functions
    def get_current_pos(self, id: int=None) -> None:
        if id==None:
            for i in range(self.num_motors):
                self.pos[i] = PACKET_HANDLER.read4ByteTxRx(self._port_handler, i+1, ADDR_PRESENT_POS)
        else:
            self.pos[id-1] = PACKET_HANDLER.read4ByteTxRx(self._port_handler, id, ADDR_PRESENT_POS)
        return 
    
    def get_current_load(self, id: int=None) -> None:
        if id==None:
            for i in range(self.num_motors):
                self.load[i] = PACKET_HANDLER.read2ByteTxRx(self._port_handler, i+1, ADDR_PRESENT_CURRENT)
        else:
            self.load[id-1] = PACKET_HANDLER.read2ByteTxRx(self._port_handler, id, ADDR_PRESENT_CURRENT)
        return 

# Will need to change to something valid
TEST_POSITION = [2000, 2000, 2000, 2000, 2000]

# Test Angles
def main():
    arm = Motors(5)
    while True:
        id = input(f'Enter motor to check <1> - <{arm.num_motors}>, anything else to quit.\n')
        if id.isnumeric() and int(id) <= arm.num_motors and int(id) > 0:
            arm.torque_toggle(1, int(id))
            print(f'Checking Motor {id}')
        else:
            break
        while True:
            pos = input(f'Enter position to check <0> - <4095>, anything else to quit. \n')
            if pos.isnumeric() and int(pos) >= 0 and int(pos) < 4096:
                arm.set_goal(id, int(pos))
            else:
                break
    arm.port_close()
                
if __name__ == "__main__":
    main()