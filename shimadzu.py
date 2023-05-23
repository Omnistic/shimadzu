import matplotlib.pyplot as plt
import serial
import time


# Control codes
ENQ = b'\x05'
EOT = b'\x04'
ESC = b'\x1B'
ACK = b'\x06'
NAK = b'\x15'
NUL = b'\x00'


class shimadzu:
    # Constructor
    def __init__(self, port='COM3', timeout=1.0):
        # Serial protocol properties
        BAUDRATE = 9600
        BYTESIZE = serial.SEVENBITS
        PARITY = serial.PARITY_ODD
        STOPBITS = serial.STOPBITS_ONE
        
        # Timeout
        self.__timeout = timeout
        
        # Connect to instrument
        self.__serial = serial.Serial(port=port,
                                      baudrate=BAUDRATE,
                                      bytesize=BYTESIZE,
                                      parity=PARITY,
                                      stopbits=STOPBITS,
                                      timeout=self.__timeout,
                                     )
        
        # Flush buffers
        self.__serial.reset_input_buffer()
        self.__serial.reset_output_buffer()

    # Destructor
    def __del__(self):
        # Flush buffers
        self.__serial.reset_input_buffer()
        self.__serial.reset_output_buffer()
        
        # Disconnect instrument
        self.__serial.close()
        
    # Protocol A (UV-1600 SERIES manual page 12-10)
    def __a(self, command):
        # Send ENQ
        self.__serial.write(ENQ)
        
        # Do not attempt to read an ACK from the instrument as it hasn't worked
        # for me yet.
        
        # Send command
        self.__serial.write(command+NUL)
        
        # Wait until EOT from instrument
        while self.__serial.read() != EOT:
            pass
            
        # Write ACK
        self.__serial.write(ACK)
    
    # [Measure] Performs wavelength scan
    def measure(self):
        # Define command
        command = b'a'
        
        # Use Protocol A to send command
        self.__a(command)
    
    # [Scanning range] Set the scanning range
    def set_scan_range(self, long_wave, short_wave):
        # Check boundary conditions are fullfilled
        long_bound = long_wave >= 190 and long_wave <= 1100
        short_bound = short_wave >= 190 and short_wave <= 1100
        diff_bound = long_wave - short_wave >= 10
        
        if long_bound and short_bound and diff_bound:
            command = b'h' + str.encode(str(long_wave))
            command += b',' + str.encode(str(short_wave))
        
        # Use Protocol A to send command
        self.__a(command)
    
    # [Scanning speed] Set the scanning speed
    def set_speed(self, speed='medium'):
        # Put speed into small letters
        speed = speed.lower()
        
        # Default speed code: Medium
        speed_code = b'2'
        
        # Resolve speed code from paramter
        if speed == 'fast':
            speed_code = b'1'
        if speed == 'medium':
            speed_code = b'2'
        if speed == 'slow':
            speed_code = b'3'
        if speed == 'very slow':
            speed_code = b'4'
        
        command = b'j' + speed_code
        
        # Use Protocol A to send command
        self.__a(command)
        
    # [Measurement mode] Set the measurement mode
    def set_mode(self, mode='abs'):
        # Put mode into small letters
        mode = mode.lower()
        
        # Default mode code: Abs
        mode_code = b'2'
        
        # Resolve mode code from parameter
        if mode == 't%':
            mode_code = b'1'
        if mode == 'abs':
            mode_code = b'2'
        if mode == 'energy':
            mode_code = b'3'
            
        command = b'v' + mode_code
        
        # Use Protocol A to send command
        self.__a(command)
        
    # [Wavelength setting] Set the wavelength, format: yxxx.x nm
    def set_wavelength(self, wavelength):
        # Define command: <wn> where n is between 1900 and 11000 included
        # it is assumed that the last digit is a decimal
        command = b'w' + str.encode(str(wavelength).replace('.',''))
        
        # Use Protocol A to send command
        self.__a(command)
        
    # [Transfer file data] Retrieves data which have been stored in memory
    def transfer(self):
        # Send ENQ
        self.__serial.write(ENQ)
        
        # Small pause seems required here
        time.sleep(.5)
        
        # Send command. Here I'm reading the maximum number of point and
        # waiting to recieve an EOT from the instrument to interupt the
        # transfer
        self.__serial.write(b'f1001'+NUL)
    
        # Wait until ENQ
        while self.__serial.read() != ENQ:
            pass
        
        # Write ACK
        self.__serial.write(ACK)
        
        # Placeholder in bytes of a single wavelength measurement
        data_in_bytes = b''
        
        # Initialize data lists
        wavelength = []
        measurement = []
        
        for ii in range(1001):            
            byte = self.__serial.read()
            
            if byte == EOT:
                self.__serial.write(ACK)
                break
            
            while byte != NUL:
                data_in_bytes += byte
                byte = self.__serial.read()
            
            data = data_in_bytes.split()
            
            data_in_bytes = b''
            
            wavelength.append(float(data[0]))
            measurement.append(float(data[1]))
            
            # Write ACK
            self.__serial.write(ACK)
            
        return wavelength, measurement
        
        
if __name__ == "__main__":
    # Create a new connection to the instrument
    spectro = shimadzu()
    
    # Set scan range
    spectro.set_scan_range(700, 400)
    
    # Select fast scan speed
    spectro.set_speed(speed='fast')
    
    # Select measurement mode
    spectro.set_mode()
    
    # Perform a measurement
    spectro.measure()
    
    # Retrieve measurement data
    wavelength, measurement = spectro.transfer()
    
    # Close the connection to the instrument
    del spectro
    
    # Display measurement result
    plt.figure()
    plt.plot(wavelength, measurement)
    plt.grid()
    plt.show()