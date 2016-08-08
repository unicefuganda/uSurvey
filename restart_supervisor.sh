echo 'stoping supervisor...'
{ # your 'try' block
    kill $(cat supervisord.pid)
} || { # your 'catch' block
    echo 'looks like supervisor is not running!'
}
echo 'starting supervisor...'
supervisord
