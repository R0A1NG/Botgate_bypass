import json
import base64
import asyncio
import websockets
from flask import Flask, request, make_response
from threading import Thread
from urllib.parse import urlparse
import time
import random
import string


app = Flask(__name__)
try:
    app.json.ensure_ascii = False
except:
    app.config['JSON_AS_ASCII'] = False
loop = None
message = ''
all_wsclient = {}


def generate_random_string(length=32):
    characters = string.ascii_lowercase + string.digits
    return ''.join((random.choice(characters) for _ in range(length)))


def req_handle(verChar):
    print('-----------------------------------------------------------------------------------------------')
    try:
        hmethod = request.get_json()['method']
        hurl = request.get_json()['url']
        hurl = base64.b64decode(hurl).decode()
        try:
            hheader = request.get_json()['header']
            hheader = base64.b64decode(hheader).decode()
        except:
            hheader = ''
        hdata = request.get_json()['data']
        data = '{}[][][][][][]{}[][][][][][]{}[][][][][][]{}'.format(base64.b64encode(hmethod.encode()).decode(),
                                                                     base64.b64encode(hurl.encode()).decode(), hdata,
                                                                     base64.b64encode(hheader.encode()).decode())
        print('请求信息：')
        print('Method：{}'.format(hmethod))
        print('URL：{}'.format(hurl))
        print('Headers：{}'.format(hheader))
        print('Data：{}'.format(base64.b64decode(hdata).decode()))
        data = verChar + '------------' + str(data)
        data = base64.b64encode(data.encode()).decode()
        parsed_url = urlparse(hurl)
        result = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return data, result
    except:
        print('发送给web客户端的消息：\ndata数据错误')
        print('-----------------------------------------------------------------------------------------------')
        return None, None


@app.route('/api', methods=['POST'])
def receive_data():
    verChar = str(generate_random_string())
    data = req_handle(verChar)
    if not data[0]:
        return 'data数据错误'
    try:
        loop.call_soon_threadsafe(send_data_to_client, all_wsclient[data[1]], data)
    except:
        print('ws客户端已断开或未连接，目标站点：{}'.format(data[1]))
        return 'ws客户端已断开或未连接，目标站点：{}'.format(data[1])
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            messages1 = message.split('------------')
            if messages1 == ['']:
                continue
            newmessages0 = messages1[0]
            newmessages1 = base64.b64decode(messages1[1]).decode()
            newmessages2 = base64.b64decode(messages1[2]).decode()
            newmessages3 = base64.b64decode(messages1[3]).decode()
            if verChar == newmessages0:
                print('响应信息：')
                print('Code：' + str(newmessages1))
                print('Headers：' + newmessages2)
                print('Data：' + newmessages3)
                print('-----------------------------------------------------------------------------------------------')
                if newmessages2 == '0' and newmessages3 == '0':
                    return '网站访问失败，请检查\n1、URL是否正确！\n2、是否存在跨域访问\n3、网站是否能正常访问'
                newheaders = json.loads(newmessages2)
                response = make_response(newmessages3, int(newmessages1))
                for key, value in newheaders.items():
                    if key == 'transfer-encoding' or key == 'content-encoding':
                        continue
                    response.headers[key] = value
                return response
        except:
            time.sleep(0.1)
    print(
        '发送给web客户端的消息：\n发送给了ws客户端，但是没有返回！\n请检查：\n1、网站访问时间是否超过5秒\n2、ws客户端是否断开连接')
    print('-----------------------------------------------------------------------------------------------')
    return '发送给了ws客户端，但是没有返回！\n请检查：\n1、网站访问时间是否超过5秒\n、ws客户端是否断开连接'


async def handle_client(websocket):
    global message, all_wsclient
    token = await websocket.recv()
    if token != 'password=123456':
        await websocket.close()
        return
    client_address = websocket.remote_address
    try:
        headers = websocket.request_headers
        oriin = headers.get('Origin')
    except:
        oriin = ''
    all_wsclient[oriin] = websocket
    print('ws客户端连接成功，IP：{}，端口：{}，所在站点域名：{}'.format(client_address[0], client_address[1], oriin))
    await websocket.send(base64.b64encode('success!'.encode()).decode())
    while True:
        try:
            message = await websocket.recv()
            message = base64.b64decode(message).decode()
        except websockets.exceptions.ConnectionClosed:
            if oriin in all_wsclient:
                all_wsclient.pop(oriin)
                print("ws客户端已断开，目标站点：{}".format(oriin))
            break


def send_data_to_client(websocket, data):
    try:
        asyncio.run_coroutine_threadsafe(websocket.send(data[0]), loop)
    except websockets.exceptions.ConnectionClosed:
        if data[1] in all_wsclient:
            all_wsclient.pop(data[1])
            print("ws客户端已断开，目标站点：{}".format(data[1]))


def start_ws_server():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(handle_client, '0.0.0.0', 8765)
    loop.run_until_complete(server)
    loop.run_forever()


def start_flask_app():
    app.run('127.0.0.1', port=12931)


if __name__ == '__main__':
    flask_thread = Thread(target=start_flask_app)
    flask_thread.start()
    start_ws_server()
