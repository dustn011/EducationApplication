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
        self.now_connected_account = []

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
                    account_info = self.method_check_account()
                    self.login_access_message(client_socket, account_info)
                # 로그아웃 요청
                elif identifier == 'plzLogoutAccount':
                    self.logout_account(client_socket)
                # 클라이언트 종료
                elif identifier == 'plzDisconnectSocket':
                    self.disconnect_socket(client_socket)
                # plzGiveQuiz = 퀴즈 목록 요청 코드
                elif identifier == "plzGiveQuiz":
                    # 클라이언트의 현재 탭
                    now_tab = self.received_message.pop(0)
                    # 클라이언트에 접속중인 학생
                    account = self.received_message[0]
                    self.send_quiz(client_socket, now_tab, account)
                # hereAnswer = 학생이 제출한 답과 결과
                elif identifier == "hereAnswer":
                    self.insert_answer(self.received_message[0], self.received_message[1],
                                       self.received_message[2], self.received_message[3], self.received_message[4])

    # 접속중인 account 리스트에서 빼주기
    def logout_account(self, sender_socket):
        self.now_connected_account.remove(self.received_message[0])
        print('현재 접속한 account: ', self.now_connected_account)

    def login_access_message(self, sender_socket, account_info):
        print(account_info)
        if account_info and (account_info[0][0] not in self.now_connected_account):    # 회원정보를 옳게 입력했다면
            access_message = ['success_login']
            self.now_connected_account.append(account_info[0][0])
            print('로그인 성공')
        else:               # 회원정보를 옳게 입력하지 않았다면
            access_message = ['failed_login']
            print('로그인 실패')
        send_accessMessage = json.dumps(access_message)
        sender_socket.send(send_accessMessage.encode('utf-8'))  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌

    # DB에서 account정보와 일치하는지 확인
    def method_check_account(self):
        print('회원 정보 확인 메시지가 왔습니다')
        account = pymysql.connect(host='10.10.21.102', user='edu', password='0000', db='education_application',
                                       charset='utf8')
        # DB와 상호작용하기 위해 연결해주는 cursor 객체 만듬
        all_account = account.cursor()
        # 클라이언트가 입력한 계정 정보가 일치하는지 확인
        sql = f"SELECT * FROM account WHERE name = '{self.received_message[0]}'"
        # execute 메서드로 db에 sql 문장 전송
        all_account.execute(sql)
        account_info = all_account.fetchall()   # 회원 정보 저장
        # DB 닫아주기
        account.close()
        return account_info

    # 클라이언트에서 연결 끊는다고 시그널 보내면 소켓 리스트에서 해당 클라이언트 연결 소켓 지움
    def disconnect_socket(self, senders_socket):
        for client in self.clients:
            socket, (ip, port) = client
            if socket is senders_socket:
                self.clients.remove(client)  # 전체 클라이언트 소켓 리스트에서 해당 소켓 제거
                print(f"{datetime.now().strftime('%D %T')}, {ip} : {port} 연결이 종료되었습니다")
                socket.close()

    # 요청한 클라이언트에 해당 탭의 퀴즈 목록 전달
    def send_quiz(self, senders_socket, tab, student):
        class_tab = ''
        # DB의 과목과 클라이언트의 탭을 맞추기 위한 과정
        if tab == '곤충':
            class_tab = 'insect'
        elif tab == '조류':
            class_tab = '?'
        elif tab == '포유류':
            class_tab = '??'
        # 해당 과목의 퀴즈 목록
        conn = pymysql.connect(host='10.10.21.102', user='lilac', password='0000', db='education_application')
        curs = conn.cursor()
        curs.execute("select * from education_application.question where FIeld = '%s'" % tab)
        questions = curs.fetchall()
        senders_socket.sendall(json.dumps(["hereQuiz", questions]).encode('utf-8'))
        # 접속중인 학생의 퀴즈 진도
        curs.execute("select * from education_application.%s where student = '%s'" % (class_tab, student))
        rate = curs.fetchall()
        senders_socket.sendall(json.dumps(["hereRate", rate]).encode('utf-8'))

    # 데이터베이스에 퀴즈 결과 반영
    def insert_answer(self, tab, student, q_number, answer, score):
        class_tab = ''
        # DB의 과목과 클라이언트의 탭을 맞추기 위한 과정
        if tab == '곤충':
            class_tab = 'insect'
        elif tab == '조류':
            class_tab = '?'
        elif tab == '포유류':
            class_tab = '??'
        conn = pymysql.connect(host='10.10.21.102', user='lilac', password='0000', db='education_application')
        curs = conn.cursor()
        curs.execute("update education_application.%s set answer%d = '%s', score = '%s' where student = '%s'" %
                     (class_tab, q_number, answer, score, student))
        conn.commit()


if __name__ == "__main__":
    MultiServerObj = MultiServer()  # MultiServer클래스의 객체 생성
    host, port = '10.10.21.129', 6666
    '''
        # 아래 코드와 비슷하게 돌아감. with를 사용해서 만들어보고 싶었음
        server = ThreadedTCPServer((host, port), TCPHandler)
        server.serve_forever()
    '''
    # socketserver을 이용해서 TCP 서버 소켓 객체 생성
    with ThreadedTCPServer((host, port), TCPHandler) as server:
        server.serve_forever()  # 서버를 실행하고 서비스를 무한 반복한다
