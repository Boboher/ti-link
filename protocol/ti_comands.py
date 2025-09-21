import usb.core
import usb.util
import time
from utils.logger import log
from protocol.packet_manager import PresetPackets

class TI84PlusCE:
    def __init__(self):
        self.device = None
        self.endpoint_out = None
        self.endpoint_in = None
        
    def find_device(self):
        """Find the TI-84 Plus CE calculator"""
        # VID: 0x0451 (Texas Instruments)
        # PID: 0xe008 (TI-84 Plus CE)

        self.device = usb.core.find(idVendor=0x0451, idProduct=0xe008)
        
        if self.device is None:
            log("TI-84 Plus CE not found. Please check:")
            log("1. Calculator is connected via USB")
            log("2. Calculator is turned on")
            log("3. USB driver is installed via Zadig")
            log("4. VID/PID values are correct")
            return False
            
        log(f"Found TI-84 Plus CE: {self.device}")
        return True
    
    def setup_device(self):
        """Configure the USB device for communication"""
        try:
            # Detach kernel driver if necessary (Linux/Mac only)
            # Usually not needed on windows
            try:
                if self.device.is_kernel_driver_active(0):
                    self.device.detach_kernel_driver(0)
                    log("Detached kernel driver")
            except (NotImplementedError, AttributeError):
                pass
                
            # Set configuration
            self.device.set_configuration()
            
            # Get the active configuration
            cfg = self.device.get_active_configuration()
            intf = cfg[(0, 0)]  # Interface 0, alternate setting 0
            
            # Find bulk endpoints
            self.endpoint_out = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
            )
            
            self.endpoint_in = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
            )
            
            if self.endpoint_out is None or self.endpoint_in is None:
                log("Could not find bulk endpoints")
                return False
                
            log(f"OUT endpoint: 0x{self.endpoint_out.bEndpointAddress:02x}")
            log(f"IN endpoint: 0x{self.endpoint_in.bEndpointAddress:02x}")
            return True
            
        except usb.core.USBError as e:
            log(f"USB setup error: {e}")
            return False
    
    def send_data(self, data_hex, description=None):
        """Send data to the calculator, in chunks if 'large' is in the description"""
        try:
            # Convert hex string to bytes
            data = bytes.fromhex(data_hex.replace(' ', ''))
            log(f"Preparing to send: {data.hex()} ({len(data)} bytes)")
            
            chunk_size = 64
            use_chunking = description and 'large' in description.lower()
            
            if use_chunking:
                log("Chunked sending enabled")
                total_sent = 0
                for i in range(0, len(data), chunk_size):
                    chunk = data[i:i + chunk_size]
                    bytes_written = self.endpoint_out.write(chunk)
                    log(f"Sent chunk ({len(chunk)} bytes): {chunk.hex()}")
                    total_sent += bytes_written
                log(f"Total bytes sent: {total_sent}")
            else:
                bytes_written = self.endpoint_out.write(data)
                log(f"Sent {bytes_written} bytes")
            
            return True

        except usb.core.USBError as e:
            log(f"Send error: {e}")
            return False

    
    def receive_data(self, timeout=1000, max_packet_size=512):
        """Receive data from the calculator"""
        try:
            # Try to read larger buffer first
            data = self.endpoint_in.read(max_packet_size, timeout=timeout)
            received_bytes = data.tobytes()
            log(f"Received {len(received_bytes)} bytes: {received_bytes.hex()}")
            return received_bytes
            
        except usb.core.USBTimeoutError:
            log("Receive timeout - no data received")
            return None
        except usb.core.USBError as e:
            log(f"Receive error: {e}")
            # If large read fails, try smaller chunks
            try:
                log("Trying smaller read size...")
                data = self.endpoint_in.read(64, timeout=timeout)
                received_bytes = data.tobytes()
                log(f"Received {len(received_bytes)} bytes: {received_bytes.hex()}")
                return received_bytes
            except:
                return None
    
    def receive_data_chunked(self, timeout=1000):
        """Receive data in chunks for larger packets"""
        all_data = b''
        chunk_size = 64
        
        while True:
            try:
                chunk = self.endpoint_in.read(chunk_size, timeout=timeout)
                chunk_bytes = chunk.tobytes()
                all_data += chunk_bytes
                log(f"Chunk received: {len(chunk_bytes)} bytes")
                
                # If chunk is smaller than expected, we probably got all data
                if len(chunk_bytes) < chunk_size:
                    break
                    
            except usb.core.USBTimeoutError:
                log("No more data - timeout reached")
                break
            except usb.core.USBError as e:
                log(f"Chunk read error: {e}")
                break
        
        if all_data:
            log(f"Total received: {len(all_data)} bytes: {all_data.hex()}")
            return all_data
        return None
    
    def transaction_step(self, step_num, direction, data_hex=None, expected_response=None, description=""):
        """
        Execute a single transaction step
        
        Args:
            step_num: Step number for logging
            direction: 'OUT' (send to calc) or 'IN' (receive from calc)
            data_hex: Hex string to send (for OUT operations)
            expected_response: Expected hex response (for validation)
            description: Human readable description of what this step does
        """
        log(f"--- Step {step_num}: {direction} {description} ---")
        
        if direction == 'OUT':
            if data_hex is None:
                log("ERROR: No data specified for OUT operation")
                return False
            return self.send_data(data_hex, description)
        
        elif direction == 'IN' and expected_response == "skip":
            # For large packets, try chunked reading
            if "large" in description.lower():
                response = self.receive_data_chunked()
            else:
                response = self.receive_data()
                
            if response is None:
                log("No response received")
                return False
            return response
        
        elif direction == 'IN':
            # For large packets, try chunked reading
            if "large" in description.lower():
                response = self.receive_data_chunked()
            else:
                response = self.receive_data()
                
            if response is None:
                log("No response received")
                return False
                
            response_hex = response.hex()
            if expected_response:
                if response_hex == expected_response.replace(' ', ''):
                    log(f"Got expected response: {response_hex}")
                else:
                    log(f"Response mismatch!")
                    log(f"Expected: {expected_response}")
                    log(f"Got:      {response_hex}")
            else:
                log(f"Response: {response_hex}")
            
            return response
        
        else:
            log(f"ERROR: Unknown direction '{direction}'")
            return False
        
    
    def perform_sequence(self, sequence):
        """
        Execute a custom transaction sequence
        
        Args:
            steps: List of dictionaries, each containing:
                   {'direction': 'OUT'/'IN', 'data': 'hex_string', 'expected': 'hex_string', 'desc': 'description', 'delay': seconds}
        """
        log("Starting custom transaction...")
        
        for i, step in enumerate(sequence, 1):
            # Optional delay before step
            if 'delay' in step and step['delay'] > 0:
                time.sleep(step['delay'])
            
            direction = step['direction']
            data_hex = step.get('data', None)
            expected = step.get('expected', None)
            description = step.get('desc', '')
            
            result = self.transaction_step(i, direction, data_hex, expected, description)
            
            # Stop if step failed (for OUT operations)
            if direction == 'OUT' and not result:
                log(f"Transaction failed at step {i}")
                return False
        
        log("Transaction completed!")
        return True
    
    def get_all_program_names(self):
        """
        Get all program names from the TI-84 Plus CE calculator
        
        Args:
            initial_sequence: List of transaction steps to execute before the loop
            final_sequence: List of transaction steps to execute after the loop
            
        Returns:
            List of hex responses that contained the target pattern
        """
        initial_sequence = PresetPackets().get_all_program_names_initial
        final_sequence = PresetPackets().get_all_program_names_final
        
        log("Starting get_all_program_names...")
        
        # Pattern to look for in responses
        target_pattern = "00050003000001000005010008000004000000"
        termination_pattern = "000000060400000000dd00"
        loop_send_data = "0000000205e000"
        
        # List to store responses containing the target pattern
        program_responses = []
        
        # Execute initial preset sequence if provided
        if initial_sequence:
            log("Executing initial sequence...")
            if not self.perform_sequence(initial_sequence):
                log("Initial sequence failed!")
                return False
        
        # Main loop
        log("Starting main loop...")
        loop_count = 0
        max_loops = 250  # Safety limit to prevent infinite loops
        
        while loop_count < max_loops:
            loop_count += 1
            log(f"--- Loop iteration {loop_count} ---")
            
            # Receive data from TI
            response = self.receive_data()
            if response is None:
                log("No response received from TI, continuing...")
            else:
                response_hex = response.hex()
                log(f"Received response: {response_hex}")
                
                # Check if response contains the target pattern
                if target_pattern in response_hex:
                    log("Found target pattern! Storing response...")
                    program_responses.append(response_hex)
                
                # Check for termination condition
                if response_hex == termination_pattern.replace(' ', ''):
                    log("Termination pattern detected! Exiting loop...")
                    break
            
            # Send the loop data to TI
            log(f"Sending loop data: {loop_send_data}")
            if not self.send_data(loop_send_data, "Loop send"):
                log("Failed to send loop data!")
                return False
        
        if loop_count >= max_loops:
            log(f"WARNING: Loop terminated after {max_loops} iterations (safety limit)")
        
        # Execute final preset sequence if provided
        if final_sequence:
            log("Executing final sequence...")
            if not self.perform_sequence(final_sequence):
                log("Final sequence failed!")
                return False
        
        log(f"get_all_program_names completed. Found {len(program_responses)} responses with target pattern.")
        return program_responses
    
    def get_program_content(self, packet):
        """
        Execute a transaction sequence and return the stored value from the "store_value" step
        
        Args:
            packet: List of transaction steps, same format as perform_sequence
                   One step should have 'desc' containing "store_value" to mark what to return
        
        Returns:
            The hex string from the step marked with "store_value", or None if not found
        """
        log("Starting get_program_content...")
        
        stored_value = None
        
        for i, step in enumerate(packet, 1):
            # Optional delay before step
            if 'delay' in step and step['delay'] > 0:
                time.sleep(step['delay'])

            
            direction = step['direction']
            data_hex = step.get('data', None)
            expected = step.get('expected', None)
            description = step.get('desc', '')

            
            # Execute the transaction step
            result = self.transaction_step(i, direction, data_hex, expected, description)
            
            # Stop if OUT operation failed
            if direction == 'OUT' and not result:
                log(f"Transaction failed at step {i}")
                return None
            
            # Check if this is the step we need to store
            if direction == 'IN' and result and "store_content" in expected.lower():
                if isinstance(result, bytes):
                    stored_value = result.hex()
                else:
                    stored_value = str(result)
                log(f"Stored value from step {i}: {stored_value}")
        
        log("get_program_content completed!")
        
        if stored_value is None:
            log("WARNING: No step with 'store_value' description found!")
        
        return stored_value