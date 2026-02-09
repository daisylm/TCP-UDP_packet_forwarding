import json
import os
import matplotlib.pyplot as plt

# -----------------------------
# Configuration
# -----------------------------
BASE_DIR = "results/udp"
bandwidths = ["1M", "10M", "100M", "1000M"]
expected_bw_mbps = [1, 10, 100, 1000]   # theoretical bandwidths
UDP_PAYLOAD_BYTES = 1470                # iperf3 default UDP payload

client_rates = []
server_rates = []

# -----------------------------
# Data extraction
# -----------------------------
for bw in bandwidths:
    # ----- CLIENT (sender throughput) -----
    with open(os.path.join(BASE_DIR, bw, "client.json")) as f:
        client_data = json.load(f)

    client_bps = client_data["end"]["sum"]["bits_per_second"]

    # ----- SERVER (receiver throughput, computed) -----
    with open(os.path.join(BASE_DIR, bw, "server.json")) as f:
        server_data = json.load(f)

    udp_stream = server_data["end"]["streams"][0]["udp"]
    packets = udp_stream["packets"]
    seconds = udp_stream["seconds"]

    server_bps = (packets * UDP_PAYLOAD_BYTES * 8) / seconds

    # Convert to Mbps
    client_rates.append(client_bps / 1e6)
    server_rates.append(server_bps / 1e6)

# -----------------------------
# Plot
# -----------------------------
plt.figure(figsize=(8, 6))
plt.plot(client_rates, server_rates, marker="o", linewidth=2)

plt.xlabel("Client bitrate (Mbps)")
plt.ylabel("Server bitrate (Mbps)")
plt.title("Client vs Server Throughput (UDP Saturation Curve)")
plt.grid(True)

# Use REAL measured values for positioning,
# but EXPECTED bandwidths for axis labels
plt.xticks(client_rates, ["1M", "10M", "100M", "1000M"])
plt.yticks(server_rates, ["1M", "10M", "100M", "1000M"])

# Annotate real measured values (expected → real)
for i in range(len(client_rates)):
    plt.annotate(
        f"{expected_bw_mbps[i]}M → {client_rates[i]:.1f}/{server_rates[i]:.1f} Mbps",
        (client_rates[i], server_rates[i]),
        textcoords="offset points",
        xytext=(6, 6),
        fontsize=9
    )

plt.tight_layout()
plt.show()
