import re
import os

def extract_command(input_path, output_path):
    # Read the file content
    if not os.path.exists(input_path):
        return False

    with open(input_path, 'r', errors='ignore') as file:
        content = file.read()

    # Find all exact 512-'A' blocks
    blocks = [match.span() for match in re.finditer(r'(?<!A)A{512}(?!A)', content)]

    for i in range(len(blocks) - 1):
        _, end_first = blocks[i]
        start_second, _ = blocks[i + 1]
        message = content[end_first:start_second].strip()
        if message:
            with open(output_path, 'w') as output_file:
                output_file.write(message)
            return True

    print("No clean messages found between 512-'A' blocks.")
    return False
