# Changelog

## [1.0.0] - 2026-03-04

### 🔥 Breaking Changes

- **Removed host_filter**: Can be replaced with the new column filter (`-C
  hostnames:<regex>`)
- **Removed service_filter**: Can be replaced with the new column filter (`-C
  services:<regex>`)

### 🚀 Features
- **Relative Columns:** You can now append or remove default columns easily via the CLI by using `+` and `-` prefixes with `-c` or `--columns` (e.g. `-c +Hostnames,-OS`).

- **Database Support:** Added `-p`/`--project` flag to automatically save and
  load parsed infrastructure data from a local SQLite database.
- **Custom Columns & Fields:** Parsers can now extract and export custom fields
  (e.g., Nessus vulnerability types, Aquatone HTTP status) using the `-c` flag.
- **Trusted Fields:** Added priority system for parsers (e.g., Bloodhound,
  NetExec, Aquatone) to prevent accurate data from being overwritten by less
  reliable scans.
- **New CLI Shorthands:** Added `-C`/`--col` for quick column regex filtering
  and `--hosts-file` for filtering by IP/hostname lists.
- **Improved `column_filter`:**
  - Negation support: `col:!regex` (or bare `!regex`) keeps only rows where
      the column does **not** match the pattern.
  - Value mode (`-Cv`/`--col-value`): global patterns must match a
      service's own fields; host-level field matches no longer carry all
      services through. Multi-value fields are trimmed to exact matches.
  - Host mode (`-Ch`/`--col-host`): keeps the entire host and all its services
      if any pattern matches.
  - Chaining multiple specs applies them as logical AND.
- **Custom Merge Rules:** Added `--merge-rules` flag to specify a YAML file with
  custom auto-merge rules, allowing users to define their own logic for merging
  services.

### ⚡ Performance

- **Faster Startup:** Deferred `pandas`/`numpy` import to inside writer
  functions (lazy import). Startup time reduced by ~50% when pandas is not
  needed (e.g., `--help`, `--version`, non-DataFrame writers).
- **Massive Speedups:** Completely rewrote the infrastructure combining and
  merging logic using Union-Find clustering and parallel processing, drastically
  reducing processing time for large datasets.
- **Internal Optimizations:** Optimized `Infrastructure.add_hosts`,
  `Host.add_services`, and `Host.remove_services` to use $O(N)$ and $O(N \cdot
  \alpha(N))$ algorithms, significantly improving performance when parsing and
  merging large scans. Optimized filters (`ip_port`, `trash_banner`) to use sets
  and efficient sorting for faster filtering. Optimized helper utilities
  (`utils.py`, `file_processing.py`) by precompiling regexes and using `rglob`
  for faster file discovery. Optimized parsers (`nmap`, `nessus`, `masscan`,
  `nxc`, `merge_file`) to batch-add services and hosts, reducing overhead and
  improving parsing speed. Optimized writers (`dataframe_creator.py`) by
  pre-calculating host-level columns and reducing redundant iterations over
  services, speeding up output generation. Optimized `main.py` and `printer.py`
  by preventing unconditional evaluation of `str(combined_infra)` in debug logs,
  saving massive string formatting overhead. Optimized `auto_merge` by
  pre-processing rules and inverting the loop to $O(H \times R)$ instead of $O(R
  \times H \times S)$.
- **Filter Optimization:** Improved performance by caching field extraction
  during column filtering.
- **Adaptive Parsing:** Automatically switches to multi-process parsing for
  large batches of files to bypass the Python GIL.

### 🌟 Improvements

- **Rich Terminal UI:** Replaced `tqdm` with `rich` for beautiful, non-blocking
  progress bars, status spinners, and terminal emulator progress integration.
- **CLI Help:** Improved `--column-regex` / `-C` help text explaining syntax,
  chaining (AND), negation, and case-insensitive matching (`(?i)` inline flag).
- **Documentation:** Cleaned up README documentation and CLI help text.
- **Auto Merge:** Added lots of auto merge rules, which should make manual
  merging much less common.

### 🛠 Internal & Fixes

- **Pydantic Models:** Refactored core data structures (`Host`, `Service`,
  `Infrastructure`) to use `pydantic` for better validation and serialization.
- **Test Suite Optimization:** Replaced out-of-process `subprocess.run` calls
  with in-process `unittest.mock.patch` mocking of `sys.argv` and standard
  streams, resulting in a ~20x speedup for the entire test suite.
- Removed unused code and functions across the project (e.g., `IndexedKey`,
  `joinit`, `is_valid_ipv4`, `no_common_elements`, `list_projects`,
  `HostsUnionError`, `MergeHostsError`, `union_with_infrastructure`) to improve
  maintainability.
- Extracted Union-Find clustering logic into a reusable `cluster_hosts` function
  in `clustering.py` to reduce duplication and improve readability.
- Optimized `cluster_hosts` to use single-pass union-on-the-fly instead of a
  two-pass token map approach, reducing memory usage (`dict[str, int]` vs
  `dict[str, list[int]]`) and improving speed by ~2x at 20k hosts. Removed
  ineffective `ThreadPoolExecutor` parallel path that was slower than sequential
  due to the GIL.
- Simplified `add_host` by removing duplicated trusted-field propagation. Kept
  fast O(n) linear scan for single-host additions to avoid `cluster_hosts`
  overhead on per-host parser calls.
- Deduplicated `add_hosts` cluster-processing loop — three near-identical
  try/except blocks collapsed into one.
- Simplified `merge_with_infrastructure` by collapsing three early-return
  branches with repeated `auto_merge` calls into a single flat control flow.
- Updated project dependencies, replacing `tqdm` with `rich` and adding
  `pydantic`.
- Migrated to `uv` dependency groups for development dependencies.
