import re
import os

def extract_command(input_path, output_path):
    if not os.path.exists(input_path):
        return False

    with open(input_path, 'r', errors='ignore') as file:
        content = file.read()

    # Find all 512-A blocks (exactly 512)
    blocks = [match.span() for match in re.finditer(r'A{512,}', content)]

    for i in range(len(blocks) - 1):
        _, end_first = blocks[i]
        start_second, _ = blocks[i + 1]
        message = content[end_first:start_second].strip()
        
        print(f"Found {len(blocks)} A blocks:")
        for i, (start, end) in enumerate(blocks):
            print(f"  Block {i}: length={end - start} chars")


        # Check that message doesn't contain another A block ≥ 10 (or whatever size you define)
        if re.search(r'A{10,}', message):
            continue  # Skip this pair

        if message:
            with open(output_path, 'w') as output_file:
                output_file.write(message)
            return True

    print("No clean messages found between valid 512A blocks.")
    return False
