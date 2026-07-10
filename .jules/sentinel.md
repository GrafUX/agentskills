## 2025-06-07 - [Prompt XML Injection]
**Vulnerability:** In prompt generation (`prompt.py`), `skill_md_path` was interpolated directly into an XML element without being escaped. An attacker who controls directory names could include tags like `</location><skill><name>malicious</name>...` to inject fake agent instructions or prompt escape commands.
**Learning:** Even internal file paths must be considered potentially tainted if they include portions controlled by external users/inputs (such as downloaded skill repositories).
**Prevention:** Always use `html.escape()` or dedicated XML building tools to serialize paths, names, and descriptions when constructing LLM prompts using XML.

## 2025-06-08 - [Unbounded File Read DoS & Stack Trace Leak]
**Vulnerability:** In `parser.py` and `validator.py`, the CLI utility read files using `Path.read_text()` without limits or proper exception handling. Maliciously crafted files (e.g., massive size, invalid encoding, or unreadable permissions) could cause a DoS (Out of Memory) or crash the CLI, leaking internal Python stack traces to the user/attacker via `OSError` or `UnicodeDecodeError`.
**Learning:** `Path.read_text()` is dangerous for reading external user-supplied files because it loads everything into memory and doesn't handle OS-level errors securely. CLI applications must fail gracefully and not leak their internal execution context to external users.
**Prevention:** Use bounded file reads with `open()`, set explicit read limits (e.g., 1MB), and catch low-level exceptions like `OSError` and `UnicodeDecodeError` to return sanitized error messages.
## 2025-06-09 - [Path Leakage in Error Handling]
**Vulnerability:** Path leakage via `OSError` messages and `skill_dir` representations exposing internal server structure in error output.
**Learning:** Exception handling for missing or unreadable files can unintentionally leak full system paths if the raw exception or absolute path is formatted into user-facing output.
**Prevention:** Sanitize error messages by relying solely on the final path component (`skill_dir.name`) and restricting error string representation to safe subsets like `e.strerror`.
## 2026-06-11 - [Unhandled OSError and Symlink Loop Path Leakage]
**Vulnerability:** Unhandled `OSError` (such as `PermissionError`) during initial filesystem checks (`exists()`, `is_dir()`) and `RuntimeError` from symlink loops inside `resolve()` could crash the CLI, leaking the internal Python stack trace and exact absolute server paths to the user.
**Learning:** Even simple operations like `Path.exists()` can raise exceptions like `PermissionError` on restricted parent directories, and `Path.resolve()` can hit a `RuntimeError` from a symlink loop. If these aren't caught and sanitized at the application boundaries, internal context is leaked.
**Prevention:** Wrap all path I/O operations (including exists/is_dir) and resolution in `try...except (OSError, RuntimeError)` blocks. Fail gracefully at CLI entry points by catching generic `Exception` to prevent any stray tracebacks, and use `.name` for safe error reflections.
## 2024-05-24 - Information Leakage via Error Messages
**Vulnerability:** Information leakage where internal system paths or stack traces were exposed via `str(e)` on `RuntimeError` during path operations in `src/skills_ref/parser.py` and `src/skills_ref/validator.py`.
**Learning:** `RuntimeError` during file system operations can contain sensitive internal paths or stack traces that shouldn't be exposed to external users. This occurred because `str(e)` was directly used to construct the user-facing error message.
**Prevention:** Avoid using `str(e)` directly on exceptions like `RuntimeError` from path operations; use `path.name` or generic fallback messages like "Symlink loop or unresolvable path" instead. Strictly sanitize error and exception messages.
## 2024-05-25 - Information Leakage via Unhandled Path Exceptions
**Vulnerability:** Information leakage where internal system paths or stack traces could be exposed due to unhandled exceptions (`OSError`, `RuntimeError`) during path evaluation `path.is_file()` in `cli.py`.
**Learning:** Even simple checks like `is_file()` can raise exceptions, such as a `RuntimeError` due to symlink loops or `OSError` due to permission issues. When executed outside of protected regions (like the `try` block of CLI commands), these can crash the application and leak the full stack trace to the user.
**Prevention:** Always wrap all path evaluation operations (like `is_file`, `exists`) in `try...except (OSError, RuntimeError)` blocks, even seemingly innocuous ones, to prevent unhandled exceptions from propagating to the user.
## 2025-06-20 - [Denial of Service via FIFO/Special Files]
**Vulnerability:** The application used `path.exists()` in `parser.py` before attempting to open `SKILL.md`. An attacker could provide a named pipe (FIFO) or special device file, causing the `open()` call to block indefinitely, leading to a Denial of Service.
**Learning:** `path.exists()` does not guarantee a path is a regular file. Opening special files can result in hangs or unexpected behavior.
**Prevention:** Always use `path.is_file()` when looking up files to ensure the target is a regular file before attempting to read its contents.

## 2024-06-27 - Implement String Length Limits for YAML Parsing

