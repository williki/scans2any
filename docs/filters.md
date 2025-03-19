# Filters

Filters in scans2any transform and clean up scan data before it's formatted for
output. They help remove unwanted information, normalize data, and enhance the
quality of the final result.

## General Usage

You can control which filters are applied using the following command-line
options:

- `--filters` - Specify a custom filter chain, overriding the defaults
- `--enable-filters` - Add additional filters to the default set
- `--disable-filters` - Disable specific filters from the default set

The default filters are:

- trash_banner
- trash_service_name
- trash_hostname
- combine_banner
- nmap_banner

Example:

```sh
# Override default filters with a custom chain
scans2any --nmap scan.xml --filters trash_banner nmap_banner

# Add additional filters to the default set
scans2any --nmap scan.xml --enable-filters empty_host

# Disable specific filters
scans2any --nmap scan.xml --disable-filters trash_banner
```

## Filter Priority

Each filter has a priority value that determines the order of execution. Filters
with lower priority values run first. This ensures that filters work together
properly when multiple filters are enabled.

## Available Filters

### empty_host

**Priority:** 4

Removes hosts that have no identified open ports or only have trivial services
like "ident".

**When to use:** When you want to exclude hosts with no meaningful services from
your results.

**How it works:** The filter removes hosts that either have no services or only
have a single service with a service name in the delete list ("", "ident").

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters empty_host
```

Before:

```
Host: 192.168.1.1
  - Port 113: ident

Host: 192.168.1.2
  - Port 80: http
  - Port 443: https
```

After:

```
Host: 192.168.1.2
  - Port 80: http
  - Port 443: https
```

### empty_service

**Priority:** 3

Removes services that don't have any identified banner or service name.

**When to use:** When you want to clean up your results by removing ports that
were found open but couldn't be identified.

**How it works:** The filter keeps only services that have either a banner or a
service name.

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters empty_service
```

Before:

```
Host: 192.168.1.1
  - Port 22: ssh
  - Port 12345: (no service name or banner)
```

After:

```
Host: 192.168.1.1
  - Port 22: ssh
```

### hostname_filter

**Priority:** 3

Filters hosts based on regex patterns matching their hostnames.

**When to use:** When you only want to see hosts with specific hostname
patterns.

**How it works:** The filter accepts regex patterns via the `--hosts-regex`
argument and keeps only hosts with hostnames matching at least one pattern.

**Example:**

```sh
scans2any --nmap scan.xml --hosts-regex ".*\.example\.com" "dev.*"
```

This will keep only hosts with hostnames that either end with `.example.com` or
start with `dev`.

### ip_port

**Priority:** 1

Filters hosts and services based on IP address ranges and port ranges.

**When to use:** When you want to focus on specific IP ranges or ports, or
exclude certain ranges.

**How it works:** The filter accepts IP and port ranges through four arguments:

- `--ip-allowlist`: Keeps only hosts in the specified IP ranges
- `--ip-blocklist`: Excludes hosts in the specified IP ranges
- `--port-allowlist`: Keeps only services with ports in the specified ranges
- `--port-blocklist`: Excludes services with ports in the specified ranges

**Example:**

```sh
# Keep only hosts in the 10.0.1.0-10.0.1.255 range with ports 80-443
scans2any --nmap scan.xml --enable-filters ip_port --ip-allowlist 10.0.1.0-10.0.1.255 --port-allowlist 80-443

# Block a specific range of IPs and ports
scans2any --nmap scan.xml --enable-filters ip_port --ip-blocklist 192.168.5.0-192.168.5.255 --port-blocklist 1-1024
```

### nmap_banner

**Priority:** 1

Formats Nmap-specific banner information in a more readable format.

**When to use:** When you have Nmap scan data and want to present banner
information in a cleaner, more consistent format.

**How it works:** The filter identifies Nmap banners (which contain keys like
"product", "version", etc.), extracts the most important information, and
reformats it to `product/version (devicetype)`.

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters nmap_banner
```

Before:

```
Host: 192.168.1.1
  - Port 80: http
    - Banner: "product: Apache version: 2.4.46 extrainfo: (Ubuntu)"
```

After:

```
Host: 192.168.1.1
  - Port 80: http
    - Banner: "Apache/2.4.46"
