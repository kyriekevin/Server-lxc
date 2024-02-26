#!/usr/bin/expect -f

set container [lindex $argv 0]
spawn sudo lxc exec $container -- /bin/bash

expect "#"
send "nvidia-smi -L\r"

expect {
  "*GPU 0*" { exit 0 }
  eof       { exit 1 }
}
