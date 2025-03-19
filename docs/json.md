## scans2any JSON Format

The JSON writer creates a JSON representation of an infrastructure
See below an example, showing the structure of the resulting JSON

```json
{
  "192.168.1.1": {
    "hostnames": [
       "sshserver"
    ],
    "tcp_ports": {
      "22": {
        "service_names": [
          "ssh"
        ],
        "banners": [
          "Dropbear sshd"
        ]
      }
    },
    "udp_ports": {},
    "os": [
      "linux"
    ]
  },
  "unknown_0": { /* this host had no address */
    "hostnames": [],
    "tcp_ports": {
      "22": {
        "service_names": [
          "ssh"
        ],
        "banners": [
          "Dropbear sshd"
        ]
      }
    },
    "udp_ports": {},
    "os": [
      "linux"
    ]
  }
}
```
