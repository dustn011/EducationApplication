import json
import requests
import xmltodict
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from datetime import datetime
from socket import *
from threading import *


def api_test():
    # API
    # 인증키 저장
    key = "jAB8gOQ%2BEjRxryPTRcGIWjS6sTl2FCowle%2Bb%2FVaRrcoCuQZTgCIEID85tLqWiPIfuY4%2FzUsqf81dQj6dYuTyYg%3D%3D"

    # 인증키 정보가 들어간 url 저장 (요청)
    url = f'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctPrtctList?serviceKey={key}'

    # request 모듈을 이용해서 정보 가져오기(byte형태로 가져와지는듯)
    content = requests.get(url).content
    # xmltodict 모듈을 이용해서 딕셔너리화 & 한글화
    diction = xmltodict.parse(content)
    # print(diction)
    # json.dumps를 이용해서 문자열화(데이터를 보낼때 이렇게 바꿔주면 될듯)
    json_string = json.dumps(diction, ensure_ascii=False)
    # 데이터 불러올 때(딕셔너리 형태로 받아옴)
    json_obj = json.loads(json_string)
    # print(json_obj)
    # diction 과 json_obj의 차이점이 뭔지 모르겠다
    # print 결과는 똑같아 보이는데

    # <response> 속 <body> 속 <items> 속 <item> 의 각 요소들
    # response 딕셔너리의 body 딕셔너리의 items 딕셔너리의 item 딕셔너리의 각 key 요소들의 value값을 가져왔음
    for item in json_obj['response']['body']['items']['item']:
        # print(item)
        print(item['imgUrl'], item['insctFamilyNm'], item['insctOfnmScnm'],
              item['insctPcmtt'], item['insctPilbkNo'], item['insctofnmkrlngnm'])

    # 아 벌써 힘들다


student_ui = uic.loadUiType("studentUi2.ui")[0]


class StudentClient(QWidget, student_ui):
    # 스택 0 = 메인 / 스택 1 = 개인 학습
    # 스택 2 = QnA / 스택 3 = Quiz
    # 스택 4 = 상담 / 스택 5 = 로그인
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.client_socket = None
        # self.initialize_socket('ip', 'port')
        self.clPage.setCurrentIndex(5)
        self.account = ''
        self.goStudy.clicked.connect(self.go_study)
        self.goQnA.clicked.connect(self.go_qna)
        self.goQuiz.clicked.connect(self.go_quiz)
        self.goConsulting.clicked.connect(self.go_consult)
        self.logIn.clicked.connect(self.log_in)
        self.studentName.returnPressed.connect(self.log_in)
        self.logOut.clicked.connect(self.log_out)
        self.goMain.clicked.connect(self.go_main)
        self.goMain_2.clicked.connect(self.go_main)
        self.goMain_3.clicked.connect(self.go_main)
        self.goMain_4.clicked.connect(self.go_main)

        # 소켓 설정 함수 실행
        self.initialize_socket()
        # 서버에서 메시지 보내면 응답하는 함수 스레드로 실행
        self.listen_thread()

        # QnA 질문 입력 버튼
        self.writingComplete.clicked.connect(self.send_question)

    # 소켓 설정 메서드
    def initialize_socket(self):
        ip = input("서버 IP를 입력해주세요(default=10.10.21.102): ")
        if ip == '':
            ip = '10.10.21.102'
        port = 6666

        # TCP socket을 생성하고 server와 연결
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.client_socket.connect((ip, port))

    # 질문입력 버튼 누르면 실행할 메서드
    def send_question(self):
        if not self.question_title.text():
            QMessageBox.information(self, '입력오류', '제목을 입력해주세요')
        elif not self.question_content.text():
            QMessageBox.information(self, '입력오류', '질문을 입력해주세요')
        else:
            # 인덱스 0번에 식별자 'plzInsertQuestion' 넣어주고 [질문자 이름, 제목, 질문 내용, 질문한 시간]서버로 전송
            question = ['plzInsertQuestion', self.studentName.text(), self.question_title.text(),
                                  self.question_content.text(), datetime.now().strftime('%D %T')]
            send_question = json.dumps(question)
            self.client_socket.send(send_question.encode('utf-8'))
            print('서버에 질문등록 요청을 보냈습니다')

    def go_study(self):
        self.clPage.setCurrentIndex(1)

    def go_qna(self):
        self.clPage.setCurrentIndex(2)

    def go_quiz(self):
        self.clPage.setCurrentIndex(3)

    def go_consult(self):
        self.clPage.setCurrentIndex(4)

    # 로그인 버튼 누르면 서버에 요청 보냄
    def log_in(self):
        if not bool(self.studentName.text()):
            QMessageBox.information(self, '입력 오류', '이름을 입력해주세요')
        else:
            # 인덱스 0번에 식별자 'plzCheckAccount' 넣어주고 서버로 전송
            checkAccountSignal = ['plzCheckAccount', self.studentName.text()]
            send_accountSignal = json.dumps(checkAccountSignal)
            self.client_socket.send(send_accountSignal.encode('utf-8'))
            print('서버에 로그인 요청을 보냈습니다')

    # 로그아웃 버튼 누르면 로그인 페이지로 이동
    def log_out(self):
        # 인덱스 0번에 식별자 'plzCheckAccount' 넣어주고 서버로 전송
        logoutSignal = ['plzLogoutAccount', self.studentName.text()]
        send_logoutSignal = json.dumps(logoutSignal)
        self.client_socket.send(send_logoutSignal.encode('utf-8'))
        print('서버에 로그아웃 요청을 보냈습니다')

        self.studentName.clear()
        self.fail_message.clear()
        self.clPage.setCurrentIndex(5)

    def go_main(self):
        self.clPage.setCurrentIndex(0)

    # 메시지를 받는 메서드 스레드로 실행
    def listen_thread(self):
        # 데이터 수신 thread를 생성하고 시작
        self.receiveThr = Thread(target=self.receive_message, args=(self.client_socket,), daemon=True)
        self.receiveThr.start()

    # 스레드에서 실행되는 메시지 받기 메서드. identifier번으로 식별자 구분
    def receive_message(self, so):
        while True:
            try:
                buf = so.recv(9999)
            except:
                print('연결 종료')
                break
            else:
                message_log = json.loads(buf.decode('utf-8'))
                identifier = message_log.pop(0)     # identifier = 식별자 -> 추출
                print(identifier)
                if not buf:     # 연결이 종료됨
                    print('서버에서 빈 메시지가 왔습니다')
                    break
                # 처음 입장했을 때 모든 채팅 내역 출력(예시 elif)
                elif identifier == 'success_login':
                    self.clPage.setCurrentIndex(0)
                elif identifier == 'failed_login':
                    self.fail_message.setText('로그인 실패')

    # 유저가 종료했을 경우 (함수를 따로 실행 안해도 종료하면 알아서 실행됨)
    def closeEvent(self, QCloseEvent):
        # 로그아웃 안하고 종료하면 로그아웃 시킴
        if self.clPage.currentIndex() != 5:
            self.log_out()
        # 서버에 소켓을 닫는다고 시그널 보냄
        exitsocketsignal = ['plzDisconnectSocket']
        send_exitsocketsignal = json.dumps(exitsocketsignal)  # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        self.client_socket.send(send_exitsocketsignal.encode('utf-8'))  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌
        self.client_socket.close()


if __name__ == "__main__":
    # api_test()
    app = QApplication(sys.argv)
    studentCl = StudentClient()
    studentCl.show()
    app.exec_()

# 질문 / 학생 / 제목 / 질문 내용
# 답변 / 학생 / 제목 / 답변 내용