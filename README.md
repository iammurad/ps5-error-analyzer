# PS5 Error Analyzer

A local diagnostic collector for jailbroken PS5s. It checks supported homebrew logs, matches lines against a small set of rules, and writes a report with the source and evidence for each finding.

## Choose a download

Get the files from the [latest release](https://github.com/iammurad/ps5-error-analyzer/releases/latest):

- **`.elf`** — load this with a payload manager. This is the raw payload format.
- **`.plugin`** — use this with etaHEN's plugin loader. Copy it to `/data/etaHEN/plugins/`; etaHEN can load it from its plugin menu or at startup.

Each download has a matching `.sha256` file you can use to verify it. The two formats run the same collector.

## How it works

Once loaded, the collector scans once per minute:

- `/data/etaHEN/etaHEN.log`
- `/data/etaHEN/etaHEN_crash.log`
- `/data/devtools/crashes/*.json`, if PS5_DevTools is installed

It looks for explicit phrases related to storage space, timeouts, network connection failures, and generic errors. It does not change the source logs or send data anywhere.

## Read the report

Open `/data/PS5ErrorAnalyzer/report.txt` using your usual file access method (for example, etaHEN's FTP service, if enabled). The report is refreshed after each scan.

Each finding shows the source path, line number, original matching text, rule ID, confidence, and context that is missing. The confidence describes how specific the match is; it is not a probability. A generic “error” match is only a low-confidence pointer for further investigation.

The collector also appends startup messages to `/data/PS5ErrorAnalyzer/collector.log`. If no supported logs are available, or no rule matches, the report says so. No matches do not prove the console is error-free.

## Current limits

This is an early release. It only reads the paths listed above and recognizes a small set of text patterns. It cannot read protected Sony system logs, diagnose every installation or transfer failure, or establish hardware faults. A matching line is a lead to investigate, not a confirmed cause.

The project has not been tested on every firmware, jailbreak, payload manager, or console. Back up important data and follow the instructions for your own homebrew environment.

## Build from source

The PS5 build uses the [PS5 payload SDK](https://github.com/ps5-payload-dev/sdk), [etaHEN Plugin SDK](https://github.com/etaHEN/etaHEN-Plugins), CMake, Ninja, and Clang. The GitHub Actions workflow builds both files and publishes them with checksums and a generated changelog when a new version is merged to `main`.

## License

GNU GPL version 3. See [LICENSE](LICENSE). Third-party dependencies retain their own licenses.
