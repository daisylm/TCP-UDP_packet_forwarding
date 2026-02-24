import json
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

# LOAD DATA

def load_data(filename):

    records = []

    with open(filename) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except:
                continue

    return records


# CONVERT BANDWIDTH STRING → Mbps (numeric)

def parse_bandwidth(bw):

    if bw.endswith("M"):
        return float(bw[:-1])

    if bw.endswith("K"):
        return float(bw[:-1]) / 1000

    if bw.endswith("G"):
        return float(bw[:-1]) * 1000

    return float(bw)


# ==================================================
# SPLIT SUCCESS / FAILURE
# ==================================================
def split_records(records):

    success = [r for r in records if r.get("status") == "success"]
    failure = [r for r in records if r.get("status") == "failure"]

    return success, failure


# ==================================================
# GROUP SUCCESS BY BANDWIDTH
# ==================================================
def group_by_bandwidth(records):

    data = defaultdict(list)

    for r in records:
        bw = parse_bandwidth(r["bandwidth"])
        data[bw].append(r)

    return data


# ==================================================
# CPU UTILIZATION
# ==================================================
def compute_cpu_percent(samples):

    valid = [
        s for s in samples
        if "cpu_counters" in s.get("metrics", {})
    ]

    if len(valid) < 2:
        return 0

    first = valid[0]["metrics"]["cpu_counters"]
    last = valid[-1]["metrics"]["cpu_counters"]

    idle_diff = last["idle"] - first["idle"]

    total_first = sum(first.values())
    total_last = sum(last.values())

    total_diff = total_last - total_first

    if total_diff <= 0:
        return 0

    return 100 * (1 - idle_diff / total_diff)


# ==================================================
# PACKETS PER SECOND (router)
# ==================================================
def compute_pps(samples):

    valid = [
        s for s in samples
        if "interfaces" in s.get("metrics", {})
    ]

    if len(valid) < 2:
        return 0

    first = valid[0]["metrics"]["interfaces"]
    last = valid[-1]["metrics"]["interfaces"]

    total_packets = 0

    for iface in first:
        total_packets += (
            last[iface]["rx_packets"] -
            first[iface]["rx_packets"]
        )

    duration = len(valid)

    if duration == 0:
        return 0

    return total_packets / duration


# ==================================================
# PLOT 1 — THROUGHPUT vs BANDWIDTH
# ==================================================
def plot_throughput(data):

    bws = sorted(data.keys())

    avg_tp = [
        sum(r["throughput_bps"] for r in data[bw]) / len(data[bw])
        for bw in bws
    ]

    plt.figure()
    plt.plot(bws, avg_tp, marker="o")

    plt.xlabel("Offered Bandwidth (Mbps)")
    plt.ylabel("Throughput (bps)")
    plt.title("UDP Throughput vs Offered Bandwidth")
    plt.grid(True)


# ==================================================
# PLOT 2 — PACKET LOSS %
# ==================================================
def plot_loss(data):

    bws = sorted(data.keys())

    loss = [
        sum(r["lost_percent"] for r in data[bw]) / len(data[bw])
        for bw in bws
    ]

    plt.figure()
    plt.plot(bws, loss, marker="o", color="red")

    plt.xlabel("Offered Bandwidth (Mbps)")
    plt.ylabel("Packet Loss (%)")
    plt.title("Packet Loss vs Bandwidth")
    plt.grid(True)


# ==================================================
# PLOT 3 — JITTER
# ==================================================
def plot_jitter(data):

    bws = sorted(data.keys())

    jitter = [
        sum(r["jitter_ms"] for r in data[bw]) / len(data[bw])
        for bw in bws
    ]

    plt.figure()
    plt.plot(bws, jitter, marker="o", color="orange")

    plt.xlabel("Offered Bandwidth (Mbps)")
    plt.ylabel("Jitter (ms)")
    plt.title("Jitter vs Bandwidth")
    plt.grid(True)


# ==================================================
# PLOT 4 — CPU USAGE
# ==================================================
def plot_cpu(data):

    bws = sorted(data.keys())

    cpu = []

    for bw in bws:

        values = [
            compute_cpu_percent(r["router_samples"])
            for r in data[bw]
        ]

        cpu.append(sum(values) / len(values))

    plt.figure()
    plt.plot(bws, cpu, marker="o")

    plt.xlabel("Offered Bandwidth (Mbps)")
    plt.ylabel("CPU Usage (%)")
    plt.title("Router CPU vs Bandwidth")
    plt.grid(True)


# ==================================================
# PLOT 5 — PACKETS PER SECOND
# ==================================================
def plot_pps(data):

    bws = sorted(data.keys())

    pps = []

    for bw in bws:

        values = [
            compute_pps(r["router_samples"])
            for r in data[bw]
        ]

        pps.append(sum(values) / len(values))

    plt.figure()
    plt.plot(bws, pps, marker="o")

    plt.xlabel("Offered Bandwidth (Mbps)")
    plt.ylabel("Packets per Second")
    plt.title("Packet Rate vs Bandwidth")
    plt.grid(True)


# ==================================================
# PLOT 6 — SUCCESS RATE
# ==================================================
def plot_success_rate(records):

    counts = defaultdict(lambda: {"ok": 0, "total": 0})

    for r in records:

        bw = parse_bandwidth(r.get("bandwidth", "0M"))
        counts[bw]["total"] += 1

        if r["status"] == "success":
            counts[bw]["ok"] += 1

    bws = sorted(counts.keys())

    rates = [
        counts[bw]["ok"] / counts[bw]["total"]
        for bw in bws
    ]

    plt.figure()
    plt.plot(bws, rates, marker="o")

    plt.xlabel("Bandwidth (Mbps)")
    plt.ylabel("Success Rate")
    plt.title("Feasibility vs Bandwidth")
    plt.ylim(0, 1.05)
    plt.grid(True)
    
def plot_failures(failure):

    errors = Counter(
        r.get("error", "unknown")
        for r in failure
    )

    if not errors:
        return

    plt.figure()
    plt.bar(errors.keys(), errors.values())

    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Occurrences")
    plt.title("Failure Type Distribution")
    plt.grid(True)


# MAIN
def main():

    records = load_data("udp_results.jsonl")

    success, failure = split_records(records)

    data = group_by_bandwidth(success)

    plot_throughput(data)
    plot_loss(data)
    plot_jitter(data)
    plot_cpu(data)
    plot_pps(data)
    plot_success_rate(records)
    plot_failures(failure)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()