```

### service_filter

**Priority:** 1

Filters services based on regex patterns matching their service names.

**When to use:** When you only want to see specific types of services, e.g.,
only web services.

**How it works:** The filter accepts regex patterns via the `--service-regex`
argument and keeps only services with names matching at least one pattern.

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters service_filter --service-regex "http.*" "ftp"
```

This will keep only services with names containing "http" (like "http", "https",
"http-proxy") or exactly "ftp".

### trash_banner

**Priority:** 2

Cleans up service banners by removing common "trash" strings and duplicates.

**When to use:** When you want cleaner, more meaningful banner information in
your output.

**How it works:** The filter removes banners matching a list of common
uninformative strings (like "unknown", "Not Found", "Error"), HTTP error codes,
and removes banners that are substrings of other banners to reduce redundancy.

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters trash_banner
```

Before:

```
Host: 192.168.1.1
  - Port 80: http
    - Banner: "Not Found"
    - Banner: "Apache"
    - Banner: "Apache Web Server"
```

After:

```
Host: 192.168.1.1
  - Port 80: http
    - Banner: "Apache Web Server"
```

### trash_hostname

**Priority:** 2

Cleans up hostnames by removing redundant subdomains.

**When to use:** When you want to simplify your hostname list by removing
redundant information.

**How it works:** If a hostname is a prefix of another hostname (with a dot
following), it's considered redundant and removed. For example, if both
"example.com" and "www.example.com" are present, "example.com" will be removed
because it's a prefix of "www.example.com".

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters trash_hostname
```

Before:

```
Host: 192.168.1.1
  - Hostnames: example.com, www.example.com, mail.example.com
```

After:

```
Host: 192.168.1.1
  - Hostnames: www.example.com, mail.example.com
```

### trash_service_name

**Priority:** 2

Cleans up service names by removing uninformative names and merging related
services.

**When to use:** When you want more meaningful service names in your output.

**How it works:** The filter removes "trash" service names (like "", "unknown",
"tcpwrapped"), filters out less useful names like "www" when multiple names are
present, and combines related services like "http" and another service into
"http/service".

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters trash_service_name
```

Before:

```
Host: 192.168.1.1
  - Port 80: http, www, unknown
  - Port 443: https, ssl
```

After:

```
Host: 192.168.1.1
  - Port 80: http
  - Port 443: https/ssl
```

### use_first_entry

**Priority:** 5

Resolves multiple conflicting banners or service names by selecting only the
first one.

**When to use:** As a last resort when you have multiple conflicting pieces of
information and just want to pick one consistently.

**How it works:** For each service with multiple banners or service names, it
keeps only the first one. It also applies the same principle to OS information.

**Example:**

```sh
scans2any --nmap scan.xml --enable-filters use_first_entry
```

Before:

```
Host: 192.168.1.1
  - Port 80: http, www-http
  - OS: Windows Server 2019, Windows 10
```

After:

```
Host: 192.168.1.1
  - Port 80: http
  - OS: Windows Server 2019
```

## Filter Chain Examples

### Minimal Information

Keep only essential information:

```sh
scans2any --nmap scan.xml --filters empty_host trash_service_name trash_banner
```

### Focus on Web Services

Keep only web-related services:

```sh
scans2any --nmap scan.xml --service-regex "http.*" "https.*"
```

### Clean Output for a Specific Network

Clean output for a specific network:

```sh
scans2any --nmap scan.xml --filters trash_banner trash_hostname trash_service_name nmap_banner --ip-allowlist 192.168.1.0-192.168.1.255
```

## Creating Custom Filters

You can create your own filters by adding Python files to the
`scans2any/filters` directory. Each filter must define:

1. A `PRIORITY` constant (integer)
2. An `apply_filter` function that takes an appropriate object (Host, Service,
   or Infrastructure) and an args parameter

Optional:

- An `add_arguments` function to add command-line arguments

Example template for a custom filter:

```python
from scans2any.internal import Host

PRIORITY = 10  # Choose an appropriate priority

def add_arguments(parser):
    """Add command-line arguments for this filter."""
    parser.add_argument(
        "--my-filter-option",
        help="Description of the option",
        default="default_value",
    )

def apply_filter(host: Host, args):
    """Description of what the filter does."""
    # Filter implementation
    pass
```
