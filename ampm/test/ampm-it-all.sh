#!/bin/bash

msg()
{
    echo 
    echo "============ $1 ============"
    echo 
}

create_ampm_config()
{
cat <<EOF
[server]
url=http://127.0.0.1:5150
[user]
username=admin
password=fedora

EOF

}


test_ampm()
{
    msg "Testing ampm"
    create_ampm_config > ~/.ampm_config

    msg "ampm list hosts"
    /usr/bin/ampm list hosts

    msg "ampm list status"
    /usr/bin/ampm list status
    
    msg "ampm list guests"
    /usr/bin/ampm list guests

    msg "ampm list profiles"
    /usr/bin/ampm list profiles

    msg "ampm list -v profiles"
    /usr/bin/ampm list -v profiles

    msg "ampm list tasks"
    /usr/bin/ampm list tasks

    msg "ampm list users"
    /usr/bin/ampm list users

    msg "ampm query <profiles>"
    for i in `/usr/bin/ampm list profiles | cut -f1 -d' '`
    do
	/usr/bin/ampm query --profile $i
    done
    

    msg "ampm user add"
    /usr/bin/ampm add user --username adrian --password foobar --first Adrian --last Likins  --email "alikins@redhat.com" --description "Adrian is awesome"
    /usr/bin/ampm add user --username test_user --password test1 --first Robert  --last Zimmerman  --email "bob@example.com" --description "shorttimer"
    /usr/bin/ampm add user --username mdehaan --password llama --first Michael --last DeHaan --email "mdehaan@redhat.com" --description "I like llamas"

    msg "ampm delete user"
    test_user_id=`/usr/bin/ampm list users | grep Zimmerman | cut -f1 -d' '` 
    /usr/bin/ampm delete --user_id $test_user_id
    /usr/bin/ampm list users

    msg "testing ampm with a non admin user"
    /usr/bin/ampm --username adrian --password foobar list users
    

    msg "testing ampm with specified server and user"
    /usr/bin/ampm --server http://127.0.0.1:5150 --username adrian --password foobar list profiles


}

test_ampm
