import json
import requests
import xmltodict
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import sys
from socket import *
from threading import *
import urllib.request

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
        self.clPage.setCurrentIndex(5)
        self.account = ''
        # 탭과 일치하는 퀴즈 목록
        self.questions = None
        # 학생의 퀴즈 진도
        self.rate = None
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
        self.url = 'http://www.nature.go.kr/fileUpload/photo/O1/ZOEC0011_1.jpg'
        self.insect = urllib.request.urlopen(self.url).read()
        self.pixmap = QPixmap()
        self.pixmap.loadFromData(self.insect)
        self.pixmap = self.pixmap.scaledToHeight(400)
        self.insectImage.setPixmap(self.pixmap)

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
        if not bool(self.studentName.text()):
            QMessageBox.information(self, '입력 오류', '이름을 입력해주세요')
        else:
            # 인덱스 0번에 식별자 'plzCheckAccount' 넣어주고 서버로 전송
            check_account_signal = ['plzCheckAccount', self.studentName.text()]
            send_account_signal = json.dumps(check_account_signal)
            self.client_socket.send(send_account_signal.encode('utf-8'))
            print('서버에 로그인 요청을 보냈습니다')
            # 유저 이름을 저장하고 퀴즈 목록을 불러옴
            self.account = self.studentName.text()
            self.show_quiz()

    # 로그아웃
    def log_out(self):
        # 인덱스 0번에 식별자 'plzCheckAccount' 넣어주고 서버로 전송
        logout_signal = ['plzLogoutAccount', self.studentName.text()]
        send_logout_signal = json.dumps(logout_signal)
        self.client_socket.send(send_logout_signal.encode('utf-8'))
        print('서버에 로그아웃 요청을 보냈습니다')

        self.studentName.clear()
        self.fail_message.clear()
        self.clPage.setCurrentIndex(5)

    # 메인 페이지로 이동
    def go_main(self):
        self.clPage.setCurrentIndex(0)

    # 퀴즈 목록 받아오기
    def show_quiz(self):
        # 현재 탭의 정보 저장
        now_tab = self.classTab.tabText(self.classTab.currentIndex())
        # 요청 코드와 탭 이름, 학생 이름 전달
        show_quiz = json.dumps(["plzGiveQuiz", now_tab, self.account])
        self.client_socket.send(show_quiz.encode('utf-8'))

    # 테이블에서 셀 클릭했을 때 퀴즈 내용 출력하기
    def cell_click(self, row):
        self.row = row
        self.quizText.clear()
        self.answerText.clear()
        self.exact.clear()
        self.quizText.append(self.questions[row][2] + "\n")
        self.quizText.append(self.questions[row][3])

    # 정답 제출
    def answer(self):
        # 현재 탭 저장
        now_tab = self.classTab.tabText(self.classTab.currentIndex())
        # 풀지 않은 문제였을 때
        if self.questionList.item(self.row, 1).text() == "-":
            # 정답을 출력
            self.correct.setText("정답 : " + self.questions[self.row][4])
            # 답이 맞으면
            if self.answerText.text() == self.questions[self.row][4]:
                # 현재 점수에 점수를 추가 (문제 당 10점)
                self.score.setText(str(int(self.score.text()) + 10))
                self.exact.setText("정답!")
                # 테이블에 바로 결과 반영
                self.questionList.setItem(self.row, 1, QTableWidgetItem("정답"))
                # 서버에 데이터 수정을 요청
                self.client_socket.send(json.dumps(["hereAnswer",
                                                    now_tab, self.account, self.row + 1, '정답',
                                                    self.score.text()]).encode('utf-8'))
            # 답이 틀리면
            else:
                self.exact.setText("땡!!")
                # 테이블에 바로 결과 반영
                self.questionList.setItem(self.row, 1, QTableWidgetItem("오답"))
                # 서버에 데이터 수정을 요청
                self.client_socket.send(json.dumps(["hereAnswer",
                                                    now_tab, self.account, self.row + 1, '오답',
                                                    self.score.text()]).encode('utf-8'))
            # 입력했던 답 지우기
            self.answerText.clear()

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
                        self.questionList.setItem(row, 0, QTableWidgetItem("%s" % self.questions[row][2]))
                    # 테이블 컬럼 길이 재설정
                    self.questionList.resizeColumnsToContents()
                # hereRate = 학생의 퀴즈 진도 코드
                elif identifier == "hereRate":
                    self.rate = message_log[0][0]
                    self.score.setText(str(self.rate[1]))
                    for row in range(len(self.rate) - 2):
                        self.questionList.setItem(row, 1, QTableWidgetItem("%s" % self.rate[row + 2]))
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

    # api 가져오기
    def api_test(self):
        # API
        # 인증키 저장
        key = "jAB8gOQ%2BEjRxryPTRcGIWjS6sTl2FCowle%2Bb%2FVaRrcoCuQZTgCIEID85tLqWiPIfuY4%2FzUsqf81dQj6dYuTyYg%3D%3D"

        # 인증키 정보가 들어간 url 저장 (요청)
        url = f'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctPrtctList?serviceKey={key}'

        # request 모듈을 이용해서 정보 가져오기(byte형태로 가져와지는듯)
        content = requests.get(url).content
        # xmltodict 모듈을 이용해서 딕셔너리화 & 한글화
        diction = xmltodict.parse(content)
        # # 아래 과정은 json 기능을 공부해야 이해할 듯
        # # json.dumps를 이용해서 문자열화(데이터를 보낼때 이렇게 바꿔주면 될듯)
        # json_string = json.dumps(diction, ensure_ascii=False)
        # # 데이터 불러올 때(딕셔너리 형태로 받아옴)
        # json_obj = json.loads(json_string)

        # <response> 속 <body> 속 <items> 속 <item> 의 각 요소들
        # response 딕셔너리의 body 딕셔너리의 items 딕셔너리의 item 딕셔너리의 각 key 요소들의 value값을 가져왔음
        for item in diction['response']['body']['items']['item']:
            # print(item)
            print(item['imgUrl'], item['insctFamilyNm'], item['insctOfnmScnm'],
                  item['insctPcmtt'], item['insctPilbkNo'], item['insctofnmkrlngnm'])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    studentCl = StudentClient()
    studentCl.show()
    studentCl.api_test()
    app.exec_()
