#!/bin/sh
yum -y install ruby ruby-libs ruby-rdoc ruby-irb ruby-ri ruby-docs ruby-mode
wget http://rubyforge.org/frs/download.php/11289/rubygems-0.9.0.tgz
gunzip rubygems-0.9.0.tgz
tar -xvf rubygems-0.9.0.tar
(cd rubygems-0.9.0; ruby setup.rb; cd -)
gem install rails --include-dependencies

