import json
import matplotlib.pyplot as plt
from collections import defaultdict, Counter



def load_data(filename):

    records = []

    with open(filename) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except:
                continue

    return records



def success_failure(records):

    success = [r for r in records if r.get("status") == "success"]
    failure = [r for r in records if r.get("status") == "failure"]

    return success, failure


def summarize_by_test(records):

    data = defaultdict(list)

    for r in records:

        key = r.get("test_id", "unknown")

        data[key].append({
            "sender": r.get("throughput_sender_bps", 0),
            "receiver": r.get("throughput_receiver_bps", 0),
            "retrans": r.get("retransmissions", 0),
            "samples": r.get("router_samples", [])
        })

    return data


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


def plot_throughput(data, failures):

    tests = sorted(set(data.keys()) |
                   set(r.get("test_id") for r in failures))

    sender_avg = []
    receiver_avg = []

    for t in tests:

        if t in data:
            sender_avg.append(
                sum(d["sender"] for d in data[t]) / len(data[t])
            )
            receiver_avg.append(
                sum(d["receiver"] for d in data[t]) / len(data[t])
            )
        else:
            sender_avg.append(0)
            receiver_avg.append(0)

    plt.figure()
    plt.plot(tests, sender_avg, marker="o", label="Sender")
    plt.plot(tests, receiver_avg, marker="s", label="Receiver")

    # Mark failures
    fail_tests = [r.get("test_id") for r in failures]

    plt.scatter(fail_tests,
                [0] * len(fail_tests),
                marker="x",
                color="red",
                label="Failure")

    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Test ID")
    plt.ylabel("Throughput (bps)")
    plt.title("Throughput per Test (Failures Marked)")
    plt.legend()
    plt.grid(True)


def plot_sender_vs_receiver(data):

    sender = []
    receiver = []

    for t in data:
        for d in data[t]:
            sender.append(d["sender"])
            receiver.append(d["receiver"])

    plt.figure()
    plt.scatter(sender, receiver)

    plt.xlabel("Sender Throughput")
    plt.ylabel("Receiver Throughput")
    plt.title("Sender vs Receiver Throughput")
    plt.grid(True)



def plot_retransmissions(data):

    tests = sorted(data.keys())

    retrans_avg = [
        sum(d["retrans"] for d in data[t]) / len(data[t])
        for t in tests
    ]

    plt.figure()
    plt.plot(tests, retrans_avg, marker="o")

    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Test ID")
    plt.ylabel("Retransmissions")
    plt.title("Retransmissions per Test")
    plt.grid(True)

def plot_cpu_usage(data):

    tests = sorted(data.keys())
    cpu_avg = []

    for t in tests:

        cpu_values = [
            compute_cpu_percent(d["samples"])
            for d in data[t]
        ]

        cpu_avg.append(
            sum(cpu_values) / len(cpu_values)
            if cpu_values else 0
        )

    plt.figure()
    plt.plot(tests, cpu_avg, marker="o")

    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Test ID")
    plt.ylabel("CPU Usage (%)")
    plt.title("Router CPU Usage per Test")
    plt.grid(True)


def plot_interface_throughput(data):

    tests = sorted(data.keys())
    rates = []

    for t in tests:

        total = 0
        count = 0

        for d in data[t]:

            samples = d["samples"]

            valid = [
                s for s in samples
                if "interfaces" in s.get("metrics", {})
            ]

            if len(valid) < 2:
                continue

            first = valid[0]["metrics"]["interfaces"]
            last = valid[-1]["metrics"]["interfaces"]

            for iface in first:

                rx_diff = (
                    last[iface]["rx_bytes"] -
                    first[iface]["rx_bytes"]
                )

                total += rx_diff
                count += 1

        rates.append(total / count if count else 0)

    plt.figure()
    plt.plot(tests, rates, marker="o")

    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Test ID")
    plt.ylabel("RX Bytes (Delta)")
    plt.title("Interface Throughput per Test")
    plt.grid(True)


def plot_success_rate(records):

    counts = defaultdict(lambda: {"ok": 0, "total": 0})

    for r in records:
        key = r.get("test_id", "unknown")
        counts[key]["total"] += 1

        if r.get("status") == "success":
            counts[key]["ok"] += 1

    tests = sorted(counts.keys())

    rates = [
        counts[t]["ok"] / counts[t]["total"]
        for t in tests
    ]

    plt.figure()
    plt.plot(tests, rates, marker="o")

    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Success Rate")
    plt.title("Feasibility per Test")
    plt.ylim(0, 1.05)
    plt.grid(True)


# main
def main():

    records = load_data("tcp_results.jsonl")

    success, failure = success_failure(records)

    data = summarize_by_test(success)

    plot_throughput(data, failure)
    plot_sender_vs_receiver(data)
    plot_retransmissions(data)
    plot_cpu_usage(data)
    plot_interface_throughput(data)
    plot_success_rate(records)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()