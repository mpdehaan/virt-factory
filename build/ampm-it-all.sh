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

    msg "ampm list machines"
    /usr/bin/ampm list machines

    msg "ampm list status"
    /usr/bin/ampm list status
    
    msg "ampm list deployments"
    /usr/bin/ampm list deployments

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
	echo profile $i
	/usr/bin/ampm query --profile $i
    done
    

    msg "ampm user add"
    /usr/bin/ampm add user --username adrian --password foobar --first Adrian --last Likins  --email "alikins@redhat.com" --description "Adrian is awesome"
    /usr/bin/ampm add user --username test_user --password test1 --first Robert  --last Zimmerman  --email "bob@example.com" --description "shorttimer"

    msg "ampm delete user"
    test_user_id=`/usr/bin/ampm list users | grep Zimmerman | cut -f1 -d' '` 
    /usr/bin/ampm delete --user_id $test_user_id
    /usr/bin/ampm list users

    msg "testing ampm with a non admin user"
    /usr/bin/ampm --username adrian --password foobar list users
    


}

test_ampm