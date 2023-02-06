import json
import requests
import xmltodict
from PyQt5.QtWidgets import *
from PyQt5 import uic
import sys
# from bs4 import BeautifulSoup ?

# 인증키 저장
key = "jAB8gOQ%2BEjRxryPTRcGIWjS6sTl2FCowle%2Bb%2FVaRrcoCuQZTgCIEID85tLqWiPIfuY4%2FzUsqf81dQj6dYuTyYg%3D%3D"

# 인증키 정보가 들어간 url 저장
url = f'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctPrtctList?serviceKey={key}'

content = requests.get(url).content                     # request 모듈을 이용해서 정보 가져오기(byte형태로 가져와지는듯)
diction = xmltodict.parse(content)                      # xmltodict 모듈을 이용해서 딕셔너리화 & 한글화
jsonString = json.dumps(diction, ensure_ascii=False)    # json.dumps를 이용해서 문자열화(데이터를 보낼때 이렇게 바꿔주면 될듯)
jsonObj = json.loads(jsonString)                        # 데이터 불러올 때(딕셔너리 형태로 받아옴)

for item in jsonObj['response']['body']['items']['item']:
    # print(item)
    print(item['imgUrl'], item['insctFamilyNm'], item['insctOfnmScnm'],
          item['insctPcmtt'], item['insctPilbkNo'], item['insctofnmkrlngnm'])

# 아 벌써 힘들다

student_ui = uic.loadUiType("studentUi.ui")[0]


class StudentClient(QWidget, student_ui):
    # 스택 0 = 메인 / 스택 1 = 개인 학습
    # 스택 2 = QnA / 스택 3 = Quiz
    # 스택 4 = 상담 / 스택 5 = 로그인
    def __init__(self):
        super().__init__()
        self.setupUi(self)
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

    def go_study(self):
        self.clPage.setCurrentIndex(1)

    def go_qna(self):
        self.clPage.setCurrentIndex(2)

    def go_quiz(self):
        self.clPage.setCurrentIndex(3)

    def go_consult(self):
        self.clPage.setCurrentIndex(4)

    def log_in(self):
        if self.studentName.text():
            self.account = self.studentName.text()
            print(self.account)
            self.clPage.setCurrentIndex(0)

    def log_out(self):
        self.clPage.setCurrentIndex(5)

    def go_main(self):
        self.clPage.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    studentCl = StudentClient()
    studentCl.show()
    app.exec_()
