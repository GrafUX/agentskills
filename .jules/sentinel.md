# Sentinel Security Incident Log

## 2025-06-19 - [Denial of Service via FIFO/Device File Blocking]

**Vulnerability:** The application used `path.exists()` in `parser.py` before attempting to open `SKILL.md`. An attacker could provide a named pipe (FIFO) or special device file, causing the `open()` call to block indefinitely, leading to a Denial of Service.

**Learning:** `path.exists()` does not guarantee a path is a regular file. Opening special files can result in hangs or unexpected behavior.

**Prevention:** Always use `path.is_file()` when looking up files to ensure the target is a regular file before attempting to read its contents.

## 2025-06-21 - [Denial of Service via Unbounded Metadata String Lengths]

**Vulnerability:** The application parsed and accepted metadata fields (`license`, `allowed-tools`) from `SKILL.md` frontmatter without enforcing maximum string length limits during validation in `validator.py`. An attacker could supply arbitrarily large strings, leading to excessive memory consumption and CPU exhaustion during serialization or processing down the line.

**Learning:** Even fields that are generally harmless like strings need explicit upper bounds to prevent Denial of Service (DoS) attacks via resource exhaustion, especially when the input originates from external, untrusted sources (e.g., downloaded skill repositories).

**Prevention:** Always enforce maximum string length limits on all metadata fields. Add constant boundary definitions (e.g., `MAX_LICENSE_LENGTH = 100`) and explicitly validate inputs against these limits early in the processing pipeline.
