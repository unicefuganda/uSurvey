jQuery(document).ready(function($) {
    var ws4redis = WS4Redis({
        uri: ws_uri+'statusbar?subscribe-user&subscribe-broadcast&subscribe-group',
        connecting: on_connecting,
        connected: on_connected,
        receive_message: receiveMessage,
        disconnected: on_disconnected,
        heartbeat_msg: ws_heartbeat
    });

    // attach this function to an event handler on your site
    function sendMessage(msg) {
        ws4redis.send_message(JSON.stringify(msg));
    }

    function on_connecting() {
        console.info('Websocket is connecting...');
    }

    function on_connected() {
        console.info('connected.');
    }

    function on_disconnected(evt) {
        console.info('disconnected.');
        //===to do====
        //Need to produce some colour indication on screen to display this
    }

    // receive a message though the websocket from the server
    function receiveMessage(msg) {
        msg = JSON.parse(msg); //expecting JSON msg
        switch(msg.type) {
            case 'download-data':
                //handle data updates
                updateDownloadStatus(msg)
                break;
            //in the future we can have other update type
        }
    }
});

updateDownloadStatus = function(msg) {
        //handle status update on screen
};