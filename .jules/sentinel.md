## 2025-06-07 - [Prompt XML Injection]
**Vulnerability:** In prompt generation (`prompt.py`), `skill_md_path` was interpolated directly into an XML element without being escaped. An attacker who controls directory names could include ta[...]
**Learning:** Even internal file paths must be considered potentially tainted if they include portions controlled by external users/inputs (such as downloaded skill repositories).
**Prevention:** Always use `html.escape()` or dedicated XML building tools to serialize paths, names, and descriptions when constructing LLM prompts using XML.

## 2025-06-08 - [Unbounded File Read DoS & Stack Trace Leak]
**Vulnerability:** In `parser.py` and `validator.py`, the CLI utility read files using `Path.read_text()` without limits or proper exception handling. Maliciously crafted files (e.g., massive size,[...])
**Learning:** `Path.read_text()` is dangerous for reading external user-supplied files because it loads everything into memory and doesn't handle OS-level errors securely. CLI applications must fai[...]
**Prevention:** Use bounded file reads with `open()`, set explicit read limits (e.g., 1MB), and catch low-level exceptions like `OSError` and `UnicodeDecodeError` to return sanitized error messages[...]
## 2025-06-09 - [Path Leakage in Error Handling]
**Vulnerability:** Path leakage via `OSError` messages and `skill_dir` representations exposing internal server structure in error output.
**Learning:** Exception handling for missing or unreadable files can unintentionally leak full system paths if the raw exception or absolute path is formatted into user-facing output.
**Prevention:** Sanitize error messages by relying solely on the final path component (`skill_dir.name`) and restricting error string representation to safe subsets like `e.strerror`.
## 2025-06-29 - [Type Confusion via YAML Metadata Parsing]
**Vulnerability:** The SKILL.md parser did not validate the type of the `metadata` field. If an attacker provided a YAML list or string instead of a map, it could lead to downstream application crashes (Denial of Service) due to type confusion.
**Learning:** Metadata fields parsed from external YAML files must be strictly type-validated before being processed.
**Prevention:** Always check `isinstance(field, dict)` for the metadata field parsed from untrusted sources to ensure it's a valid mapping.

## 2025-06-10 - [CLI Path and Stack Trace Exposure]
**Vulnerability:** The CLI commands leaked stack traces when unexpected exceptions occurred, and `validate_cmd` printed the raw, potentially absolute file path of the skill being validated.
**Learning:** Raw paths can expose internal directory structures of the system running the validation. Uncaught exceptions can expose the underlying library's call stack to the end user.
**Prevention:** Wrap CLI command logic in broad `Exception` try/catch blocks with sanitized error messages. When outputting user paths, use `path.name` or `path.resolve().name` to print only the final component.
