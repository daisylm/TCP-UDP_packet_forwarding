import subprocess
import json
import time
from datetime import datetime
from itertools import product


class UDPBenchmark:

    def __init__(self, server_ip, router_ip, ssh_user):

        self.server_ip = server_ip
        self.router_ip = router_ip
        self.ssh_user = ssh_user

        # UDP CONTROL PARAMETERS

        # Offered load 
        self.bandwidth_values = [
            "30M","32M", "34M", "40M", "42M", "50M"
        ]

        # Packet size 
        self.length_values = [256, 512, 1024, 1400]

        # Optional parallel streams
        self.streams_values = [1]

        self.duration = 30
        self.repeats = 3

        # Router monitoring interval
        self.sample_interval = 5

        # Cooling periods
        self.cooldown_success = 30
        self.cooldown_failure = 90

        # Timeout margin
        self.timeout_margin = 30

        # Output file
        self.output_file = "udp_results.jsonl"

    # ROUTER METRICS VIA SSH
    def get_router_metrics(self):

        cmd = (
            "cat /proc/stat | head -n1; "
            "cat /proc/net/dev; "
            "cat /proc/meminfo | head -n5; "
            "cat /proc/loadavg"
        )

        ssh_cmd = [
            "ssh",
            "-i", "/home/vagrant/router_key",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{self.ssh_user}@{self.router_ip}",
            cmd
        ]

        res = subprocess.run(ssh_cmd, capture_output=True, text=True)

        if res.returncode != 0 or not res.stdout:
            return {"ssh_error": res.stderr.strip()}

        return self.parse_router_output(res.stdout)

    # PARSE ROUTER OUTPUT
    def parse_router_output(self, output):

        lines = output.splitlines()

        try:
            # CPU counters
            cpu_parts = lines[0].split()
            cpu_fields = [
                "user", "nice", "system", "idle",
                "iowait", "irq", "softirq", "steal"
            ]

            cpu = {
                cpu_fields[i]: int(cpu_parts[i + 1])
                for i in range(len(cpu_fields))
                if i + 1 < len(cpu_parts)
            }

            #Interface stats
            iface_data = {}

            for line in lines:
                if ":" in line and line.strip().startswith(("eth", "en", "ens")):

                    name, stats = line.split(":")
                    name = name.strip()

                    if name.startswith("lo"):
                        continue

                    fields = stats.split()

                    if len(fields) >= 12:
                        iface_data[name] = {
                            "rx_bytes": int(fields[0]),
                            "rx_packets": int(fields[1]),
                            "rx_drop": int(fields[3]),
                            "tx_bytes": int(fields[8]),
                            "tx_packets": int(fields[9]),
                            "tx_drop": int(fields[11])
                        }

            #Load average
            load_avg = float(lines[-1].split()[0])

            return {
                "cpu_counters": cpu,
                "interfaces": iface_data,
                "load_avg": load_avg
            }

        except Exception as e:
            return {"parse_error": str(e)}

    # SAVE RESULT IMMEDIATELY
    def append_result(self, result):

        with open(self.output_file, "a") as f:
            f.write(json.dumps(result) + "\n")

    # RUN SINGLE UDP TEST
    def run_single_test(self, bandwidth, length, streams, repeat):

        test_id = f"B{bandwidth}; L{length}; P{streams}; R{repeat}"
        print(f"\nTest : {test_id}")

        cmd = [
            "iperf3",
            "-c", self.server_ip,
            "-u",                 # UDP MODE
            "-b", bandwidth,      # Offered load
            "-l", str(length),    # Packet size
            "-P", str(streams),
            "-t", str(self.duration),
            "-J"
        ]

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        samples = []
        start_time = time.time()
        max_time = self.duration + self.timeout_margin

        #Monitor router during test 
        while proc.poll() is None:

            if time.time() - start_time > max_time:
                proc.kill()
                stdout, stderr = proc.communicate()

                return {
                    "test_id": test_id,
                    "status": "failure",
                    "error": "timeout",
                    "stderr": stderr,
                    "timestamp": datetime.now().isoformat()
                }

            snapshot = self.get_router_metrics()

            samples.append({
                "timestamp": datetime.now().isoformat(),
                "metrics": snapshot
            })

            time.sleep(self.sample_interval)

        stdout, stderr = proc.communicate()

        # PARSE IPERF JSON (UDP FORMAT)
        try:
            data = json.loads(stdout)
        except:
            return {
                "test_id": test_id,
                "status": "failure",
                "error": "Invalid JSON output",
                "raw_output": stdout,
                "stderr": stderr,
                "timestamp": datetime.now().isoformat()
            }

        if "error" in data:
            return {
                "test_id": test_id,
                "status": "failure",
                "error": data["error"],
                "stderr": stderr,
                "timestamp": datetime.now().isoformat()
            }

        if "end" not in data or "sum" not in data["end"]:
            return {
                "test_id": test_id,
                "status": "failure",
                "error": "Missing UDP performance data",
                "stderr": stderr,
                "timestamp": datetime.now().isoformat()
            }

        summary = data["end"]["sum"]

        return {
            "test_id": test_id,
            "status": "success",

            # Test parameters
            "bandwidth": bandwidth,
            "packet_length": length,
            "streams": streams,
            "repeat": repeat,
            "duration": self.duration,

            # UDP performance metrics
            "throughput_bps": summary.get("bits_per_second", 0),
            "jitter_ms": summary.get("jitter_ms", 0),
            "lost_packets": summary.get("lost_packets", 0),
            "lost_percent": summary.get("lost_percent", 0),
            "packets": summary.get("packets", 0),

            # Router telemetry
            "router_samples": samples,

            "timestamp": datetime.now().isoformat()
        }

    # RUN FULL EXPERIMENT
    def run(self):

        for bandwidth, length, streams in product(
            self.bandwidth_values,
            self.length_values,
            self.streams_values
        ):
            for r in range(1, self.repeats + 1):

                result = self.run_single_test(
                    bandwidth, length, streams, r
                )

                self.append_result(result)

                if result["status"] == "failure":
                    print("⚠️ Failure — extended cooldown")
                    time.sleep(self.cooldown_failure)
                else:
                    time.sleep(self.cooldown_success)

        print("\nAll UDP tests completed safely.")

# MAIN
if __name__ == "__main__":

    bench = UDPBenchmark(
        server_ip="192.168.20.10",
        router_ip="192.168.10.1",
        ssh_user="vagrant"
    )

    bench.run()
