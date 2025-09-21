import sys
import time
from protocol.ti_comands import TI84PlusCE
from protocol.packet_manager import Packet_Manager
from utils.logger import create_new_log

# Initialize calculator and packet manager
calc = TI84PlusCE()
pm = Packet_Manager()


def send_variable():
    var_name = input("Enter variable name: ")
    var_value = input("Enter variable value: ")
    packet = pm.create_packet('send_var', var_name=var_name, var_value=var_value)
    calc.perform_sequence(packet)

def send_program(title = None, text = None):
    if title == None:
        title = input("Enter program title: ").strip().upper()
    if text == None:
        text = input("Enter program text: ")

    # Check if program exists already
    program_names_packet = calc.get_all_program_names()
    program_names = pm.parse_program_titles(program_names_packet)
    if title in program_names:
        packet = pm.create_packet('send_prog', title=title, text=text, replace=True)
    else:
        packet = pm.create_packet('send_prog', title=title, text=text, replace=False)

    calc.perform_sequence(packet)

def disable_exam_mode():
    packet = pm.preset_packets.quit_exam_mode
    calc.perform_sequence(packet)

def list_programs():
    program_names_packet = calc.get_all_program_names()
    program_names = pm.parse_program_titles(program_names_packet)
    print("Stored Programs:")
    for i, name in enumerate(program_names, 1):
        print(f"{i}. {name}")
    return program_names

def read_program():
    programs = list_programs()
    if not programs:
        print("No programs found.")
        return
    choice = input("Enter program title to read: ")
    if choice not in programs:
        print("Invalid program title.")
        return
    packet = pm.create_packet("read_prog", title=choice)
    program_content_packet = calc.get_program_content(packet)
    content = pm.parse_program_content(program_content_packet)
    print(f"Content of {choice}:\n{content}")

def discord_loop(interval_seconds=60):
    global discord_message_out
    global discord_message_in
    discord_message_out = None
    discord_message_in = []

    time.sleep(3)
    create_new_log()

    print("TI-84 Plus CE USB Communication Script")
    print("=====================================")
    
    # Find the device
    if not calc.find_device():
        print("\nTroubleshooting steps:")
        print("1. Install Zadig and replace the calculator's driver with libusb-win32 or WinUSB")
        print("2. Check Device Manager for the actual VID/PID of your calculator")
        print("3. Update the VID/PID values in the script if needed")
        sys.exit(1)
    
    # Setup the device
    if not calc.setup_device():
        sys.exit(1)

    
    print("\nDevice setup successful!")
    print("Initializing connection to the calculator...")

    if not calc.perform_sequence(pm.preset_packets.init):
        print("Failed to create initial usb connection...")
        sys.exit(1)
    
    print("\nInitial handshake successful!")

    i = 1

    while True:
        # Check for new messages from Discord
        if discord_message_in:
            for message in discord_message_in:
                print("\nSending Message to calculator...")
                send_program(message["title"].strip().upper(), message["text"])
                if "Comms confirmed" in message["text"]:
                    i = 12

        discord_message_in = []

        if i != 12:
            print("Checking for question in", str(interval_seconds - (i * 5)), "seconds")

        elif i == 12:
            print("Checking for question...")

            try:
                # Try to talk to the calculator
                program_names_packet = calc.get_all_program_names()
                
                
                if not program_names_packet:
                    print(f"❌ Lost connection to TI-84")
                    discord_message_out = "Lost connection with TI84"
                    break  # Stop the loop if connection is lost

                program_names = pm.parse_program_titles(program_names_packet)
                if "SEND" in program_names and "QUESTION" in program_names:
                    packet = pm.create_packet("read_prog", title="SEND")
                    program_content_packet = calc.get_program_content(packet)
                    content = pm.parse_program_content(program_content_packet)

                    if content.strip().upper() == "SEND":
                        packet = pm.create_packet("read_prog", title="QUESTION")
                        program_content_packet = calc.get_program_content(packet)
                        content = pm.parse_program_content(program_content_packet)

                        discord_message_out = content
                        send_program("SEND", "")
            except Exception as e:
                print(f"❌ Lost connection to TI-84: {e}")
                discord_message_out = "Lost connection with TI84"
                break  # Stop the loop if connection is lost

            i = 0

        time.sleep(5)
        i += 1

    

def main():

    create_new_log()

    print("TI-84 Plus CE USB Communication Script")
    print("=====================================")
    
    # Find the device
    if not calc.find_device():
        print("\nTroubleshooting steps:")
        print("1. Install Zadig and replace the calculator's driver with libusb-win32 or WinUSB")
        print("2. Check Device Manager for the actual VID/PID of your calculator")
        print("3. Update the VID/PID values in the script if needed")
        sys.exit(1)
    
    # Setup the device
    if not calc.setup_device():
        sys.exit(1)

    
    print("\nDevice setup successful!")
    print("Initializing connection to the calculator...")

    if not calc.perform_sequence(pm.preset_packets.init):
        print("Failed to create initial usb connection...")
        sys.exit(1)
    
    print("\nInitial handshake successful!")

    while True:
        print("\n=== Calculator Packet Interface ===")
        print("1. Send Variable")
        print("2. Send Program")
        print("3. Disable Exam Mode")
        print("4. List Stored Programs")
        print("5. Read a Program")
        print("6. Exit")

        choice = input("Choose an option: ")

        if choice == '1':
            send_variable()
        elif choice == '2':
            send_program()
        elif choice == '3':
            disable_exam_mode()
        elif choice == '4':
            list_programs()
        elif choice == '5':
            read_program()
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
