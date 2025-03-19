# Test Data
Data has been generated using the following commands:

- Nmap:
```bash
sudo nmap -sV -O --min-rate 10000 -oA acme_intern 192.168.1.0/24
```

- Aquatone:
```bash
cat ../nmap/acme_intern.xml | aquatone -nmap
```

- Nessus:
Exported `acme Intern` scan, of new server infrastructure (08/2023).
