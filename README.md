# wifi-scout

> CLI tool that benchmarks and logs WiFi quality across locations with exportable reports

---

## Installation

```bash
pip install wifi-scout
```

Or install from source:

```bash
git clone https://github.com/yourname/wifi-scout.git && cd wifi-scout && pip install .
```

---

## Usage

Run a benchmark at your current location:

```bash
wifi-scout scan --location "Office - Floor 2"
```

Log multiple readings and export a report:

```bash
wifi-scout scan --location "Coffee Shop" --interval 30 --count 10
wifi-scout report --format csv --output results.csv
```

View a summary of all logged sessions:

```bash
wifi-scout history
```

**Example output:**

```
Location: Office - Floor 2
Signal Strength: -52 dBm  (Good)
Download:        87.4 Mbps
Upload:          43.1 Mbps
Latency:         11 ms
Logged at:       2024-06-10 14:32:05
```

---

## Features

- Benchmark signal strength, speed, and latency
- Tag readings by location for easy comparison
- Export reports as CSV or JSON
- View historical session logs in the terminal

---

## License

This project is licensed under the [MIT License](LICENSE).