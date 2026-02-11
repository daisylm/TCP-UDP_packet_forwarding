# Hardware optimization for Linux servers: 5G RAN workloads

This project involve *number of steps to be mentionned later* :

**Stage 1: Vagrant-based Packet Forwarding with iperf**

*Objective:*

Set up a virtual network environment to analyze packet forwarding performance between client and server through an intermediate router. The goal is to measure and compare network throughput (bitrate) between transmission "Client" and reception "Server" endpoints.

*Architecture overview:*
                                     
      Client (Subnet: 192.168.10.20/24)        ---->      Router (Subnet: Dual)         ---->     Server (Subnet: 192.168.20.10/24)
                                           
                    

*Test Methodology:*

We generate UDP/TCP traffic using "iperf" from client to server. The router in the middle do the packet inspection and the forwarding between subnets, finally the server receive the packets by listening on port 5201 and do the traffic income measurement.

*UDP Case* For each Bandwidth value : 
  - On server : iperf3 -s -J > server.json
  - On Client : iperf3 -c < server ip > -u -b < rate > -t 10 -J > client.json
Each test produces one clean JSON file per side, enabling reproducible analysis.

*TCP Case* The bandwidth is defined by default, so we run :
  - On server: iperf3 -s -J > server.json
  - On client: iperf3 -c  < server ip > -t 10 -i 

The metrics we used to measure the performance of Virtual machines are:
  - Bitrate/Throughput: Mbps transmitted vs received
  - Packet Loss: Percentage of packets lost in transit
  - Jitter: Latency Variation in packet arrival times

*Mistakes to avoid ( for beginners)*

  - NAT interface kept enabled, using Static routes added for internal subnets, where the routing decision relies on Longest Prefix Match (LPM) on both Client and Server, if not the Linux system by default send packets via default Gateway "NAT". Example : (on client section in Vagrant file we add : **sudo ip route add 192.168.20.0/24 via 192.168.10.1** )

*The setup Foundation*

  - Environment: Local Virtualization
  - Tools: Vagrant, VirtualBox, iperf3, Linux networking
  - Reproducibility: Fully automated, version-controlled setup

