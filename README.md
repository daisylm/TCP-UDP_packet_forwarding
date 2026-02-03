# Hardware optimization for Linux servers: 5G RAN workloads

This project involve *number of steps to be mentionned later* :

**Stage 1: Vagrant-based Packet Forwarding with iperf**

*Objective:*

Set up a virtual network environment to analyze packet forwarding performance between client and server through an intermediate router. The goal is to measure and compare network throughput (bitrate) between transmission "Client" and reception "Server" endpoints.

*Architecture overview:*
                                     
      Client (Subnet: 10.0.1.1/24)        ---->      Router (Subnet: Dual)         ---->     Server (Subnet: 10.0.2.1/24)
                                           
                    

*Test Methodology:*

We generate UDP/TCP traffic using "iperf" from client to server. The router in the middle do the packet inspection and the forwarding between subnets, finally the server receive the packets by listening on port 5201 and do the traffic income measurement.
The metrics we used to measure the performance of Virtual machines are:
  - Bitrate/Throughput: Mbps transmitted vs received
  - Packet Loss: Percentage of packets lost in transit
  - Jitter: Variation in packet arrival times

*The setup Foundation*

  - Environment: Local Virtualization
  - Tools: Vagrant, VirtualBox, iperf3, Linux networking
  - Reproducibility: Fully automated, version-controlled setup