**Vulnerability:** The validator for SKILL.md did not impose limits on the length of strings for `license`, `allowed-tools`, and custom `metadata` dictionary keys and values. This lack of constraints could allow parsing maliciously crafted strings, leading to resource exhaustion (DoS) when manipulating those items.
**Learning:** External inputs like parsed metadata require comprehensive validation, explicitly checking length and bounds on all fields (including loosely structured dictionaries) to prevent unbounded memory allocation and CPU overhead during validation.
**Prevention:** Explicitly define maximum length limits for all expected metadata fields and enforce those limits within dedicated validation functions early in the processing pipeline. Use constraints like `MAX_METADATA_KEY_LENGTH` to safeguard against excessively long dictionary keys and values.
## 2025-07-02 - [Type Confusion DoS via Unvalidated YAML Types]
**Vulnerability:** In `parser.py`, optional metadata fields like `license`, `compatibility`, `allowed-tools`, and `metadata` were parsed directly from YAML into `SkillProperties` without type validation. If an attacker provided a list or dictionary instead of a string for these fields, downstream applications iterating over or expecting string methods (e.g., `.startswith()`) would crash, leading to a Denial of Service (DoS) via Type Confusion.
**Learning:** Even though `strictyaml` enforces basic YAML safety, without an explicit schema, it infers types based on YAML syntax (e.g., lists and dicts). Data models (like dataclasses) do not enforce types at runtime, allowing invalid types to silently bypass instantiation checks.
**Prevention:** Always enforce explicit runtime type validation for all parsed fields (e.g., `isinstance(val, str)`) before injecting them into data models to ensure downstream type safety.
## 2025-07-15 - [Third-Party Parser Bug DoS & Traceback Leak]
**Vulnerability:** The application used `strictyaml.load()` to parse SKILL.md frontmatter, expecting it to only raise `strictyaml.YAMLError` on invalid inputs. However, `strictyaml` has an internal bug where it throws an `AttributeError` instead when encountering certain invalid characters (like ANSI escape codes). This unhandled exception caused the CLI and any host applications to crash unexpectedly, leading to a Denial of Service and leaking internal Python stack traces to the user.
**Learning:** You cannot blindly trust third-party libraries to stick to their documented exception contracts, especially when parsing untrusted user input. Internal bugs in parsers can throw generic built-in exceptions like `AttributeError` or `ValueError`, bypassing specific exception handlers.
**Prevention:** When parsing untrusted data using external libraries, always include a fallback `except Exception` block (or similar broad catch) to handle unexpected internal library crashes gracefully, converting them into standard, sanitized application errors (like `ParseError`).

## 2025-07-15 - [Third-Party Parser Bug DoS & Traceback Leak Fix]
**Vulnerability:** The `strictyaml.load()` call in `parser.py` was wrapped in a broad `except Exception as e:` block which then exposed `str(e)` to the user in a `ParseError`. This could expose internal stack traces or Python built-in error messages (like `AttributeError`) when the third-party parser fails unexpectedly on maliciously crafted YAML.
**Learning:** Broad exception handling is sometimes necessary when calling third-party parsing libraries that might crash on unexpected input. However, the raw exception message of a broad exception must never be exposed to the user as it acts as an information leak.
**Prevention:** When catching broad generic exceptions for untrusted input parsing, specifically check if the exception is an instance of an expected error class (e.g., `isinstance(e, strictyaml.YAMLError)`). Expose the message only if it's the expected type; otherwise, return a safe, generic fallback message (e.g., "Unexpected parsing error") to mask internal implementation details.

## 2026-07-09 - [Resource Exhaustion via Unbounded Frontmatter]
**Vulnerability:** The SKILL.md parser did not limit the number of top-level fields or the length of keys and values in the YAML frontmatter. An attacker could provide a file with thousands of fields or megabytes of text in a single field, leading to excessive memory consumption or CPU usage during parsing and subsequent processing.
**Learning:** Even if the total file size is limited (e.g., 1MB), the internal structure of parsed data (like YAML mappings) can still cause issues if not explicitly constrained.
**Prevention:** Implement strict counts and character length limits for all parsed fields at the earliest possible stage, immediately after the raw data is loaded into a structured format.

## 2025-07-20 - [Prompt Inflation & DoS via Unbounded Metadata]
**Vulnerability:** In `parser.py`, `read_properties` parsed skill metadata without enforcing length limits. While the `validator.py` utility checked these limits, the code path used for generating LLM prompts (via `read_properties`) did not. An attacker could provide a skill with metadata fields (like `description`) approaching the 1MB file limit, leading to "Prompt Inflation" and exhausting the LLM context window.
**Learning:** Security bounds must be enforced at the data ingestion point (`read_properties`) to protect all downstream consumers, including those that might skip the full validation utility.
**Prevention:** Enforce string length limits for all metadata fields early in the parsing logic and share these constants between the parser and validator to ensure consistent security policy.
