from mitmproxy import http
import aiohttp
import time
import base64

flag_req = None
jstext = '''function socket_start(){window.globalSocket121=new WebSocket("ws://127.0.0.1:8765"),window.globalSocket121.onopen=function(t){window.globalSocket121.send("password=123456")},window.globalSocket121.onmessage=function(t){t=atob(t.data).split("------------");const o=t[0];var a=t[1];if(2==t.length)var[e,d,n,r]=a.split("[][][][][][]"),s=(data_method=atob(e),data_url=atob(d),data_data=atob(n),data_headers=atob(r),{});const b={};void 0!==data_headers&&null!==data_headers&&""!==data_headers&&data_headers.split("|||||").map(t=>t.trim().split(": ")).forEach(([t,a])=>{b[t]=a}),s.method=data_method,["GET","HEAD","OPTIONS"].includes(data_method.toUpperCase())||(s.body=data_data),0<Object.keys(b).length&&(s.headers=new Headers(b)),fetch(data_url,s).then(t=>{const a=t.status.toString(),e={};return t.headers.forEach((t,a)=>{e[a]=t}),headersString=JSON.stringify(e),(xydata=t.text()).then(t=>({statusCode:a,headersString:headersString,xydata:t}))}).then(({statusCode:t,headersString:a,xydata:e})=>{e=function(t){for(var a="",e=new Uint8Array(t),o=e.byteLength,d=0;d<o;d++)a+=String.fromCharCode(e[d]);return a}((new TextEncoder).encode(e));window.globalSocket121.send(btoa(o+"------------"+btoa(t)+"------------"+btoa(a)+"------------"+btoa(e)))})}}void 0!==window.globalSocket121&&window.globalSocket121.readyState!==WebSocket.CLOSED||socket_start();'''


class CustomResponse:

    async def request(self, flow: http.HTTPFlow) -> None:
        global flag_req
        headers6 = {k.lower(): v for k, v in flow.request.headers.items()}
        flag_req = headers6.get('req-flag', '')
        if flag_req:
            await self.handle_delayed_request(flow)

    async def handle_delayed_request(self, flow: http.HTTPFlow) -> None:
        newheaders = '|||||'.join(
            [f'Res-flag: {value}' if key.lower() == 'req-flag' else f'{key}: {value}' for key, value in
             flow.request.headers.items()])
        burp0_json = {'data': base64.b64encode(flow.request.text.encode()).decode(),
                      'header': base64.b64encode(newheaders.encode()).decode(), 'method': str(flow.request.method),
                      'url': base64.b64encode(flow.request.url.encode()).decode()}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('http://127.0.0.1:12931/api',
                                        headers={'Content-Type': 'application/json;charset=UTF-8'},
                                        json=burp0_json) as response:
                    resp_headers = http.Headers()
                    for key, value in response.headers.items():
                        if key == 'Server' and 'Python' in value and ('Werkzeug' in value):
                            continue
                        resp_headers.add(key, value)
                    response2 = http.Response(http_version=b'HTTP/1.1', status_code=response.status,
                                              reason=response.reason.encode(), headers=resp_headers,
                                              content=await response.read(), trailers=None, timestamp_start=time.time(),
                                              timestamp_end=time.time())
                    flow.response = response2
        except:
            flow.response.content = 'flask服务器请求失败，检查server.py是否启动'

    def response(self, flow: http.HTTPFlow) -> None:
        global jstext
        headers6 = {k.lower(): v for k, v in flow.request.headers.items()}
        resflag = headers6.get('res-flag', '')
        flag_req = headers6.get('req-flag', '')
        if not flag_req and (not resflag):
            content_type = flow.response.headers.get('Content-Type', '').lower()
            if content_type.startswith('application/javascript'):
                flow.response.text += jstext
            if content_type.startswith('text/html'):
                flow.response.text += '<script>' + jstext + '</script>'
            if 'Content-Security-Policy' in flow.response.headers:
                del flow.response.headers['Content-Security-Policy']


addons = [CustomResponse()]
