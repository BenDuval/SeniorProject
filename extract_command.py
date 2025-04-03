import re

def extract_command():
    input_file_path = 'out.txt'
    output_file_path = 'command.txt'

    try:
        with open(input_file_path, 'r', errors='ignore') as file:
            content = file.read()
    except FileNotFoundError:
        return False  # Nothing to extract

    # Find all exact 512-'A' blocks
    blocks = [match.span() for match in re.finditer(r'(?<!A)A{512}(?!A)', content)]

    # Extract all messages between clean 512-A blocks
    messages = []
    for i in range(len(blocks) - 1):
        _, end_first = blocks[i]
        start_second, _ = blocks[i + 1]
        message = content[end_first:start_second].strip()
        if message:
            messages.append(message)

    if messages:
        with open(output_file_path, 'w') as output_file:
            output_file.write(messages[-1])  # Save most recent message only
        print(f"{len(messages)} message(s) extracted and saved to {output_file_path}.")
        return True
    else:
        print("No clean messages found between 512-'A' blocks.")
        return False

