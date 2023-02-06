import json
import socketserver
import threading
from datetime import timedelta, datetime


# 클라이언트의 요청을 처리하는 핸들러 클래스 socketserver을 사용해서 TCPserver을 만들 때 이용
class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):  # 데이터가 수신될 때 실행되는 handle함수
        """
            BaseRequestHandler 클래스에 정의된 인스턴스 변수
            클라이언트와 연결된 소켓 정보
            self.request: 클라이언트 소켓
            self.client_address: 클라이언트 주소
        """
        (IP, PORT) = self.client_address  # 클라이언트의 ip, port 저장
        client = self.request, (IP, PORT)  # client 변수에 self.request, ip, port 저장
        print(client)

        if client not in MultiServerObj.clients:  # 서버 접속 목록 클라이언트가 아니라면
            MultiServerObj.clients.append(client)  # 서버 접속 목록에 client 변수 정보 저장
            print(f"{datetime.now().strftime('%D %T')}\n{IP} : {PORT} 가 연결되었습니다.")
        MultiServerObj.receive_messages(self.request)  # MultiServer 클래스의 receive_message 함수 실행


# 멀티 클라이언트를 서비스하기 위해서 두 개의 클래스를 부모로 갖는 파생 클래스 생성
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass  # 아무일도 하지 않기 때문에 pass 넣음


class MultiServer:
    def __init__(self):
        self.clients = []  # 접속된 클라이언트 소켓 목록을 넣을 모든 클라이언트 소켓 저장 리스트
        self.received_message = None  # self.received_message 대충 정의해놓기

    # 클라이언트에서 요청이 오면 실행될 함수
    def receive_messages(self, client_socket):
        while True:
            try:
                incoming_message = client_socket.recv(9999)
                if not incoming_message:  # 수신 받은 메시지가 없으면 연결이 종료됨
                    break
            except ConnectionAbortedError as e:
                print(e)
                # self.remove_socket(client_socket)     # 연결 오류 뜨면 client_socket 연결 종료시킴
                break
            except ConnectionResetError as e:
                print(e)
                break
            else:
                self.received_message = json.loads(incoming_message.decode('utf-8'))
                print(self.received_message)


if __name__ == "__main__":
    MultiServerObj = MultiServer()  # MultiServer클래스의 객체 생성
    host, port = '10.10.21.102', 6666
    '''
        # 아래 코드와 비슷하게 돌아감. with를 사용해서 만들어보고 싶었음
        server = ThreadedTCPServer((host, port), TCPHandler)
        server.serve_forever()
    '''
    # socketserver을 이용해서 TCP 서버 소켓 객체 생성
    with ThreadedTCPServer((host, port), TCPHandler) as server:
        server.serve_forever()  # 서버를 실행하고 서비스를 무한 반복한다
