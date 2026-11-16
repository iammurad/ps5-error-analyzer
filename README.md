# PS5 Error Analyzer

An evidence-based diagnostic tool that turns available PS5 homebrew logs and user-provided error codes into understandable findings and practical next steps.

## Project direction

The primary product is a homebrew diagnostic application for jailbroken PS5 consoles. Keep the diagnostic rules and report model separate from the PS5 interface and environment-specific collection code so they can also power a Windows companion. The current Python CLI is a development prototype for validating input parsing, rules, and traceable reports; it is not the PS5 product.

## What current sources establish

Access depends on the console firmware, jailbreak, and homebrew environment. The project must label each input by provenance and avoid implying that it can read every PS5 system log.

| Input | Current evidence | Initial support |
| --- | --- | --- |
| etaHEN logs | etaHEN documents its logs under `/data/etaHEN`; etaHEN also provides optional FTP and Klog services. | Primary candidate for on-console collection when etaHEN is present; also accept exported text logs. |
| Kernel log stream | etaHEN documents an optional Klog server (port 9081); its toolbox configuration also exposes the service. | Later, optionally import a saved Klog capture. Streaming is out of scope for the first version. |
| Homebrew crash reports | PS5_DevTools documents JSON crash reports in `/data/devtools/crashes/`, FTP retrieval, and a system error-history API in its own payload. | Prioritize documented JSON crash report import, with clear source attribution. |
| General console / retail logs | The sources above do not establish broad access to Sony's private system logs on ordinary retail consoles. | Treat as unavailable unless a supported tool documents and demonstrates a specific interface. |
| Error codes | Error-code explanations need a traceable, curated source and confidence level. | Begin with a small hand-reviewed JSON catalog; mark causes as known, likely, or unverified. |

These are capabilities of particular homebrew tools and configurations, not guarantees for every PS5 or firmware version. The analyzer should never require kernel access or alter console files.

## First working version

The target product is a homebrew diagnostic app for jailbroken PS5s. The first console-side implementation is a loader-compatible ELF payload: it reads a user-exported etaHEN text log from `/data/PS5ErrorAnalyzer/input.log` and writes a traceable TXT report to `/data/PS5ErrorAnalyzer/report.txt`. The user can transfer the log with the homebrew environment's FTP service. The payload does not patch the kernel, collect protected system logs, or alter the source log.

This ELF is an early proof of the console-side workflow, not a polished native PS5 application with a graphical interface. The public PS5Dev SDK currently targets ELF payloads and says full proper applications are not supported. The current Python CLI remains a developer/companion tool for checking structured reports and iterating on rules.

