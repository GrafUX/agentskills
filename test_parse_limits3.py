def write_large_md2(filename):
    with open(filename, 'w') as f:
        f.write("---\n")
        f.write("name: a\n")
        f.write("description: b\n")
        f.write("metadata:\n")
        f.write(f"  k: {'c' * 200000}\n")
        f.write("---\n")
