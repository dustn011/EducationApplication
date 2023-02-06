import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from socket import *
import threading
import json

#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("teacher.ui")[0]

#화면을 띄우는데 사용되는 Class 선언
class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        self.initialize_socket()

        self.entrance_btn.clicked.connect(self.main)    # 입장버튼 누르면 메인화면 들어감
        self.update_btn.clicked.connect(self.update)    # 출제완료버튼 눌렀을 때

        self.stackedWidget.setCurrentIndex(0)

    # 소켓생성 및 서버와 연결
    def initialize_socket(self):
        ip=input('ip입력')
        port=int(input('port입력'))
        self.client_socket=socket(AF_INET,SOCK_STREAM)
        self.client_socket.connect((ip,port))

    # 첫번째 페이지에서 메인화면으로 들어옴
    def main(self):
        self.stackedWidget.setCurrentIndex(1)

    # 출제완료 버튼 눌렀을 때
    def update(self):
        up_field=self.update_comboBox.currentText()
        up_title=self.update_title.text().strip()
        up_content=self.update_content.toPlainText().strip()
        up_answer=self.update_answer.text().strip()
        if up_field == '선택' :
            self.update_label.setText('분야 입력요망')
        elif up_title == '':
            self.update_title_label.setText('제목 입력요망')
        elif up_content == '':
            self.update_content_label.setText('내용 입력요망')
        elif up_answer == '':
            self.update_answer_label.setText('정답입력요망')
        else:
            self.update_label.setText('')
            self.update_title_label.setText('')
            self.update_content_label.setText('')
            self.update_answer_label.setText('')
            self.update_title.clear()
            self.update_content.clear()
            self.update_answer.clear()
            update=['teacher_update',f'{up_field}',f'{up_title}',f'{up_content}',f'{up_answer}']
            self.client_socket.send((json.dumps(update)).encode())

    def receive_message(self,socket):
        while True:
            try:
                buf=socket.recv(9999)
                if not buf:
                    break
            except Exception as e:
                print(e)
            else:
                recv_data=buf.decode()
                # print(recv_data)


if __name__ == "__main__" :
    app = QApplication(sys.argv)        #QApplication : 프로그램을 실행시켜주는 클래스
    myWindow = WindowClass()            #WindowClass의 인스턴스 생성
    myWindow.show()                     #프로그램 화면을 보여주는 코드
    Thread=threading.Thread(target=myWindow.receive_message, args=(myWindow.client_socket,))
    Thread.daemon=True
    Thread.start()
    app.exec_()                         #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
























































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































