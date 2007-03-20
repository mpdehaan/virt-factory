#!/bin/bash

USER=alikins
HOST=et.redhat.com

rsync -rav --delete -e ssh rpms/ $USER@$HOST:/var/www/sites/virt-factory.et.redhat.com/download/repo/fc6/i686/
rsync -rav --delete -e ssh srpms/  $USER@$HOST:/var/www/sites/virt-factory.et.redhat.com/download/repo/fc6/srpms/
rsync -rav --delete -e ssh tars/  $USER@$HOST:/var/www/sites/virt-factory.et.redhat.com/download/src/


