import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from socket import *
import threading
import json
import datetime

#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("teacher.ui")[0]

#화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.initialize_socket()                        # 소켓생성 및 서버와 연결

        self.entrance_btn.clicked.connect(self.main)    # 초기화면 입장버튼 누르면 메인화면 들어감
        self.update_btn.clicked.connect(self.update)    # 문제 update 출제완료버튼 눌렀을 때
        self.QA_send_btn.clicked.connect(self.QNA)      # QNA 작성완료버튼 눌렀을 때
        self.tableWidget.cellDoubleClicked.connect(self.qna_doubleclick) # QNA 더블클릭했을 때
        self.consulting_line.returnPressed.connect(self.consulting_send)
        self.send_btn.clicked.connect(self.consulting_send)         # 실시간상담에서 전송버튼 눌렀을 떄
        self.consulting_combo.currentIndexChanged.connect(self.send_stname) # 실시간상담에서 학생이름이 선택되었을때
        self.f5_btn.clicked.connect(self.f5)                                # 현재접속자에서 새로고침 누르면

        # 헤더, 열
        header=['학생','질문','답변여부']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().resizeSection(0, 30)
        self.tableWidget.horizontalHeader().resizeSection(2, 60)

        self.stackedWidget.setCurrentIndex(0)

    # 새로고침버튼 눌렀을 때 현재접속자 수, 실시간상담 학생 수 바꾸기
    def f5(self):
        message=['teacher_consulting_st']
        self.client_socket.send((json.dumps(message)).encode())

    # 실시간상담에서 학생이름이 선택되었을때
    def send_stname(self):
        self.consulting_show.clear()
        # 실시간상담, chat 내역 가져올 수 있도록 서버로 보내기
        name=self.consulting_combo.currentText()
        consulting_chat=['teacher_consulting_ch',f'{name}']
        print(consulting_chat)
        self.client_socket.send((json.dumps(consulting_chat)).encode())

    # 실시간상담에서 전송눌렀을 떄
    def consulting_send(self):
        if self.consulting_line.text() == '':
            pass
        elif self.consulting_combo.currentText() == '':
            pass
        else:
            # 콤보박스 학생이름, 라인에딧 전송한 메시지 가져오기
            student = self.consulting_combo.currentText()
            send_m=self.consulting_line.text()
            time=datetime.datetime.now().strftime("%D,%T")
            # 상담화면에 띄우기
            self.consulting_show.addItem(f'[{time}] [manager] {send_m}')
            # 서버로 보내기
            send_message=['teacher_send_message','manager',f'{send_m}',f'{student}']
            self.client_socket.send((json.dumps(send_message)).encode())
            # 전송한 메시지 삭제
            self.consulting_line.clear()

    # 소켓생성 및 서버와 연결
    def initialize_socket(self):
        ip=input('ip입력')
        port=int(input('port입력'))
        self.client_socket=socket(AF_INET,SOCK_STREAM)
        self.client_socket.connect((ip,port))

    def receive_message(self,socket):
        while True:
            try:
                buf=socket.recv(9999)
                if not buf:
                    break
            except:
                print('연결 종료')
                break
            else:
                self.received_message = json.loads(buf.decode('utf-8'))
                print(self.received_message)
                identifier = self.received_message.pop(0)
                # QNA 받기
                if identifier == 'teacher_QNA':
                    self.qna_show()
                # 접속한 학생으로 명단띄움, 현재 접속자 띄우기
                elif identifier == 'teacher_consulting_st':
                    self.chat_state()
                # 실시간상담 이전내역 불러오기
                elif identifier == 'teacher_consulting_ch':
                    self.pre_chat()
                # 실시간상담 학생이 보낸 내용 불러오기
                elif identifier == 'teacher_send_message':
                    self.chat_st()

    # 접속한 학생으로 명단띄움, 현재 접속자 띄우기
    def chat_state(self):
        self.current_man.clear()
        self.consulting_combo.clear()
        self.received_message = self.received_message[0]
        for i in range(len(self.received_message)):
            self.consulting_combo.addItem(f'{self.received_message[i]}')
        for i in self.received_message:
            self.current_man.addItem(f'{i}')
        self.man_num.setText(f'[{len(self.received_message)}] 명')

    # 학생쪽에서 온 채팅을 받아 띄움
    def chat_st(self):
        # self.received_message = [self.studentName.text(), self.send_chat.text()]
        chat = self.received_message
        self.consulting_show.addItem(f'[{chat[2]}] [{chat[0]}] {chat[1]}')

    # 이전채팅내역 보여주기
    def pre_chat(self):
        self.received_message=self.received_message[0]              # 이거 민석님 일지보고 배워옴!!!
        print(self.received_message)
        for i in self.received_message:
            self.consulting_show.addItem(f'[{i[0]}] [{i[1]}] {i[2]}')
        self.consulting_show.addItem(f'--------------------------------- 이전내역 ---------------------------------')

    # 첫번째 페이지에서 메인화면으로 들어옴
    def main(self):
        self.stackedWidget.setCurrentIndex(1)
        # 교수 접속내용 확인할 수 있도록 서버로 보내기
        account = ['teacher_account']
        self.client_socket.send((json.dumps(account)).encode())

    # QNA 작성완료 버튼 눌렀을 때
    def QNA(self):
        qna_answer = self.QA_answer.toPlainText().strip()
        if qna_answer == '':
            self.alarm_label.setText('작성내용확인요망')
        else:
            num = self.qna[self.row][0]
            # self.tableWidget.clearContents()          # 구지 안해도 됨...
            qna_answer_list=['teacher_qna_answer',f'{qna_answer}','완료',f'{num}']
            # 서버로 전송
            self.client_socket.send((json.dumps(qna_answer_list)).encode())
            # 제목, 작성자, 내용, 답변 초기화
            self.title_browser.clear()
            self.man_browser.clear()
            self.content_browser.clear()
            self.QA_answer.clear()
            self.alarm_label.setText('')

    # qna내역 테이블 위젯에 띄우기
    def qna_show(self):
        # DB에서 가져온 데이터 None값 바꾸기
        self.qna = []
        for i in range(len(self.received_message[0])):
            temp1 = []
            for j in range(len(self.received_message[0][0])):
                if bool(self.received_message[0][i][j]) == False:
                    temp1.append('')
                else:
                    temp1.append(self.received_message[0][i][j])
            self.qna.append(temp1)
        print(self.qna)
        self.tableWidget.setRowCount(len(self.qna))
        # 테이블 위젯에 띄우기
        for i in range(len(self.qna)):
            self.tableWidget.setItem(i,0,QTableWidgetItem(str(self.qna[i][1]))) # 작성자명
            self.tableWidget.setItem(i,1,QTableWidgetItem(str(self.qna[i][2]))) # QNA제목
            self.tableWidget.setItem(i,2,QTableWidgetItem(str(self.qna[i][7]))) # 답변상태

    # qna 셀 더블클릭시
    def qna_doubleclick(self):
        self.row=self.tableWidget.currentRow()                 # 행 번호 가져오기
        title=self.tableWidget.item(self.row,1).text()         # 행의 제목 가져오기
        self.title_browser.setPlainText(f'{title}')
        man=self.tableWidget.item(self.row,0).text()           # 행의 작성자명 가져오기
        self.man_browser.setPlainText(f'{man}')
        content = self.qna[self.row][3]                        # 행의 내용 가져오기
        self.content_browser.setPlainText(f'{content}')
        answer = self.qna[self.row][5]                         # 행의 답변내용 가져오기
        self.QA_answer.setText(f'{answer}')

    # 출제완료 버튼 눌렀을 때
    def update(self):
        # 분야, 제목, 내용, 정답 입력 내용 가져오기
        up_field=self.update_comboBox.currentText()
        up_title=self.update_title.text().strip()
        up_content=self.update_content.toPlainText().strip()
        up_answer=self.update_answer.text().strip()
        # 입력 내용들 누락시 알림
        if up_field == '선택' :
            self.check_label.setText('전체내용 입력요망')
        elif up_title == '':
            self.check_label.setText('전체내용 입력요망')
        elif up_content == '':
            self.check_label.setText('전체내용 입력요망')
        elif up_answer == '':
            self.check_label.setText('전체내용 입력요망')
        # 모두 입력되었을 때
        else:
            # 누락시 알림한 내용, 입력내용 clear,
            self.check_label.setText('')
            self.update_title.clear()
            self.update_content.clear()
            self.update_answer.clear()
            # 서버로 전송
            update=['teacher_update',f'{up_field}',f'{up_title}',f'{up_content}',f'{up_answer}']
            self.client_socket.send((json.dumps(update)).encode())

    # 유저가 종료했을 경우 (함수를 따로 실행 안해도 종료하면 알아서 실행됨)
    def closeEvent(self, QCloseEvent):
        self.client_socket.send((json.dumps(['plzLogoutAccount','manager'])).encode('utf-8'))
        # 서버에 소켓을 닫는다고 시그널 보냄
        exitsocketsignal = ['plzDisconnectSocket']
        send_exitsocketsignal = json.dumps(exitsocketsignal)  # json.dumps로 리스트의 값들 바이트형으로 바꿔줌
        self.client_socket.send(send_exitsocketsignal.encode('utf-8'))  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌
        self.client_socket.close()

if __name__ == "__main__" :
    app = QApplication(sys.argv)        #QApplication : 프로그램을 실행시켜주는 클래스
    myWindow = WindowClass()            #WindowClass의 인스턴스 생성
    myWindow.show()                     #프로그램 화면을 보여주는 코드
    Thread=threading.Thread(target=myWindow.receive_message, args=(myWindow.client_socket,))
    Thread.daemon=True
    Thread.start()
    app.exec_()                         #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
