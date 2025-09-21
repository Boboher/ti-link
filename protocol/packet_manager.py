from utils.logger import log
from utils.helpers import string_is_valid_number


class Packet_Manager:
    """Manages packet creation and parsing for TI calculator communication."""
    
    def __init__(self):
        self.preset_packets = PresetPackets()
        self.base_packets = BasePackets()
        self.char_to_hex = CharToHex()
        self._hex_to_char_map = self._build_hex_to_char_map()

    def _build_hex_to_char_map(self):
        """Build reverse mapping for parsing responses."""
        return {tuple(codes): char for char, codes in self.char_to_hex.char_to_hex.items()}

    def create_packet(self, packet_type, **data):
        """Create packet based on type and parameters."""
        creators = {
            'send_var': lambda: self._create_variable_packet(data['var_name'], data['var_value']),
            'send_prog': lambda: self._create_program_packet(data['title'], data['text'], data['replace']),
            'read_prog': lambda: self._create_read_packet(data['title'])
        }
        
        creator = creators.get(packet_type)
        if not creator:
            log(f"ERROR: Unknown packet type: {packet_type}")
            return False
            
        return creator()

    def _create_variable_packet(self, var_name, var_value):
        """Create packet for sending a variable."""
        # Validate variable name (single letter)
        var_name = var_name.strip().upper()
        if not (len(var_name) == 1 and var_name.isalpha()):
            log("ERROR: Variable name must be a single letter")
            return False

        # Validate and convert value
        if not string_is_valid_number(var_value):
            log("ERROR: Invalid variable value")
            return False

        var_name_hex = f"{ord(var_name):02x}"
        var_value_hex = self._encode_ti_number(var_value)

        packet = self.base_packets.send_var.copy()
        packet[0]['data'] = (f'00000033040000002d000b0001{var_name_hex}'
                           f'0000000009010005000100040000000900020004f00b0000000300010000410001000008000400000000')
        packet[6]['data'] = f'0000000f0400000009000d00{var_value_hex}0000'
        
        return packet

    def _create_program_packet(self, title, program_text, replace):
        """Create packet for sending a program."""
        program_hex = self._text_to_hex(program_text)
        program_len = len(program_hex) // 2
        
        # Calculate packet lengths
        total_len = program_len + 8
        data_len = program_len + 2
        
        # Convert title
        title = title.upper()
        title_hex = ''.join(f"{ord(c):02x}" for c in title)
        title_len = len(title)
        
        # Format header components
        total_hex = f"{total_len:08x}"
        data_hex = f"{data_len:08x}"
        length_hex = self._format_length_field(program_len)
        
        # Build packet
        packet = self.base_packets.send_ti_basic_program.copy()
        
        # Header packet
        header_len = f"{50 + title_len:04x}"
        header_total = f"{44 + title_len:08x}"
        title_len_hex = f"{title_len:04x}"

        if replace:
            packet[0]['data'] = (f"0000{header_len}04{header_total}000b{title_len_hex}{title_hex}00{data_hex}"
                            f"01000500010004{data_hex}00020004f00b0005000300010000410001000008000400000000")
            packet[6]['data'] = f"{total_hex}04{data_hex}000d{length_hex}{program_hex}"
        
        if not replace:
            packet[0]['data'] = (f"0000{header_len}04{header_total}000b{title_len_hex}{title_hex}00{data_hex}"
                            f"00000500010004{data_hex}00020004f00b0005000300010000410001000008000400000000")
            packet[6]['data'] = f"{total_hex}04{data_hex}000d{length_hex}{program_hex}"
        
        return packet

    def _create_read_packet(self, title):
        """Create packet for reading a program."""
        title = title.strip().upper()
        title_hex = ''.join(f"{ord(c):02x}" for c in title)
        title_len = len(title)
        
        # Calculate header values
        total_len = f"{40 + title_len:08x}"
        data_len = f"{34 + title_len:08x}"
        title_len_hex = f"{title_len:04x}"
        
        packet = self.base_packets.read_ti_basic_program.copy()
        packet[0]['data'] = (f"{total_len}04{data_len}000c{title_len_hex}{title_hex}"
                           f"00017fffffff0006000100020003000500080041000100110004f00f00050000")
        
        return packet

    def _encode_ti_number(self, num_str):
        """Convert number string to TI calculator format."""
        if num_str.startswith(("0.", "0,")):
            # Decimal starting with 0 (e.g., 0.123)
            decimal_part = num_str[2:]
            return f"7f{decimal_part.ljust(10, '0')[:10]}"
        
        # Regular number
        separator = '.' if '.' in num_str else ','
        if separator in num_str:
            integer_part, decimal_part = num_str.split(separator)
            digits = integer_part + decimal_part
            digit_count = len(integer_part)
        else:
            digits = num_str
            digit_count = len(num_str)
        
        prefix = f"8{digit_count - 1}"
        padded_digits = digits.ljust(10, '0')[:10]
        return prefix + padded_digits

    def _format_length_field(self, value):
        """Format length value for packet headers."""
        hex_str = f"{value:x}"
        if len(hex_str) <= 2:
            return f"{hex_str:0>2s}00"
        elif len(hex_str) == 3:
            return f"{hex_str[:2]}0{hex_str[2]}"
        elif len(hex_str) == 4:
            return hex_str
        else:
            raise ValueError(f"Length value too large: {value}")

    def _text_to_hex(self, text):
        """Convert text to hex using TI character mapping."""
        text = text.replace("ENTER", "\n")
        hex_codes = []
        
        for char in text:
            if char in self.char_to_hex.char_to_hex:
                hex_codes.extend(self.char_to_hex.char_to_hex[char])
            else:
                log(f"WARNING: Unknown character '{char}', skipping")
        
        return ''.join(hex_codes)

    def parse_program_content(self, content):
        """Parse program content into readable text."""
        if not content:
            return ""
        
        # Skip 26-character header
        hex_data = content[26:]
        hex_bytes = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]
        
        result = []
        i = 0
        while i < len(hex_bytes):
            # Try two-byte sequence first, then single byte
            if i + 1 < len(hex_bytes):
                two_byte = tuple(hex_bytes[i:i+2])
                if two_byte in self._hex_to_char_map:
                    result.append(self._hex_to_char_map[two_byte])
                    i += 2
                    continue
            
            one_byte = tuple([hex_bytes[i]])
            if one_byte in self._hex_to_char_map:
                result.append(self._hex_to_char_map[one_byte])
            else:
                result.append('?')  # Unknown character
            i += 1
        
        return ''.join(result)

    def parse_program_titles(self, titles):
        """Parse program titles into readable text."""
        result = []

        for hex_str in titles:
            # Remove front and back characters
            trimmed = hex_str[26:len(hex_str)-108]

            # Convert hex to string
            try:
                ascii_str = bytes.fromhex(trimmed).decode('ascii')
            except Exception as e:
                ascii_str = f"<Error decoding: {e}>"

            result.append(ascii_str)

        return result


