import pyvisa

class Instrument:
    def __init__(self, address: str):
        self.address = address
        self.resource = None
        self.connected = False
        self.rm = pyvisa.ResourceManager()
    
    def connect(self):
        if not self.connected:
            try:
                self.resource = self.rm.open_resource(self.address)
                self.connected = True
                print(f"Connected to instrument at address {self.address}")
            except pyvisa.VisaIOError as e:
                print(f"Failed to connect: {e}")
    
    def disconnect(self):
        if self.connected:
            try:
                self.resource.close()
                self.connected = False
                print(f"Disconnected from instrument at address {self.address}")
            except pyvisa.VisaIOError as e:
                print(f"Failed to disconnect: {e}")

    def is_connected(self):
        return self.connected

    def get_status(self):
        if self.connected:
            return "Instrument is connected."
        else:
            return "Instrument is not connected."

    def write(self, command):
        if self.connected:
            try:
                self.resource.write(command)
                print(f"Command sent: {command}")
            except pyvisa.VisaIOError as e:
                print(f"Failed to write command: {e}")
        else:
            print("Instrument is not connected.")

    def query(self, command):
        if self.connected:
            try:
                resp = self.resource.query(command)
                print(f"Response received: {resp}")
                return resp
            except pyvisa.VisaIOError as e:
                print(f"Failed to query command: {e}")
        else:
            print("Instrument is not connected.")
            return None

class ESG(Instrument):
    def __init__(self, addr):
        super().__init__(addr)
    
    def set_frequency(self, freq: float):
        self.frequency = freq
        freq = freq * 1E6
        cmd = f":FREQ:FIX {freq}"
        self.write(cmd)
        
    def set_amplitude(self, ampl: float):
        self.ampl = ampl
        cmd = f":POW:LEV:IMM:AMPL {ampl}"
        self.write(cmd)
    
    def rf_out(self, pwr):
        self.pwr = pwr
        cmd = f":OUTP:STAT {pwr}"
        self.write(cmd)

class EXA(Instrument):
    def __init__(self, address: str):
        super().__init__(address)
    
    def set_range(self, start: float, end: float):
        self.range_start = start
        self.range_end = end
        command = f"FREQ:START {self.range_start}; FREQ:STOP {self.range_end}"
        self.write(command)
    
    def get_range(self):
        start = self.query("FREQ:START?")
        end = self.query("FREQ:STOP?")
        if start and end:
            return (float(start.strip()), float(end.strip()))
        return (None, None)

class PS(Instrument):
    def __init__(self, address: str):
        super().__init__(address)
    
    def set_voltage(self, voltage: float):
        self.voltage = voltage
        command = f":VOLT {self.voltage}"
        self.write(command)
    
    def set_current(self, current: float):
        self.current = current
        command = f"CURR {self.current}"
        self.write(command)
    
    def get_voltage(self):
        response = self.query("VOLT?")
        if response:
            return float(response.strip())
        return None
    
    def get_current(self):
        response = self.query("CURR?")
        if response:
            return float(response.strip())
        return None
    
    def output(self, val):
        self.val = val
        cmd = f":OUTP:STAT {val}"
        self.write(cmd)

def read_instrument_addresses(filename: str):
    instruments = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                # Strip leading/trailing whitespace and split by comma
                parts = line.strip().split(',')
                if len(parts) != 2:
                    print(f"Invalid line format: {line}")
                    continue

                instr_type, address = parts
                instr_type = instr_type.strip()
                address = address.strip()

                # Create instrument instance based on type
                if instr_type == "EXA":
                    instruments[instr_type] = EXA(address)
                elif instr_type == "ESG":
                    instruments[instr_type] = ESG(address)
                elif instr_type == "PS":
                    instruments[instr_type] = PS(address)
                else:
                    print(f"Unknown instrument type: {instr_type}")
        
        return instruments
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return {}







