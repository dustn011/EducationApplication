import json
import requests
import xmltodict
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
from socket import *
from threading import *
from datetime import datetime


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
    print(diction)
    # 아래 과정은 json 기능을 공부해야 이해할 듯
    # json.dumps를 이용해서 문자열화(데이터를 보낼때 이렇게 바꿔주면 될듯)
    json_string = json.dumps(diction, ensure_ascii=False)
    # 데이터 불러올 때(딕셔너리 형태로 받아옴)
    json_obj = json.loads(json_string)
    print(json_obj)
    # diction 과 json_obj의 차이점이 뭔지 모르겠다
    # print 결과는 똑같아 보이는데

    # <response> 속 <body> 속 <items> 속 <item> 의 각 요소들
    # response 딕셔너리의 body 딕셔너리의 items 딕셔너리의 item 딕셔너리의 각 key 요소들의 value값을 가져왔음
    for item in diction['response']['body']['items']['item']:
        # print(item)
        print(item['imgUrl'], item['insctFamilyNm'], item['insctOfnmScnm'],
              item['insctPcmtt'], item['insctPilbkNo'], item['insctofnmkrlngnm'])

    # 아 벌써 힘들다


student_ui = uic.loadUiType("studentUi.ui")[0]


class StudentClient(QWidget, student_ui):
    # 스택 0 = 메인 / 스택 1 = 개인 학습
    # 스택 2 = QnA / 스택 3 = Quiz
    # 스택 4 = 상담 / 스택 5 = 로그인
    # 학습 기능이랑 퀴즈 구현하기
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.client_socket = None
        self.initialize_socket('10.10.21.129', 6666)
        self.listen_thread()
        self.clPage.setCurrentIndex(0)
        self.account = ''
        # 탭과 일치하는 퀴즈 목록
        self.questions = None
        # 퀴즈 테이블에서 선택한 셀의 row값
        self.row = 0
        # 학습 페이지 이동
        self.goStudy.clicked.connect(self.go_study)
        # QnA 페이지 이동
        self.goQnA.clicked.connect(self.go_qna)
        # 퀴즈 페이지 이동
        self.goQuiz.clicked.connect(self.go_quiz)
        # 상담 페이지 이동
        self.goConsulting.clicked.connect(self.go_consult)
        # 로그인 / 로그아웃
        self.logIn.clicked.connect(self.log_in)
        self.studentName.returnPressed.connect(self.log_in)
        self.logOut.clicked.connect(self.log_out)
        # 메인 페이지로 이동
        self.goMain.clicked.connect(self.go_main)
        self.goMain_2.clicked.connect(self.go_main)
        self.goMain_3.clicked.connect(self.go_main)
        self.goMain_4.clicked.connect(self.go_main)
        # 퀴즈 목록 가져오기
        self.showQuestions.clicked.connect(self.show_quiz)
        # 퀴즈 선택하기
        self.questionList.cellClicked.connect(self.cell_click)
        # 답 제출
        self.sendAnswer.clicked.connect(self.answer)
        self.answerText.returnPressed.connect(self.answer)

    def initialize_socket(self, ip, port):
        # TCP socket을 생성하고 server와 연결
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        remote_ip = ip
        remote_port = port
        self.client_socket.connect((remote_ip, remote_port))

    # 학습 페이지로 이동
    def go_study(self):
        self.clPage.setCurrentIndex(1)

    # QnA 페이지로 이동
    def go_qna(self):
        self.clPage.setCurrentIndex(2)

    # 퀴즈 페이지로 이동
    def go_quiz(self):
        self.clPage.setCurrentIndex(3)

    # 상담 페이지로 이동
    def go_consult(self):
        self.clPage.setCurrentIndex(4)

    # 로그인
    def log_in(self):
        if self.studentName.text():
            self.account = self.studentName.text()
            print(self.account)
            self.clPage.setCurrentIndex(0)

    # 로그아웃
    def log_out(self):
        self.clPage.setCurrentIndex(5)

    # 메인 페이지로 이동
    def go_main(self):
        self.clPage.setCurrentIndex(0)

    # 퀴즈 목록 받아오기
    def show_quiz(self):
        # 현재 탭의 정보 저장
        now_tab = self.classTab.tabText(self.classTab.currentIndex())
        # 요청 코드와 탭 이름 전달
        show_quiz = json.dumps(["plzGiveQuiz", now_tab])
        self.client_socket.send(show_quiz.encode('utf-8'))

    # 테이블에서 셀 클릭했을 때 퀴즈 내용 출력하기
    def cell_click(self, row):
        self.row = row
        self.quizText.clear()
        self.answerText.clear()
        self.exact.clear()
        self.quizText.append(self.questions[row][1] + "\n")
        self.quizText.append(self.questions[row][2])

    # 정답 제출
    def answer(self):
        if self.questionList.item(self.row, 1).text() == "해결 안됨":
            # 답이 맞으면
            if self.answerText.text() == self.questions[self.row][3]:
                self.score.setText(str(int(self.score.text()) + 10))
                self.exact.setText("정답!")
            # 답이 틀리면
            else:
                self.exact.setText("땡!!")
            self.answerText.clear()
        self.questionList.setItem(self.row, 1, QTableWidgetItem("해결"))

    def listen_thread(self):
        # 데이터 수신 Tread를 생성하고 시작한다
        t = Thread(target=self.receive_message, args=(self.client_socket,))
        t.start()

    def receive_message(self, so):
        while True:
            try:
                buf = so.recv(9999)
            except:
                print('연결 종료')
                break
            else:
                message_log = json.loads(buf.decode('utf-8'))
                identifier = message_log.pop(0)  # identifier = 식별자 -> 추출
                print(identifier)
                if not buf:  # 연결이 종료됨
                    print('서버에서 빈 메시지가 왔습니다')
                    break
                # hereQuiz = 퀴즈 목록 코드
                elif identifier == "hereQuiz":
                    # 쓸데없이 3중 리스트로 돼있어서 2중으로 줄임
                    self.questions = message_log[0]
                    print(self.questions)
                    # 퀴즈 갯수만큼 행 생성
                    self.questionList.setRowCount(len(self.questions))
                    for row in range(len(self.questions)):
                        for col in range(2):
                            # 제목 칸에 제목 넣기
                            if col == 0:
                                self.questionList.setItem(row, col, QTableWidgetItem("%s" % self.questions[row][1]))
                            # 해결 여부 넣기 (임시로 탭 '해결 안됨'으로 넣음)
                            else:
                                self.questionList.setItem(row, col, QTableWidgetItem("해결 안됨"))
                    # 테이블 컬럼 길이 재설정
                    self.questionList.resizeColumnsToContents()

    # 유저가 종료했을 경우 (함수를 따로 실행 안해도 종료하면 알아서 실행됨)
    def closeEvent(self, QCloseEvent):
        # 서버에 소켓을 닫는다고 시그널 보냄
        exitsocketsignal = ['plzDisconnectSocket']
        send_exitsocketsignal = json.dumps(exitsocketsignal)  # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        self.client_socket.send(send_exitsocketsignal.encode('utf-8'))  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌
        self.client_socket.close()


if __name__ == "__main__":
    api_test()
    app = QApplication(sys.argv)
    studentCl = StudentClient()
    studentCl.show()
    app.exec_()
    
# 질문 / 학생 / 제목 / 질문 내용
# 답변 / 학생 / 제목 / 답변 내용
