# TCP-UDP_packet_forwarding
Vagrant file contains the configurations of the VMs : Sender, receiver and tracker.
forwarder.py : used a forwarder function that has three main components:

There's the logging system. Every time a packet arrives, I record:
  - The exact timestamp
  - Whether it's UDP or TCP
  - Where it came from and where it's going
  - The size of the packet
  - And for TCP, whether it's a new connection or data transfer
