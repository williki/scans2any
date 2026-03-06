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
written to an output format. To achieve this, the tool detects and resolves
conflicting information automatically. Sometimes, however, conflicts arise that
cannot be resolved automatically. In this case, scans2any creates a file called
`MERGE_FILE.yaml`. This file contains all the conflicting elements of the
infrastructure. You can edit the merge-file to resolve the conflicts manually,
and in a second call, use the merge-file to create a conflict-free result.

In case of unresolved conflicts, scans2any also creates a buffer file called
`BUFFER_FILE.json`. This file contains intermediary results up until the
conflict. After resolving the issues inside the merge-file, you can use the
buffer-file as input to speed up operation. Details are explained in the
example.

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
scans2any --json one.json two.json
[...]
Checking for Remaining Conflicts
[ ! ] Conflicts found in infrastructure.
[ ! ] One or multiple unresolvable conflicts have been identified. A Mergefile has been written to 'MERGE_FILE.yaml' and a JSON Bufferfile has been written to 'BUFFER_FILE.json'.
Please edit the Mergefile to resolve the issues and then continue with: scans2any --merge-file MERGE_FILE.yaml --json BUFFER_FILE.json.
For further documentation refer to: https://github.com/softScheck/scans2any/blob/main/docs/tutorial.md#merge-file
```

Now edit `MERGE_FILE.yaml` to resolve the conflict. In this case, simply remove
either the line with `- ssh` or `- openssh`. A buffer file called
`BUFFER_FILE.json` was also created (the path to the buffer-file can be
different. Pay attention to the output of your call to scans2any). It contains
the entire infrastructure including conflicts. It is not meant to be edited,
simply use it when the conflicts in the merge-file have been resolved. The path
of the buffer-file can be specified using the `--buffer` flag.

Run scans2any again, this time specifying the merge-file and the buffer-file:

```sh
scans2any --json BUFFER_FILE.json --merge-file MERGE_FILE.yaml
```

No conflicts will occur, and the output will be displayed.

Alternatively you can repeat the same call as previously, adding the merge-file.

```sh
scans2any --json one.json two.json --merge-file MERGE_FILE.yaml
```

### Benefits and downsides of the buffer-file

When scans2any realizes that there are conflicts it cannot resolve
automatically, it has already done a lot of work reading, parsing and combining
scan results. The buffer-file stores all those results, making them usable on
subsequent execution. So, the buffer-file makes the subsequent execution faster.

However, there are scenarios where not using the buffer-file might be
preferable:

Let's imagine you want to explain to someone else how a specific result has
been created. If they have the scans, you just need to give them the call that
does not use the buffer-file and give them the used merge-file. Then they can
not only recreate the result, but they can also see what scan files were used. The
buffer-file only contains the information contained in the scans; it does not
store its origins.

Or imagine a scenario where your scan files are constantly changing. Having one
call that always takes in the current state of affairs while also resolving
known conflicts is useful. The buffer-file can only contain information that
was present when it was created.

In short: Using the buffer-file leads to faster results; not using the buffer-file
is more verbose. However, the results are the same given the same input.

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
