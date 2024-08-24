import pyvisa
import read_cal_file

# Base class for all instruments
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

    def write(self, command: str):
        if self.connected:
            try:
                self.resource.write(command)
                print(f"Command sent: {command}")
            except pyvisa.VisaIOError as e:
                print(f"Failed to write command: {e}")
        else:
            print("Instrument is not connected.")

    def query(self, command: str):
        if self.connected:
            try:
                response = self.resource.query(command)
                print(f"Response received: {response}")
                return response
            except pyvisa.VisaIOError as e:
                print(f"Failed to query command: {e}")
        else:
            print("Instrument is not connected.")
            return None

# Subclass for ESG (Example Signal Generator)
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

    def load_esg_wfm(self, wfm):
        self.wfm = wfm
        cmd = f':MEM:COPY "{wfm}"@NVWFM, "{wfm}"@WFM1'# :MEM:COPY "wfm path@NVWFM", "wfmpath@WFM1"
        self.write(cmd)
        
# Subclass for EXA (Example Spectrum Analyzer)
class EXA(Instrument):
    def __init__(self, address: str):
        super().__init__(address)
    
    def sa_preset(self):
        self.write(":SYSt:PRES")
        
    def set_center_freq(self, freq):
        self.freq = freq
        cmd = f":FREQ:CENT {freq} MHz"
        self.write(cmd)
    
    def set_sa_span(self, span):
        self.span = span
        cmd = f":FREQ:SPAN {span} MHz"
        self.write(cmd)
    
    def set_sa_reflevel(self, rlev):
        self.rfl = rlev
        cmd = f":DISP:WIND:TRAC:Y:RLEV"
    
    def sa_opc(self):
        val=0
        while val == 0:
            val = self.query("*OPC?")
        return val

    def sa_set_atten(self, atten):
        self.atten = atten
        cmd = f":POW:ATT {atten}"
        self.write(cmd)
    
    def get_sa_peak_srch(self, peak):
        self.peak = peak
        cmd = f":CALC:MARK 1:MAX"
        peak = self.query(cmd)
        return peak
    
    def set_sa_rbw(self, rbw):
        self.rbw = rbw
        cmd = f":BWID {rbw} MHz"
        self.write(cmd)
    
    def set_sa_vbw(self, vbw):
        self.vbw = vbw
        cmd = f":BWID:VID {vbw} MHz"
        self.write(cmd)
    
    def set_sa_mode(self, mode):
        self.mode = mode
        cmd = f":INST:NSEl {mode}"
        self.write(cmd)

    def set_sa_corr(self, tbl):
        self.tbl = tbl
        
        self.write(":CORR:CSET1 OFF")
        val = 0
        while val == 0:
            val = self.query("*OPC?")
            print(val)
        self.write(":CORR:CSET:ALL:DEL")
        self.sa_opc()
        self.write(f":CORR:CSET1:DATA {tbl}")
        self.sa_opc()
        self.write(":SENS:CORR:CSET1 ON")
    
    def set_sa_evm(self):
        self.write("INST:NSEl 102")
        self.sa_opc()
        self.write("INIT:CONT 1")
        self.write(":EVM:AVER:STAT 0")
        self.write(":CONF:EVM")
        self.sa_opc()
        self.write(":INIT:EVM")
    
    def set_dir_ul(self):
        self.write(":RAD:STAN:DIR ULIN")
    
    def set_dir_dl(self):
        self.write(":RAD:STAN:DIR DLIN")
    
    def sa_get_evm(self):
        return(self.query(":FETC:EVM?"))
    
    def set_evm_trace_auto(self):
        self.write(":DISP:EVM:TRAC1:Y:AUTO:ONCE")
        self.write(":DISP:EVM:TRAC2:Y:AUTO:ONCE")
        self.write(":DISP:EVM:TRAC3:Y:AUTO:ONCE")
        self.write(":DISP:EVM:TRAC4:Y:AUTO:ONCE")
        
# Subclass for Power Supply
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
           resp = float(response)
           return resp
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

    def opc(self):
        val=0
        while val == 0:
            val = self.query("*OPC?")
        return val


