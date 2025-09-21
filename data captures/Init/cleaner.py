import os

# === Configuration ===
base_dir = os.path.dirname(os.path.abspath(__file__))
input_folder = os.path.join(base_dir, '', 'data')
output_folder = os.path.join(base_dir, '.', 'processed')
os.makedirs(output_folder, exist_ok=True)




def clean_line(line):
    """Remove offset and trailing ASCII, return only hex part."""
    line = line[5:]  # Remove the first 5 characters
    hex_part = line.split('   ')[0]  # Split before ASCII part
    return hex_part.strip()


def extract_blocks(lines):
    """Group lines into blocks separated by empty lines."""
    blocks = []
    current_block = []

    for line in lines:
        if line.strip() == "":
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)

    return blocks


def process_block(block):
    # Combine cleaned hex bytes from all lines in this block
    hex_string = ''
    for line in block:
        cleaned = clean_line(line)
        hex_string += cleaned.replace(' ', '')

    # Remove the first 25 bytes (50 hex characters)
    if len(hex_string) <= 50:
        return ''  # Nothing left after trimming
    return hex_string[50:]


def process_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    blocks = extract_blocks(lines)

    output_lines = []
    for idx, block in enumerate(blocks):
        leftover = process_block(block)
        if leftover:
            output_lines.append(f"step-{idx+1}")
            output_lines.append(leftover)

    return '\n'.join(output_lines)


def main():
    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            processed_text = process_file(input_path)

            with open(output_path, 'w') as out_file:
                out_file.write(processed_text)

            print(f"Processed {filename} -> {output_path}")


if __name__ == '__main__':
    main()

