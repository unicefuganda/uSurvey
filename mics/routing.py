__author__ = 'anthony'
from django.conf import settings
from channels.routing import route
from channels import Group
from channels.auth import channel_session_user
from channels.auth import channel_session_user_from_http


def get_group_path(user, path):
    path = path.strip("/")
    return '%s/%s' % (path, user.pk)


@channel_session_user_from_http
def ws_add(message):
    print 'incoming ', message.user.pk
    path = message.content['path']
    if message.user.is_authenticated():
        Group(get_group_path(message.user, path)).add(message.reply_channel)


@channel_session_user
def ws_message(message):
    pass


@channel_session_user
def ws_disconnect(message):
    path = message.content['path']
    if message.user.is_authenticated():
        Group(get_group_path(message.user, path)
              ).discard(message.reply_channel)


channel_routing = [
    route("websocket.connect", ws_add, path=r"^%s$" % settings.WEBSOCKET_URL),
    route("websocket.receive", ws_message),
    route("websocket.disconnect", ws_disconnect),
]
