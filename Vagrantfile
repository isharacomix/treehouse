Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.network "forwarded_port", guest: 80, host: 8000, protocol: "tcp"
  config.vm.network "forwarded_port", guest: 80, host: 8000, protocol: "udp"
  config.vm.network "forwarded_port", guest: 1935, host: 1935, protocol: "tcp"
  config.vm.network "forwarded_port", guest: 1935, host: 1935, protocol: "udp"
end
