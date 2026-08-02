import sys

def write_large_md(filename, field):
    with open(filename, 'w') as f:
        f.write("---\n")
        f.write("name: a\n")
        f.write("description: b\n")
        f.write(f"{field}: {'c' * 200000}\n")
        f.write("---\n")
