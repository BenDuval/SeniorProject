import difflib

def fuzzy_match(word, valid_set, cutoff=0.7):
    match = difflib.get_close_matches(word, valid_set, n=1, cutoff=cutoff)
    return match[0] if match else None

def extract_valid_command_from_stream(filepath, save_path="command.txt"):
    VALID_DESTS = {"NodeG", "Node1", "Node2"}
    VALID_CMDS = {"Master", "Slave", "Idle"}
    VALID_SRCS = {"Node1", "Node2", "NodeG"}

    try:
        with open(filepath, 'r', errors='ignore') as file:
            lines = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        return None, None, None

    for i in range(len(lines) - 2):
        dest_candidate = fuzzy_match(lines[i], VALID_DESTS)
        cmd_candidate  = fuzzy_match(lines[i + 1], VALID_CMDS)
        src_candidate  = fuzzy_match(lines[i + 2], VALID_SRCS)

        if dest_candidate and cmd_candidate and src_candidate:
            with open(save_path, 'w') as outfile:
                outfile.write(f"{dest_candidate}\n{cmd_candidate}\n{src_candidate}\n")
            return cmd_candidate, dest_candidate, src_candidate

    return None, None, None
