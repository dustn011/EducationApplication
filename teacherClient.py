import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from socket import *
import threading
import json
import datetime

from matplotlib import font_manager,rc
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

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

        self.insect_btn.clicked.connect(self.insect)              # 곤충버튼 눌렀을 때
        self.mammalia_btn.clicked.connect(self.mammalia)          # 포유류 눌렀을 때
        self.bird_btn.clicked.connect(self.bird)                  # 조류 눌렀을 때

        # QNA 헤더, 열
        header=['학생','질문','답변여부']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableWidget.horizontalHeader().resizeSection(0, 40)
        self.tableWidget.horizontalHeader().resizeSection(2, 60)

        # 전체 ui 구성 스텍위젯
        self.stackedWidget.setCurrentIndex(0)

        # 학습현황 ui 구성 스텍위젯
        self.stackedWidget_2.setCurrentIndex(2)

        # 상담 시작 버튼
        self.btn_startConsulting.clicked.connect(self.method_start_consulting)

        # 곤충, 포유류, 조류 헤더, 열
        self.header_col()

        self.fig = plt.Figure()
        self.fig2 = plt.Figure()
        self.fig3 = plt.Figure()

        self.canvas = FigureCanvas(self.fig)
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas3 = FigureCanvas(self.fig3)

        self.verticalLayout.addWidget(self.canvas)
        self.verticalLayout_2.addWidget(self.canvas2)
        self.verticalLayout_3.addWidget(self.canvas3)

        self.state_list = [self.table_st_mammalia, \
                      self.Q1_2, self.Q2_2, self.Q3_2, self.Q4_2, self.Q5_2, \
                      self.m_m, self.m_s, self.m_y, self.table_st_bird, \
                      self.Q1_3, self.Q2_3, self.Q3_3, self.Q4_3, self.Q5_3, \
                      self.j_m, self.j_s, self.j_y, \
                      self.table_st_insect, \
                      self.Q1, self.Q2, self.Q3, self.Q4, self.Q5, \
                      self.insect_m, self.insect_s, self.insect_y, \
                      self.in_m, self.in_s, self.in_y]


    # 곤충, 포유류, 조류 헤더, 열
    def header_col(self):
        # 곤충 교과별 현황 헤더, 열
        header = ['학생', '문제1', '문제2', '문제3', '문제4', '문제5', '점수']
        self.table_st_insect.setColumnCount(len(header))
        self.table_st_insect.setHorizontalHeaderLabels(header)
        self.table_st_insect.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_st_insect.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_st_insect.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_st_insect.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_st_insect.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_st_insect.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table_st_insect.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table_st_insect.horizontalHeader().resizeSection(0, 50)

        # 포유류 교과별 현황 헤더, 열
        header = ['학생', '문제1', '문제2', '문제3', '문제4', '문제5', '점수']
        self.table_st_mammalia.setColumnCount(len(header))
        self.table_st_mammalia.setHorizontalHeaderLabels(header)
        self.table_st_mammalia.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_st_mammalia.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_st_mammalia.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_st_mammalia.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_st_mammalia.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_st_mammalia.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table_st_mammalia.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table_st_mammalia.horizontalHeader().resizeSection(0, 50)

        # 조류 교과별 현황 헤더, 열
        header = ['학생', '문제1', '문제2', '문제3', '문제4', '문제5', '점수']
        self.table_st_bird.setColumnCount(len(header))
        self.table_st_bird.setHorizontalHeaderLabels(header)
        self.table_st_bird.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table_st_bird.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_st_bird.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_st_bird.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_st_bird.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table_st_bird.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table_st_bird.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table_st_bird.horizontalHeader().resizeSection(0, 50)

    # 상담 시작 버튼
    def method_start_consulting(self):
        if self.consulting_combo.currentText():
            message = ['plzStartConsulting', self.consulting_combo.currentText()]
            self.client_socket.send((json.dumps(message)).encode())
        else:
            QMessageBox.information(self, '선택오류', '상담할 학생을 선택해주세요')


    # 곤충분야눌렀을 때
    def insect(self):
        self.stackedWidget_2.setCurrentIndex(1)
        message=['teacher_ststate_insect']
        self.client_socket.send((json.dumps(message)).encode())

    # 포유류 눌렀을 때
    def mammalia(self):
        self.stackedWidget_2.setCurrentIndex(0)
        message=['teacher_ststate_mammalia']
        self.client_socket.send((json.dumps(message)).encode())

    # 조류 눌렀을 때
    def bird(self):
        self.stackedWidget_2.setCurrentIndex(3)
        message=['teacher_ststate_bird']
        self.client_socket.send((json.dumps(message)).encode())

    # 새로고침버튼 눌렀을 때 현재접속자 수, 실시간상담 학생 수 바꾸기
    def f5(self):
        self.consulting_show.clear()
        self.send_btn.setEnabled(True)
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
            self.consulting_show.scrollToBottom()
            # 서버로 보내기
            send_message=['teacher_send_message','manager',f'{send_m}',f'{student}']
            self.client_socket.send((json.dumps(send_message)).encode())
            # 전송한 메시지 삭제
            self.consulting_line.clear()

    # 소켓생성 및 서버와 연결
    def initialize_socket(self):
        ip='10.10.21.124'
        port=6666
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
                # 실시간 상담시 접속종료되면 접속종료시키기
                elif identifier == 'teacher_account_delete':
                    self.current_delete()
                # 학습현황 곤충분야 선택했을 때
                elif identifier == 'teacher_ststate_insect':
                    print(type(self.table_st_insect))
                    # self.insect_state()
                    self.i_m_b_state(18)
                # 학습현황 포유류분야 선택했을 때
                elif identifier == 'teacher_ststate_mammalia':
                    # self.mammalia_state()
                    self.i_m_b_state(0)
                # 학습현황 조류분야 선택했을 때
                elif identifier == 'teacher_ststate_bird':
                    # self.bird_state()
                    self.i_m_b_state(9)

    # 곤충, 포유류, 조류 선택했을 때
    def i_m_b_state(self,num):
        font_path = "C:\\Windows\\Fonts\\gulim.ttc"
        font = font_manager.FontProperties(fname=font_path).get_name()
        rc('font', family=font)

        temp = []
        state = self.received_message[0]
        wrong = self.received_message[1]
        jindo = self.received_message[2]

        self.state_list[num].setRowCount(len(state))
        # 테이블 위젯에 띄우기
        for i in range(len(state)):
            self.state_list[num].setItem(i, 0, QTableWidgetItem(str(state[i][0])))  # 학생명
            self.state_list[num].setItem(i, 1, QTableWidgetItem(str(state[i][2])))  # 문제1
            self.state_list[num].setItem(i, 2, QTableWidgetItem(str(state[i][3])))  # 문제2
            self.state_list[num].setItem(i, 3, QTableWidgetItem(str(state[i][4])))  # 문제3
            self.state_list[num].setItem(i, 4, QTableWidgetItem(str(state[i][5])))  # 문제4
            self.state_list[num].setItem(i, 5, QTableWidgetItem(str(state[i][6])))  # 문제5
            self.state_list[num].setItem(i, 6, QTableWidgetItem(str(state[i][1])))  # 점수

        # 오답률 보이기
        for i in range(len(wrong[0])):
            temp.append(int(wrong[0][i] / len(state) * 100))
        self.state_list[num+1].setText(f'{temp[0]}%')
        self.state_list[num+2].setText(f'{temp[1]}%')
        self.state_list[num+3].setText(f'{temp[2]}%')
        self.state_list[num+4].setText(f'{temp[3]}%')
        self.state_list[num+5].setText(f'{temp[4]}%')

        # 라벨에 현재 진행현황 보이기
        self.state_list[num+6].setText(f'{jindo[0][0]}%')
        self.state_list[num+7].setText(f'{jindo[2][0]}%')
        self.state_list[num+8].setText(f'{jindo[1][0]}%')

        # 포유류 그래프 넣기
        if num == 0:
            ax3 = self.fig3.add_subplot(111)  # 버티컬 레이아웃에 딱맞게 들어감.
            # ax3.set_xlabel("QUiZ NUMBER", size=10)
            # ax3.set_ylabel("%", size=10)
            ax3.set_xlim([0, 6])
            ax3.set_ylim([0, 120])
            ax3.set_title("포유류 오답률 그래프")

            x = np.array([1, 2, 3, 4, 5])
            y = np.array([temp[0], temp[1], temp[2], temp[3], temp[4]])

            ax3.scatter(x, y, marker='*', color='black')
            self.canvas3.draw()

        # 조류 그래프 넣기
        if num == 9:
            ax = self.fig.add_subplot(111)  # 버티컬 레이아웃에 딱맞게 들어감.
            ax.set_xlim([0, 6])
            ax.set_ylim([0, 120])
            ax.set_title("조류 오답률 그래프")

            x = np.array([1, 2, 3, 4, 5])
            y = np.array([temp[0], temp[1], temp[2], temp[3], temp[4]])

            ax.scatter(x, y, marker='*', color='black')
            self.canvas.draw()

        # 곤충 그래프 넣기
        if num == 18:

            jindo2 = self.received_message[3]

            self.state_list[num+9].setText(f'{jindo2[0][0]}%')
            self.state_list[num+10].setText(f'{jindo2[2][0]}%')
            self.state_list[num+11].setText(f'{jindo2[1][0]}%')

            ax2 = self.fig2.add_subplot(111)  # 버티컬 레이아웃에 딱맞게 들어감.
            ax2.set_xlim([0, 6])
            ax2.set_ylim([0, 120])
            ax2.set_title("곤충 오답률 그래프")

            x = np.array([1, 2, 3, 4, 5])
            y = np.array([temp[0], temp[1], temp[2], temp[3], temp[4]])

            ax2.scatter(x, y, marker='*', color='black')
            self.canvas2.draw()

    # 상대방 접속종료시 전송버튼 안눌리도록 함, 접속종료안내멘트 전달
    def current_delete(self):
        self.received_message=self.received_message[0]
        self.current_num()  # 접속종료시 현재접속인원 바꾸기
        # 현재 접속한 인원이 아무도 없는경우
        if len(self.received_message) == 0:
            if self.consulting_combo.currentText() == '':
                self.send_btn.setEnabled(False)
            else:
                self.consulting_show.addItem(f'---------------------- 상대방이 접속을 종료했습니다 ---------------------')
                self.consulting_show.addItem(f'----------------------------- 새로고침 하세요 -----------------------------')
                self.consulting_show.scrollToBottom()
                self.send_btn.setEnabled(False)
        # 한명이상 접속한 인원이 있는 경우
        else:
            for i in range(len(self.received_message)):
                if self.consulting_combo.currentText() =='':
                    self.send_btn.setEnabled(False)
                elif str(self.received_message[i]) != self.consulting_combo.currentText():
                    self.current_num()  # 접속종료시 현재접속인원 바꾸기
                    self.consulting_show.addItem(f'---------------------- 상대방이 접속을 종료했습니다 ---------------------')
                    self.consulting_show.addItem(f'----------------------------- 새로고침 하세요 -----------------------------')
                    self.consulting_show.scrollToBottom()
                    self.send_btn.setEnabled(False)
                else:
                    pass

    # 접속종료시 현재접속인원 바꾸기, 접속종료안내멘트보내기
    def current_num(self):
        self.current_man.clear()
        for i in self.received_message:
            self.current_man.addItem(f'{i}')
        self.man_num.setText(f'[{len(self.received_message)}] 명')

    # 접속한 학생으로 명단띄움, 현재 접속자 띄우기
    def chat_state(self):
        self.current_man.clear()
        self.consulting_combo.clear()
        self.consulting_combo.addItem(f'')
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
        if self.consulting_combo.currentText() == f'{chat[0]}':
            self.consulting_show.addItem(f'[{chat[2]}] [{chat[0]}] {chat[1]}')
            self.consulting_show.scrollToBottom()
        else:
            pass

    # 이전채팅내역 보여주기
    def pre_chat(self):
        self.received_message=self.received_message[0]              # 이거 민석님 일지보고 배워옴!!!
        print(self.received_message)
        if self.consulting_combo.currentText() == '':
            pass
        else:
            for i in self.received_message:
                self.consulting_show.addItem(f'[{i[0]}] [{i[1]}] {i[2]}')
            self.consulting_show.scrollToBottom()
            self.consulting_show.addItem(f'--------------------------------- 이전내역 ---------------------------------')

    # 첫번째 페이지에서 메인화면으로 들어옴
    def main(self):
        self.stackedWidget.setCurrentIndex(1)
        self.tabWidget.setCurrentIndex(0)
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
