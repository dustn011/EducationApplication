import json
import socketserver
import threading
from datetime import timedelta, datetime
import pymysql

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
            print(f"{datetime.now().strftime('%D %T')}, {IP} : {PORT} 가 연결되었습니다.")
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
            except:
                pass
            else:
                self.received_message = json.loads(incoming_message.decode('utf-8'))
                print(self.received_message)
                identifier = self.received_message.pop(0)     # identifier = 식별자 -> 추출
                if not incoming_message:     # 연결이 종료됨
                    print('클라이언트에서 빈 메시지가 왔습니다')
                    break
                # 로그인 요청
                elif identifier == 'plzCheckAccount':
                    self.method_checkAccount(client_socket)
                    pass
                # 클라이언트 종료
                elif identifier == 'plzDisconnectSocket':
                    self.disconnect_socket(client_socket)

########################################################################################################################################################

                # 문제 출제 DB 저장
                elif identifier == 'teacher_update':
                    con=pymysql.connect(host='10.10.21.102', user='lilac',password='0000',db='education_application')
                    with con:
                        with con.cursor() as cur:
                            sql=f"insert into `education_application`.`question`(FIeld, Title, Content, Answer) values \
                            ('{self.received_message[0]}','{self.received_message[1]}','{self.received_message[2]}','{self.received_message[3]}')"
                            cur.execute(sql)
                            con.commit()
                    # self.disconnect_socket(client_socket)

                # QNA 클라이언트로 보내기
                elif identifier =='teacher_QNA':
                    qna_list=self.QNA_DB()
                    client_socket.send((json.dumps(qna_list)).encode())
                    # self.disconnect_socket(client_socket) # 왜 이게 있으면 꺼지지??

                # QNA 답변 저장 및 QNA 저장된 내역 보내기
                elif identifier == 'teacher_qna_answer':
                    print(self.received_message)
                    con=pymysql.connect(host='10.10.21.102', user='lilac',password='0000',db='education_application')
                    with con:
                        with con.cursor() as cur:
                            sql=f"update `education_application`.`qna` set answer='{self.received_message[0]}',answer_dt={'now()'}, state='{self.received_message[1]}' where number={self.received_message[2]}"
                            cur.execute(sql)
                            con.commit()
                    qna_list=self.QNA_DB()
                    print(qna_list)
                    client_socket.send((json.dumps(qna_list)).encode())

    def QNA_DB(self):
        con = pymysql.connect(host='10.10.21.102', user='lilac', password='0000', db='education_application')
        with con:
            with con.cursor() as cur:
                sql = f"select * from `education_application`.`qna`"
                cur.execute(sql)
                temp = cur.fetchall()
        # DB에서 가져온 데이터 datetime 문자열로 바꾸기
        qna = []
        for i in range(len(temp)):
            temp1 = []
            for j in range(len(temp[0])):
                if type(temp[i][j]) == datetime:
                    temp1.append(temp[i][j].strftime('%D,%T'))
                else:
                    temp1.append(temp[i][j])
            qna.append(temp1)
        qna_list = ['teacher_QNA', qna]
        return qna_list


########################################################################################################################################################

    # DB에서 account정보와 일치하는지 확인
    def method_checkAccount(self, sender_socket):
        print(f'{sender_socket}\n에서 회원 정보 확인 메시지가 왔습니다')
        pass

    # 클라이언트에서 연결 끊는다고 시그널 보내면 소켓 리스트에서 해당 클라이언트 연결 소켓 지움
    def disconnect_socket(self, senders_socket):
        for client in self.clients:
            socket, (ip, port) = client
            if socket is senders_socket:
                self.clients.remove(client)  # 전체 클라이언트 소켓 리스트에서 해당 소켓 제거
                print(f"{datetime.now().strftime('%D %T')}, {ip} : {port} 연결이 종료되었습니다")
                socket.close()
                print(self.clients)


if __name__ == "__main__":
    MultiServerObj = MultiServer()  # MultiServer클래스의 객체 생성
    host, port = '10.10.21.124', 9010
    '''
        # 아래 코드와 비슷하게 돌아감. with를 사용해서 만들어보고 싶었음
        server = ThreadedTCPServer((host, port), TCPHandler)
        server.serve_forever()
    '''
    # socketserver을 이용해서 TCP 서버 소켓 객체 생성
    with ThreadedTCPServer((host, port), TCPHandler) as server:
        server.serve_forever()  # 서버를 실행하고 서비스를 무한 반복한다
