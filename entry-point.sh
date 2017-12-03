#!/bin/bash

remove_other_environment_configs () {
    if [[ "${IS_DEV}" == "1" ]]; then
        echo " >> Development environment detected, switching domains to dev"
        cd /etc/nginx/sites-enabled/ && ls | grep -v "dev" | grep "app" | xargs rm
        return
    fi

    echo " >> Switching domains to PRODUCTION"
    cd /etc/nginx/sites-enabled/ && ls | grep "dev" | xargs rm
}

remove_other_environment_configs
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
