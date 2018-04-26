# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import paho.mqtt.client as mqtt
import time
import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookParser

from linebot.exceptions import InvalidSignatureError

from linebot.models import MessageEvent, TextMessage, TextSendMessage

global client
global options

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print 'Specify LINE_CHANNEL_SECRET as environment variable.'
    sys.exit(1)
if channel_access_token is None:
    print 'Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.'
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text

    body = request.get_data(as_text=True)
    app.logger.info('Request bodyh: ' + body)

    # parse webhook body

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text=event.message.text))
        client.publish('TA', event.message.text)
    return 'OK'


# The callback for when the client receives a CONNACK response from the server.

def on_connect(
    client,
    userdata,
    flags,
    rc,
    ):
    print 'Connected with result code ' + str(rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    app.run(debug=options.debug, port=options.port)


# The callback for when a PUBLISH message is received from the server.

def on_message(client, userdata, msg):
    print msg.topic + ' ' + str(msg.payload)


def on_publish(client, userdata, msg):
    print 'msg: ' + str(msg)


def on_subscribe(
    mosq,
    obj,
    mid,
    granted_qos,
    ):
    print 'Subscribed: ' + str(mid) + ' ' + str(granted_qos)


if __name__ == '__main__':
    arg_parser = ArgumentParser(usage='Usage: python ' + __file__
                                + ' [--port <port>] [--help]')
    arg_parser.add_argument('-p', '--port', type=int, default=8000,
                            help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug'
                            )
    options = arg_parser.parse_args()

    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe
    client.username_pw_set('bbff39d0d3066758ffe55666762b3c8b150295b848cb6c871b79f2fff36c79fb'
                           ,
                           '50acea3098359517297e08040dc6bfc371d044190be6527c1ac29e078cbe8313'
                           )

    client.connect('147.75.93.178', 1883, 60)

    client.loop_forever()