To build the console ELF, install/build the [PS5Dev PS5 SDK](https://github.com/PS5Dev/PS5SDK), CMake, Ninja, and Clang, then set `PS5SDK` to the SDK root:

```powershell
$env:PS5SDK = (Resolve-Path "C:\path\to\PS5SDK").Path
$toolchain = "$env:PS5SDK\cmake\toolchain-ps5.cmake"
cmake -S $env:PS5SDK -B "$env:PS5SDK\build-ps5" -G Ninja `
  -D CMAKE_C_COMPILER=clang -D CMAKE_CXX_COMPILER=clang++ `
  -D CMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY `
  -D "CMAKE_TOOLCHAIN_FILE=$toolchain"
cmake --build "$env:PS5SDK\build-ps5" --target ps5sdk_crt
cmake -S .\ps5 -B .\build-ps5 -G Ninja `
  -D CMAKE_C_COMPILER=clang -D CMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY `
  -D "CMAKE_TOOLCHAIN_FILE=$toolchain" -D "PS5SDK=$env:PS5SDK"
cmake --build .\build-ps5
```

The built file is [`ps5/bin/ps5_error_analyzer.elf`](ps5/bin/ps5_error_analyzer.elf). On a compatible jailbroken console, create `/data/PS5ErrorAnalyzer` using the environment's file manager or FTP, place an exported log there as `input.log`, and load the ELF through a compatible ELF loader. The report is written beside the input as `report.txt`. The SDK is a separate dependency; this repository does not redistribute it. The payload build was validated with the PS5Dev SDK toolchain, but still needs execution on a compatible console and homebrew environment.

Run the Windows developer/companion CLI with Python 3:

```powershell
python .\analyzer.py --file .\path\to\console.log
python .\analyzer.py --file .\path\to\crash-report.json --format json --output report.json
python .\analyzer.py --code "EXAMPLE-CODE"
```

It accepts a text log, structured JSON report, or manually entered code; matches conservative patterns from `data/errors.json`; and prints TXT by default or exports JSON. The bundled insufficient-space rule is a prototype pattern, not a verified PS5 error-code mapping. The initial catalog is intentionally small until traceable references and representative logs are available.

Keep parsing deterministic and offline. Avoid uploading logs, which may contain identifiers or other private data. Do not infer hardware faults, storage health, package integrity, or network causes unless the supplied evidence supports the finding.

## Evidence traceability

Traceability is a core product requirement, not optional debug output. Each finding must include:

- **Source:** original filename and, when available, input format and collector/tool provenance.
- **Location:** one-based line number and column span for text, or a JSON Pointer for structured input (for example, `/exception/message`). If a parser cannot identify a location, say so explicitly.
- **Original evidence:** exact matched error message or field value, preserved verbatim. Do not replace it with a paraphrase.
- **Matched rule:** stable rule ID, rule-set version, and a short explanation of the condition that matched.
- **Confidence:** a documented level (`high`, `medium`, or `low`) tied to evidence quality and rule specificity, not a claim of statistical probability.
- **Missing information:** the relevant context not present in the input that limits the diagnosis, such as firmware, title, install source, or surrounding log lines. Use an empty list only when the rule has no material evidence gaps.

Example JSON finding:

```json
{
  "finding_id": "install.storage.insufficient_space",
  "title": "Installation may have run out of space",
  "confidence": "medium",
  "source": {
    "filename": "install.log",
    "format": "text",
    "provenance": "user_import"
  },
  "evidence": [
    {
      "location": { "line": 42, "column_start": 1, "column_end": 39 },
      "original_message": "Install failed: insufficient free space"
    }
  ],
  "matched_rule": {
    "id": "log.install.insufficient_space.v1",
    "rule_set_version": "0.1.0",
    "reason": "Matched the explicit insufficient-space phrase in an installation failure message."
  },
  "missing_information": [
    "Available free space at the time of failure",
    "Whether temporary installation data was present"
  ]
}
```

For JSON inputs, `location` should use a JSON Pointer instead of line coordinates when the parser can identify the source field. Render the same evidence in TXT reports so a reader can find the original line or field without relying on the analyzer's interpretation.

## Current structure

```text
ps5/
  CMakeLists.txt  PS5 SDK ELF build target
  source/main.c   on-console log scan and traceable TXT report
analyzer.py       Windows companion/development CLI
data/
  errors.json curated error-code entries and rules
```

The console payload uses C and the PS5 SDK's C runtime, avoiding the unsupported C++ STL. The diagnostic rule catalog is still small and the native payload currently implements only the explicit insufficient-space text pattern. Keep the Windows companion useful for format and rule development; migrate stable parsing and report logic toward a shared C layer as the supported console environment allows.

## Initial scope boundaries

- No jailbreak, exploit, kernel patching, or firmware manipulation.
- No assumption of access to protected retail-console logs.
- No automated PKG inspection or repair in the first version.
- No uploads or community submissions until a privacy and review process exists.
- Installation and transfer diagnoses may be added as evidence-backed rules when representative logs are available.

## Research references

- [PS5Dev PS5 SDK](https://github.com/PS5Dev/PS5SDK) — current SDK status and limitations.
- [etaHEN](https://github.com/etaHEN/etaHEN) — documented log location, FTP, and Klog options.
- [PS5_DevTools](https://github.com/griches/PS5_DevTools) — homebrew crash report JSON, retrieval, and error-history interface.

Recheck these references as the homebrew ecosystem and SDK change. The project should record tested firmware, tool version, and collection method for every supported input format.

