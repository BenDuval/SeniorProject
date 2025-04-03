import sys

def set_command(destination, command, source):
    """Saves the command information to command.txt with each value on a separate line."""
    with open("command.txt", "w") as file:
        file.write(f"{destination}\n{command}\n{source}\n")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python set_command.py <destination> <command> <source>")
        sys.exit(1)

    destination = sys.argv[1]
    command = sys.argv[2]
    source = sys.argv[3]

    set_command(destination, command, source)
    print(f"Command saved:\n{destination}\n{command}\n{source}")
