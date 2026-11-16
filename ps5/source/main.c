#include <ps5/payload_main.h>

#include <stdio.h>
#include <string.h>

#define INPUT_PATH "/data/PS5ErrorAnalyzer/input.log"
#define REPORT_PATH "/data/PS5ErrorAnalyzer/report.txt"
#define LINE_CAPACITY 2048

static unsigned char ascii_lower(unsigned char value) {
    if (value >= 'A' && value <= 'Z') return (unsigned char)(value + ('a' - 'A'));
    return value;
}

static int contains_case_insensitive(const char *text, const char *needle) {
    size_t needle_length = strlen(needle);
    if (needle_length == 0) return 1;

    for (; *text; ++text) {
        size_t i = 0;
        while (i < needle_length && text[i] &&
               ascii_lower((unsigned char)text[i]) == ascii_lower((unsigned char)needle[i])) {
            ++i;
        }
        if (i == needle_length) return 1;
    }
    return 0;
}

static int is_insufficient_space(const char *line) {
    return contains_case_insensitive(line, "insufficient free space") ||
           contains_case_insensitive(line, "not enough free space") ||
           contains_case_insensitive(line, "not enough space") ||
           contains_case_insensitive(line, "no space left");
}

static void write_report(FILE *out, const char *source, unsigned int line_number,
                         const char *original_line) {
    fprintf(out, "Finding: Installation may have run out of space\n");
    fprintf(out, "Confidence: medium\n");
    fprintf(out, "Source: %s, line %u\n", source, line_number);
    fprintf(out, "Original message: %s", original_line);
    if (original_line[0] && original_line[strlen(original_line) - 1] != '\n') fputc('\n', out);
    fprintf(out, "Matched rule: log.install.insufficient_space.v1\n");
    fprintf(out, "Rule reason: Matched an explicit insufficient-space phrase.\n");
    fprintf(out, "Possible causes:\n");
    fprintf(out, "- Available space was below the installer's requirement.\n");
    fprintf(out, "- Temporary install data may have reduced available space.\n");
    fprintf(out, "Recommended checks:\n");
    fprintf(out, "- Check available storage in the console settings.\n");
    fprintf(out, "- Retry only after confirming enough free space for the install.\n");
    fprintf(out, "Missing information:\n");
    fprintf(out, "- Available free space at the time of failure.\n");
    fprintf(out, "- Package size and required temporary space.\n");
    fprintf(out, "- Whether temporary data from a previous attempt remained.\n\n");
}

int payload_main(struct payload_args *args) {
    (void)args;
    FILE *input = fopen(INPUT_PATH, "r");
    if (!input) {
        printf("PS5 Error Analyzer: cannot open %s\n", INPUT_PATH);
        printf("Create /data/PS5ErrorAnalyzer and copy a log there as input.log.\n");
        return 1;
    }

    FILE *report = fopen(REPORT_PATH, "w");
    if (!report) {
        fclose(input);
        printf("PS5 Error Analyzer: cannot write %s\n", REPORT_PATH);
        return 1;
    }

    fprintf(report, "PS5 Error Analyzer 0.1.0\n");
    fprintf(report, "Input: %s\n\n", INPUT_PATH);
    char line[LINE_CAPACITY];
    unsigned int line_number = 0;
    unsigned int findings = 0;
    unsigned int skipped_lines = 0;
    while (fgets(line, sizeof(line), input)) {
        ++line_number;
        size_t length = strlen(line);
        if (length > 0 && line[length - 1] != '\n' && !feof(input)) {
            int ch;
            while ((ch = fgetc(input)) != '\n' && ch != EOF) {}
            ++skipped_lines;
            continue; /* Oversized lines are skipped so evidence and line numbers stay honest. */
        }
        if (is_insufficient_space(line)) {
            write_report(report, INPUT_PATH, line_number, line);
            ++findings;
        }
    }

    if (findings == 0) {
        fprintf(report, "No bundled diagnostic rule matched.\n");
        fprintf(report, "This does not mean the log is error-free.\n");
    }
    if (skipped_lines > 0) {
        fprintf(report, "Input limitation: skipped %u line(s) longer than %u bytes.\n",
                skipped_lines, (unsigned int)(LINE_CAPACITY - 1));
    }
    fclose(input);
    fclose(report);

    printf("PS5 Error Analyzer finished: %u finding(s).\n", findings);
    printf("Report: %s\n", REPORT_PATH);
    return 0;
}

