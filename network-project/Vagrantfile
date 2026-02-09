Vagrant.configure("2") do |config|
    #Here we define a Vm instance named : sender, with a configuration block
    config.vm.synced_folder ".", "/vagrant", type: "virtualbox"

    config.vm.define "router" do |router|
        router.vm.box = "ubuntu/focal64"
        router.vm.hostname = "router"

        router.vm.network "private_network", ip: "192.168.10.1", virtualbox__intnet: "netA"
        router.vm.network "private_network", ip: "192.168.20.1", virtualbox__intnet: "netB"

        router.vm.provider "virtualbox" do |vb|
            vb.name = "iperf_router"
            vb.memory = 512
            vb.cpus = 1
        end
        router.vm.provision "shell", inline: <<-SHELL
            apt-get update -y
            sysctl -w net.ipv4.ip_forward=1

            iptables -P FORWARD ACCEPT
        SHELL

    end


    config.vm.define "server" do |server| #Vagrant way to define a VM, the "do" creates the variable "sender"
        server.vm.box = "ubuntu/focal64" #OS base image, Vagrant check it's cache for this box, if not found it downloads it from the official website
        server.vm.hostname = "server" #sets sender as a hostname inside the OS guest

        server.vm.network "private_network", ip: "192.168.20.10", virtualbox__intnet: "netB"
        server.vm.provider "virtualbox" do |vb|
            vb.name = "iperf-server"
            vb.memory = 512 #RAM allocation to the VM, minimal but sufficient
            vb.cpus = 1 #allocates CPU's cores 1core= 1socket= 1thread
        end
        server.vm.provision "shell", inline: <<-SHELL
            apt-get update -y
            apt-get install -y iperf3
            sudo ip route add 192.168.10.0/24 via 192.168.20.1 
        SHELL
      
    end
  
    config.vm.define "client" do |client|
        client.vm.box = "ubuntu/focal64"
        client.vm.hostname = "client"

        client.vm.network "private_network", ip: "192.168.10.20", virtualbox__intnet: "netA"
        client.vm.provider "virtualbox" do |vb|
            vb.name = "iperf-client"
            vb.memory = 512
            vb.cpus = 1 
        end
        client.vm.provision "shell", inline: <<-SHELL
            apt-get update -y 
            apt-get install -y iperf3
            sudo ip route add 192.168.20.0/24 via 192.168.10.1 
        SHELL
    end
   
end