# Writers

scans2any supports various output formats through its writer modules. This
document describes all available writers and their specific options.

## Table of Contents
- [Common Options](#common-options): Options available for all writers
- [Aquatone](#aquatone): List of potential HTTP/HTTPS URLs with ports
- [CSV](#csv): Comma-separated values format
- [Excel](#excel): Excel spreadsheet format
- [Host](#host): Simple list of hosts
- [HTML](#html): HTML representation with styled tables
- [JSON](#json): JSON representation of the infrastructure
- [LaTeX](#latex): LaTeX tables
- [Markdown](#markdown): Markdown tables
- [Nmap](#nmap): Nmap scan script generation
- [Terminal](#terminal): Pretty terminal tables (default)
- [Typst](#typst): Typst table format
- [URL](#url): List of potential URLs for the infrastructure
- [XML](#xml): XML representation
- [YAML](#yaml): YAML representation

## Common Options


### Columns

All writers support `-c, --columns`. Use it to specify which columns to include
(IP-Addresses,Hostnames,Ports,Services,Banners,OS)

### Multi Table

Most writers support `--multi-table` to break the output up into individual
tables, where each one represents a host. This output uses the headers of the
table to show information like IP-Addresses, Hostnames, and OS where as the
body of the table contains Ports, Services and Banners.

## Aquatone

The Aquatone writer generates a list of HTTP and HTTPS URLs suitable for use
with the [Aquatone](https://github.com/shelld3v/aquatone) web screenshot
tool.

For each host and port, it generates both HTTP and HTTPS URLs:
```
http://host:port
https://host:port
```

**Example usage:**
```sh
scans2any --nmap scan.xml -w aquatone
```

## CSV

The CSV writer outputs a flattened representation of the infrastructure with one
row per service.

**Example usage:**
```sh
scans2any --nmap scan.xml -w csv -o hosts.csv
```

## Excel

The Excel writer outputs the infrastructure data in Microsoft Excel format
(.xlsx).

**Options:**
- `--flattened`: Creates a flat table with one row per service (default: False)

**Example usage:**
```sh
# Standard format with multiple values per cell
scans2any --nmap scan.xml -w excel -o infra.xlsx

# Flattened format with one row per service
scans2any --nmap scan.xml -w excel --flattened -o services.xlsx
```

When using `--multi-table` without `--flattened`, each host will be placed in
its own worksheet.

## Host

The host writer generates a simple list of all IP addresses and hostnames, one
per line. This is useful for creating target lists for other tools.

**Example usage:**
```sh
scans2any --nmap scan.xml -w host -o targets.txt
```

## HTML

The HTML writer creates a complete HTML document with styled tables representing
the infrastructure.

**Example usage:**
```sh
scans2any --nmap scan.xml -w html -o report.html
```

The HTML includes basic CSS styling for readability and can be viewed in any
browser.

## JSON

The JSON writer is the only writer where the output can also be used as the
input for a future call to scans2any. This can be useful to reuse the combined
result. See the workflow below:

Let's say you need to combine many scans, that are stored in a directory. This
can take a long time, depending on how many scans you have. Instead of using
the default terminal output let's use JSON:

`scans2any -a /path/to/all/scans -w json -o combined_infra.json`

Once this is done, you can use the JSON file and try different output options
without having to read many files and combine a lot of information.

`scans2any --json combined_infra.json -c IP-Addresses,Services --filters service_filter --service-regex "https"`

The JSON output also is ideal if you want to create your own output format in
whatever language you prefer.

Learn more about the JSON format at [json.md](json.md).


## LaTeX

The LaTeX writer generates a complete LaTeX document with tables representing
the infrastructure.

**Example usage:**
```sh
scans2any --nmap scan.xml -w latex -o report.tex
```

The output includes a complete LaTeX document with necessary packages and
styling. To compile the document:

```sh
pdflatex report.tex
# Run twice for proper table formatting
pdflatex report.tex
```

Or simply use `latexmk`.

## Markdown

The Markdown writer creates tables in Markdown format representing the
infrastructure.

**Options:**
- `--flattened`: Creates a flat table with one row per service (default: False)
- `--merge-symbol`: Symbol to use when merging multiple values in a cell
  (default: "\<br>")

**Example usage:**
```sh
# Standard format
scans2any --nmap scan.xml -w markdown -o report.md

# Flattened format
scans2any --nmap scan.xml -w markdown --flattened -o services.md

# Custom merge symbol
scans2any --nmap scan.xml -w markdown --merge-symbol " | " -o report.md
```

## Nmap

The Nmap writer generates a shell script for running Nmap scans targeting the
discovered services.

**Options:**
- `--options-tcp`: TCP scan options for Nmap (default: "-sS -A -Pn -n -T4 -oA")
- `--options-udp`: UDP scan options for Nmap (default: "-sU -A -Pn -n -T4 -oA")

**Example usage:**
```sh
# Generate scan script with default options
scans2any --nmap scan.xml -w nmap -o rescan.sh

# Generate scan script with custom TCP options
scans2any --nmap scan.xml -w nmap --options-tcp "-sT -sV -O" -o custom_scan.sh
```

The generated script will include one line per host, with appropriate ports
included.

## Terminal

The terminal writer is the default output format and displays a nicely formatted
table in the console.

**Options:**
- `--table-fmt`: Table format for terminal output, using formats from the
  tabulate package (default: fancy\_grid)

**Example usage:**
```sh
# Default format (fancy_grid)
scans2any --nmap scan.xml

# Alternative table format
scans2any --nmap scan.xml --table-fmt github
```

Available table formats include: plain, simple, github, grid, fancy\_grid, pipe,
orgtbl, jira, presto, pretty, html, and more.

For all formats read the tabulate documentation at
[https://pypi.org/project/tabulate](https://pypi.org/project/tabulate/).

## Typst

The Typst writer creates tables in [Typst](https://typst.app/) format, a modern
markup-based typesetting system.

**Example usage:**
```sh
scans2any --nmap scan.xml -w typst -o report.typ
```

To compile the output:
```sh
typst compile report.typ
```

## URL

The URL writer generates a list of potential URLs for the infrastructure using
service names as protocols.

**Example usage:**
```sh
scans2any --nmap scan.xml -w url -o urls.txt
```

The output will contain URLs like:
```
http://example.com:80
ssh://192.168.1.1:22
```

## XML

The XML writer outputs a structured XML representation of the infrastructure.

**Example usage:**
```sh
scans2any --nmap scan.xml -w xml -o infrastructure.xml
```

## YAML

The YAML writer outputs a structured YAML representation of the infrastructure.

**Example usage:**
```sh
scans2any --nmap scan.xml -w yaml -o infrastructure.yml
```