class PresetPackets:
    """Predefined packet sequences for TI calculator operations."""
    
    def __init__(self):
        self.init = [
            {'direction': 'OUT', 'data': '000000040100000400', 'desc': 'Initialization', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000402000003ff', 'desc': 'Init response', 'delay': 0},
            {'direction': 'OUT', 'data': '00000010040000000a0001000300010000000007d5', 'desc': 'Capability request', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000a04000000040012000007d5', 'desc': 'Capability data', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000a040000000400070001000a', 'desc': 'Request device info', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000e040000000800080001000a00000101', 'desc': 'Device info', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '00000024040000001e0007000e000800190023002d003700380012000c0011000f001e001f001d0000', 'desc': 'Variable type request', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '00000075040000006f0008000e00080000020073001900000101002301002d0000010100370000010100380000010000120000080000000000310000000c000008000000000004000000110000080000000000132b47000f0000080000000000400000001e0000020140001f00000200f0001d00000110000001', 'desc': 'Variable info', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '00000020040000001a0007000c00010004000600070009000b002d001b00480049004b005d', 'desc': 'Program type request', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '0000005c04000000560008000c00010000040000001300040000020007000600000109000700000101000900000400050601000b00000400050700002d00000101001b000001010048000002001100490000020006004b00000100005d00000101', 'desc': 'Program info', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Final ack', 'delay': 0}
        ]
        
        self.quit_exam_mode = [
            {'direction': 'OUT', 'data': '000000060400000000dd00', 'desc': 'Exit exam mode', 'delay': 0.1},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Confirm exit', 'delay': 0.1}
        ]

        self.get_all_program_names_initial = [
            {'direction': 'OUT', 'data': '00000023040000001d00090000000900010002000300050008004100800081000400010001000101', 'desc': 'Read request', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000a0400000004bb0000075300', 'desc': '?', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0}
        ]

        self.get_all_program_names_final = [
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '00000014040000000e0007000600060007000e000c0011000f', 'desc': '?', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': 'skip', 'desc': '?', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0}
        ]


class BasePackets:
    """Base packet templates for different operations."""
    
    def __init__(self):
        self.send_var = [
            {'direction': 'OUT', 'data': '', 'desc': 'Variable header', 'delay': 0},  # Modified by packet manager
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000a0400000004bb0000075300', 'desc': 'Ready to receive', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '000000070400000001aa0001', 'desc': 'Continue', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '', 'desc': 'Variable data', 'delay': 0},  # Modified by packet manager
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '000000070400000001aa0001', 'desc': 'Complete', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '000000060400000000dd00', 'desc': 'End transmission', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Final ack', 'delay': 0}
        ]
    
        self.send_ti_basic_program = [
            {'direction': 'OUT', 'data': '', 'desc': 'Program header', 'delay': 0},  # Modified by packet manager
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000a0400000004bb0000075300', 'desc': 'Ready to receive', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '000000070400000001aa0001', 'desc': 'Continue', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '', 'desc': 'Program data', 'delay': 0},  # Modified by packet manager
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': '000000070400000001aa0001', 'desc': 'Complete', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'OUT', 'data': '000000060400000000dd00', 'desc': 'End transmission', 'delay': 0},
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Final ack', 'delay': 0}
        ]
        
        self.read_ti_basic_program = [
            {'direction': 'OUT', 'data': '', 'desc': 'Read request', 'delay': 0},  # Modified by packet manager
            {'direction': 'IN', 'expected': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': 'skip', 'desc': 'Program data', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Ack', 'delay': 0},
            {'direction': 'IN', 'expected': 'store_content', 'desc': 'Additional data', 'delay': 0},
            {'direction': 'OUT', 'data': '0000000205e000', 'desc': 'Final ack', 'delay': 0}
        ]


class CharToHex:
    """Character to hex code mapping for TI calculator text encoding."""
    
    def __init__(self):
        self.char_to_hex = {
            # Lowercase letters (multi-byte encoding)
            'a': ['62', '16'], 'b': ['62', '17'], 'c': ['62', '18'], 'd': ['62', '19'], 'e': ['62', '1a'],
            'f': ['bb', 'b5'], 'g': ['bb', 'b6'], 'h': ['bb', 'b7'], 'i': ['bb', 'b8'], 'j': ['bb', 'b9'],
            'k': ['bb', 'ba'], 'l': ['bb', 'bc'], 'm': ['bb', 'bd'], 'n': ['62', '02'], 'o': ['bb', 'bf'],
            'p': ['62', '22'], 'q': ['bb', 'c1'], 'r': ['62', '12'], 's': ['62', '34'], 't': ['62', '24'],
            'u': ['5e', '80'], 'v': ['5e', '81'], 'w': ['5e', '82'], 'x': ['bb', 'c8'], 'y': ['bb', 'c9'],
            'z': ['62', '23'],

            # Uppercase letters (single-byte encoding)
            'A': ['41'], 'B': ['42'], 'C': ['43'], 'D': ['44'], 'E': ['45'], 'F': ['46'],
            'G': ['47'], 'H': ['48'], 'I': ['49'], 'J': ['4a'], 'K': ['4b'], 'L': ['4c'],
            'M': ['4d'], 'N': ['4e'], 'O': ['4f'], 'P': ['50'], 'Q': ['51'], 'R': ['52'],
            'S': ['53'], 'T': ['54'], 'U': ['55'], 'V': ['56'], 'W': ['57'], 'X': ['58'],
            'Y': ['59'], 'Z': ['5a'],

            # Digits
            '0': ['30'], '1': ['31'], '2': ['32'], '3': ['33'], '4': ['34'],
            '5': ['35'], '6': ['36'], '7': ['37'], '8': ['38'], '9': ['39'],

            # Common symbols
            ' ': ['29'], '\n': ['3f'], '.': ['3a'], ',': ['2b'], ':': ['3e'], ';': ['bb'],
            '!': ['2d'], '?': ['af'], "'": ['ae'], '"': ['2a'], '(': ['10'], ')': ['11'],
            '[': ['06'], ']': ['07'], '{': ['08'], '}': ['09'], '+': ['70'], '-': ['71'],
            '*': ['82'], '/': ['83'], '=': ['6a'], '<': ['6b'], '>': ['6c'], '^': ['f0'],

            # Extended symbols
            '`': ['bb', 'd5'], '~': ['bb', 'cf'], '@': ['bb', 'd1'], '#': ['bb', 'd2'],
            '$': ['bb', 'd3'], '%': ['bb', 'da'], '&': ['bb', 'd4'], '_': ['bb', 'd9'],
            '\\': ['bb', 'd7'], '|': ['bb', 'd8']
        }