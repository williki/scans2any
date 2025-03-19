# Tutorial

This guide will walk you through basic and advanced ways to use scans2any.

## Table of Contents

- [Installation Check](#installation-check): Verify your installation is working
- [Basic Examples](#basic-examples): Quick examples to get started
- [Parsers](#parsers): Available input formats
- [Writers](#writers): Available output formats and their options
- [Multi-Table](#multi-table): Generate separate tables for each host
- [Custom Columns](#custom-columns): Customize which columns appear in output
- [Merge-file](#merge-file): Resolve conflicts between different scan sources
- [Filters](#filters): Filter and transform scan data before output
- [Miscellaneous](#miscellaneous): Additional options and features

## Installation Check

To verify that your installation is functional, simply execute `scans2any`. You
should see the logo and help output.

## Basic Examples

After installing scans2any, you can use it with any scan. Let's download an
example Nmap scan:

```sh
wget https://raw.githubusercontent.com/nmap/nmap/refs/heads/master/zenmap/radialnet/share/sample/nmap_example.xml
```

To read this scan and output as JSON:

```sh
scans2any --nmap nmap_example.xml -w json
```

You can use the `-a` or `--auto` flag to automatically detect scan types in a
directory:

```sh
scans2any --auto tests/data
```

You can also combine multiple scans of the same or different types:

```sh
scans2any --nmap tcp_scan.xml --nmap udp_scan.xml --nessus vulnerabilities.nessus
```

## Parsers

scans2any supports the following input formats:

- **aquatone**: Parse Aquatone reconnaissance reports (*.json)
- **bloodhound**: Parse Bloodhound computer reports (*.json)
- **json**: Import infrastructure from JSON files (*.json)
- **masscan**: Parse Masscan port scans (*.json)
- **nessus**: Parse Nessus vulnerability reports (*.nessus)
- **nmap**: Parse Nmap port scans (*.xml)
- **nxc**: Parse NetExec/CrackMapExec database files (smb.db)
- **txt**: Parse text files for additional IP-address to hostname mappings

## Writers

scans2any can output data in many formats. Select a writer using the `-w` or
`--writer` flag:

- **aquatone**: Generate a list of potential HTTP/HTTPS URLs with ports
- **csv**: Generate a flattened CSV representation of the infrastructure
- **excel**: Output an Excel spreadsheet
- **host**: Generate a list of IPs and hostnames
- **html**: Generate an HTML representation with styled tables
- **json**: Generate a JSON representation of the infrastructure
- **latex**: Generate LaTeX tables (requires running LaTeX twice to compile
  correctly)
- **markdown**: Generate Markdown tables
- **nmap**: Generate Nmap scan scripts for discovered TCP/UDP ports
- **terminal**: Pretty print tables in the terminal (default)
- **typst**: Generate Typst table representations
- **url**: Generate a list of potential URLs for the infrastructure
- **xml**: Generate an XML representation of the infrastructure
- **yaml**: Generate a YAML representation of the infrastructure

You can see all writer-specific options with:

```sh
scans2any -W
```

For more information see [writers.md](writers.md).

### Multi-Table

By default, scans2any creates a single table for all hosts. To generate separate
tables for each host:

```sh
scans2any --nmap scan.xml --multi-table
```

This is especially useful for HTML, Markdown, and terminal output when you have
many hosts.

### Custom Columns

You can specify which columns to include in your output using the `-c` or
`--columns` flag:

```sh
scans2any --nmap scan.xml -c "IP-Addresses,Ports,Services"
```

Available columns are: IP-Addresses, Hostnames, Ports, Services, Banners, OS.

## Merge-file

scans2any combines different scans into one infrastructure, which can then be
written to an output format. Sometimes issues arise that cannot be resolved
automatically. In this case, scans2any creates a file called `MERGE_FILE.yaml`.
This file contains all the conflicting elements of the infrastructure. You can
edit the merge-file to resolve the conflicts manually, and in a second call, use
the merge-file to create a conflict-free result.

### Example of Using Merge Files

Let's demonstrate this with an example:

First, let's create two conflicting infrastructures. This can be done with
scans, but we'll create two JSON files for simplicity:

**one.json**:
```json
{ "1.1.1.1":{ "tcp_ports":{ "22":{ "service_names":[ "ssh" ] } } } }
```

**two.json**:
```json
{ "1.1.1.1":{ "tcp_ports":{ "22":{ "service_names":[ "openssh" ] } } } }
```

These two files describe the same host with the same service, but with different
service names. Multiple service names for one service are not permitted, which
creates a conflict. Running scans2any will create a merge-file for manual
conflict resolution:

```sh
scans2any --json one.json --json two.json
[...]
Checking for Remaining Conflicts
[ ! ] Conflicts found in infrastructure.
[ ! ] Merge file written for manual edit: MERGE_FILE.yaml
[ ! ] Use merge file with '--merge-file filename' to resolve conflicts
```

Now edit `MERGE_FILE.yaml` to resolve the conflict. In this case, simply remove
either the line with `- ssh` or `- openssh`.

Run scans2any again, this time specifying the merge-file:

```sh
scans2any --json one.json --json two.json --merge-file MERGE_FILE.yaml
```

No conflicts will occur, and the output will be displayed.

## Filters

Filters let you transform and clean up your scan data before output. They can
remove unwanted information, normalize data, or enhance the output.

### Available Filters

scans2any includes the following filters by default:

- **trash_banner**: Removes common garbage strings from banners
- **trash_service_name**: Normalizes service names
- **trash_hostname**: Removes low-quality hostnames
- **combine_banner**: Combines similar banners to reduce redundancy
- **nmap_banner**: Formats Nmap-specific banner information nicely

You can see all available filters with:

```sh
scans2any -L
```

### Customizing Filters

You can override the default filter chain:

```sh
scans2any --nmap scan.xml --filters trash_banner nmap_banner
```

Add additional filters to the default set:

```sh
scans2any --nmap scan.xml --enable-filters trash_hostname
```

Or disable specific filters:

```sh
scans2any --nmap scan.xml --disable-filters nmap_banner
```

For more detailed information about each filter, see [filters.md](filters.md).

## Miscellaneous

### Ignoring Conflicts

If you don't care about resolving conflicts:

```sh
scans2any --nmap scan1.xml --nmap scan2.xml --ignore-conflicts
```

### Disabling Auto-Merge

To disable automatic conflict resolution:

```sh
scans2any --nmap scan.xml --no-auto-merge
```

### Output to File

To save the output to a file instead of displaying it in the terminal:

```sh
scans2any --nmap scan.xml -w json -o result.json
```

### Verbosity Levels

For more information during processing:

```sh
scans2any --nmap scan.xml -v
```

For debug output:

```sh
scans2any --nmap scan.xml -vv
```

### Quiet Mode

To suppress all output except errors:

```sh
scans2any --nmap scan.xml -q
```
