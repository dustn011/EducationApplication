import json
import requests
import xmltodict
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QRegExp
from PyQt5 import uic
import sys
from socket import *
from datetime import datetime
from threading import *
import urllib.request
import time

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
        # 학습 할 내용?
        self.extinctions = dict()
        self.insects = dict()
        self.mammalias = dict()
        self.birds = dict()
        self.study_index = ''
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
        self.goMain_5.clicked.connect(self.go_main)
        # 퀴즈 목록 가져오기
        self.showQuestions.clicked.connect(self.show_quiz)
        self.showQuestions2.clicked.connect(self.show_quiz)
        self.showQuestions3.clicked.connect(self.show_quiz)
        self.classTab.currentChanged.connect(self.show_quiz)
        # 퀴즈 선택하기
        self.questionList.cellClicked.connect(self.cell_click)
        self.questionList2.cellClicked.connect(self.cell_click)
        self.questionList3.cellClicked.connect(self.cell_click)
        # 답 제출
        self.sendAnswer.clicked.connect(self.answer)
        self.answerText.returnPressed.connect(self.answer)
        self.sendAnswer2.clicked.connect(self.answer)
        self.answerText2.returnPressed.connect(self.answer)
        self.sendAnswer3.clicked.connect(self.answer)
        self.answerText3.returnPressed.connect(self.answer)
        # 탭을 변경하면 api를 연결
        self.studyTab.currentChanged.connect(self.study_change)
        # 멸종 위기 곤충
        self.extincList.itemSelectionChanged.connect(self.extinc_info)
        # 곤충 도감
        self.insectList.itemSelectionChanged.connect(self.insect_info)
        # 포유류 도감
        self.mammaliaList.itemSelectionChanged.connect(self.mammalia_info)
        # 조류 도감
        self.birdList.itemSelectionChanged.connect(self.bird_info)
        # 학습 진도 저장
        self.saveStudy.clicked.connect(self.save_study)
        self.saveStudy_2.clicked.connect(self.save_study)
        self.saveStudy_3.clicked.connect(self.save_study)
        self.saveStudy_4.clicked.connect(self.save_study)

        # 연수's
        # 로그인 칸에는 한글만 입력 가능
        reg_exp = QRegExp("[가-힣]+")
        validator = QRegExpValidator(reg_exp, self.studentName)
        self.studentName.setValidator(validator)

        # QnA 질문 입력 버튼
        self.writingComplete.clicked.connect(self.send_question)

        # 테이블 위젯 너비에 맞추기
        self.question_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.question_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.question_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.question_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.question_table.horizontalHeader().resizeSection(0, 30)
        self.question_table.horizontalHeader().resizeSection(1, 30)
        self.question_table.horizontalHeader().resizeSection(3, 60)
        # qna 데이터 저장
        self.list_qna_data = []

        # 질문 제목 글자수 제한하기
        self.question_title.setMaxLength(22)

        # 질문 클릭하면 질문, 답변 내역 출력
        self.question_table.cellClicked.connect(self.show_one_qna)

        # 상담 입력하고 엔터
        self.send_chat.returnPressed.connect(self.method_send_chat)
        # 상담 입력하고 버튼 클릭
        self.btn_send_chat.clicked.connect(self.method_send_chat)

    def initialize_socket(self, ip, port):
        # TCP socket을 생성하고 server와 연결
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        remote_ip = ip
        remote_port = port
        self.client_socket.connect((remote_ip, remote_port))

    # 학습 페이지로 이동
    def go_study(self):
        self.clPage.setCurrentIndex(1)

    def study_change(self, index):
        if index == 0:
            self.study_extinction()
        elif index == 1:
            self.study_insect()
        elif index == 2:
            self.study_mammalia()
        elif index == 3:
            self.study_bird()
        self.load_study()

    # 퀴즈 페이지로 이동
    def go_quiz(self):
        self.show_quiz()
        self.clPage.setCurrentIndex(3)

    # 연수's
    # 상담 페이지로 이동
    def go_consult(self):
        # 인덱스 0번에 식별자 'plzGiveChattingLog' 넣어주고 [학생 이름]서버로 전송
        chat = ['plzGiveChattingLog', self.studentName.text()]
        send_chatAccess = json.dumps(chat)
        self.client_socket.send(send_chatAccess.encode('utf-8'))
        print('서버에 상담 채팅 내역을 요청했습니다')
        self.chat_list.clear()
        self.clPage.setCurrentIndex(4)

    # 상담 보내기
    def method_send_chat(self):
        if not self.send_chat.text():
            QMessageBox.information(self, '입력오류', '내용을 입력해주세요')
        else:
            # 인덱스 0번에 식별자 'plzInsertStudentChat' 넣어주고 [학생 이름, 상담 내용]서버로 전송
            chat = ['plzInsertStudentChat', self.studentName.text(), self.send_chat.text()]
            send_chat = json.dumps(chat)
            self.client_socket.send(send_chat.encode('utf-8'))
            print('서버에 상담 채팅 내역을 보냈습니다')

    # 질문 선택하면 질문 내역, 응답 내역 출력
    def show_one_qna(self):
        self.show_question_title.clear()
        self.show_question_content.clear()
        self.question_dt.clear()
        self.show_answer.clear()
        self.answer_dt.clear()

        sele_qna_num = int(self.question_table.selectedItems()[0].text())
        for i in range(len(self.list_qna_data)):
            if sele_qna_num == self.list_qna_data[i][0]:
                self.show_question_title.setText(self.list_qna_data[i][2])
                self.show_question_content.setText(self.list_qna_data[i][3])
                self.question_dt.setText(self.list_qna_data[i][4])
                self.show_answer.setText(self.list_qna_data[i][5])
                self.answer_dt.setText(self.list_qna_data[i][6])

    # 질문입력 버튼 누르면 실행할 메서드
    def send_question(self):
        if not self.question_title.text():
            QMessageBox.information(self, '입력오류', '제목을 입력해주세요')
        elif not bool(self.question_content.toPlainText()):
            QMessageBox.information(self, '입력오류', '질문을 입력해주세요')
        else:
            # 인덱스 0번에 식별자 'plzInsertQuestion' 넣어주고 [질문자 이름, 제목, 질문 내용]서버로 전송
            question = ['plzInsertQuestion', self.studentName.text(), self.question_title.text(),
                        self.question_content.toPlainText()]
            send_question = json.dumps(question)
            self.client_socket.send(send_question.encode('utf-8'))
            print('서버에 질문등록 요청을 보냈습니다')
            self.question_title.clear()
            self.question_content.clear()
            QMessageBox.information(self, '등록 완료', '질문을 등록하셨습니다')

    # 연수's
    # QnA 페이지로 이동
    def go_qna(self):
        # 인덱스 0번에 식별자 'plzGiveQuestionLog' 넣어주고 서버로 요청 전송
        questionLog = ['plzGiveQuestionLog']
        send_AccessQuestionLog = json.dumps(questionLog)
        self.client_socket.send(send_AccessQuestionLog.encode('utf-8'))
        print('서버에 질문내역 요청을 보냈습니다')
        self.clPage.setCurrentIndex(2)

        self.list_qna_data = []

        # 테이블 위젯 헤더를 제외하고 한 번 초기화
        self.question_table.clearContents()

    # 로그인
    def log_in(self):
        if not bool(self.studentName.text()):
            QMessageBox.information(self, '입력 오류', '이름을 입력해주세요')
        else:
            # 인덱스 0번에 식별자 'plzCheckAccount' 넣어주고 서버로 전송
            checkAccountSignal = ['plzCheckAccount', self.studentName.text()]
            send_accountSignal = json.dumps(checkAccountSignal)
            self.client_socket.send(send_accountSignal.encode('utf-8'))
            print('서버에 로그인 요청을 보냈습니다')
            self.account = self.studentName.text()
            self.study_change(0)

    # 로그아웃
    def log_out(self):
        # 인덱스 0번에 식별자 'plzCheckAccount' 넣어주고 서버로 전송
        logoutSignal = ['plzLogoutAccount', self.studentName.text()]
        send_logoutSignal = json.dumps(logoutSignal)
        self.client_socket.send(send_logoutSignal.encode('utf-8'))
        print('서버에 로그아웃 요청을 보냈습니다')

        self.studentName.clear()
        self.fail_message.clear()
        self.clPage.setCurrentIndex(5)

    # 메인 페이지로 이동
    def go_main(self):
        self.clPage.setCurrentIndex(0)

    # 퀴즈 목록 받아오기
    def show_quiz(self):
        self.questionList.setRowCount(0)
        # 현재 탭의 정보 저장
        now_tab = self.classTab.tabText(self.classTab.currentIndex())
        # 요청 코드와 탭 이름, 학생 이름 전달
        show_quiz = json.dumps(["plzGiveQuiz", now_tab, self.account])
        self.client_socket.send(show_quiz.encode('utf-8'))

    # 테이블에서 셀 클릭했을 때 퀴즈 내용 출력하기
    def cell_click(self, row):
        self.row = row
        if self.classTab.tabText(self.classTab.currentIndex()) == "곤충":
            self.quizText.clear()
            self.answerText.clear()
            self.exact.clear()
            self.quizText.append(self.questions[row][2] + "\n")
            self.quizText.append(self.questions[row][3])
        elif self.classTab.tabText(self.classTab.currentIndex()) == "포유류":
            self.quizText2.clear()
            self.answerText2.clear()
            self.exact2.clear()
            self.quizText2.append(self.questions[row][2] + "\n")
            self.quizText2.append(self.questions[row][3])
        elif self.classTab.tabText(self.classTab.currentIndex()) == "조류":
            self.quizText3.clear()
            self.answerText3.clear()
            self.exact3.clear()
            self.quizText3.append(self.questions[row][2] + "\n")
            self.quizText3.append(self.questions[row][3])

    # 정답 제출
    def answer(self):
        # 현재 탭 저장
        now_tab = self.classTab.tabText(self.classTab.currentIndex())
        # 풀지 않은 문제였을 때
        if now_tab == "곤충":
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
        elif now_tab == "포유류":
            if self.questionList2.item(self.row, 1).text() == "-":
                # 정답을 출력
                self.correct2.setText("정답 : " + self.questions[self.row][4])
                # 답이 맞으면
                if self.answerText2.text() == self.questions[self.row][4]:
                    # 현재 점수에 점수를 추가 (문제 당 10점)
                    self.score2.setText(str(int(self.score2.text()) + 10))
                    self.exact2.setText("정답!")
                    # 테이블에 바로 결과 반영
                    self.questionList2.setItem(self.row, 1, QTableWidgetItem("정답"))
                    # 서버에 데이터 수정을 요청
                    self.client_socket.send(json.dumps(["hereAnswer",
                                                        now_tab, self.account, self.row + 1, '정답',
                                                        self.score2.text()]).encode('utf-8'))
                # 답이 틀리면
                else:
                    self.exact2.setText("땡!!")
                    # 테이블에 바로 결과 반영
                    self.questionList2.setItem(self.row, 1, QTableWidgetItem("오답"))
                    # 서버에 데이터 수정을 요청
                    self.client_socket.send(json.dumps(["hereAnswer",
                                                        now_tab, self.account, self.row + 1, '오답',
                                                        self.score2.text()]).encode('utf-8'))
                # 입력했던 답 지우기
                self.answerText2.clear()
        elif now_tab == "조류":
            if self.questionList3.item(self.row, 1).text() == "-":
                # 정답을 출력
                self.correct3.setText("정답 : " + self.questions[self.row][4])
                # 답이 맞으면
                if self.answerText3.text() == self.questions[self.row][4]:
                    # 현재 점수에 점수를 추가 (문제 당 10점)
                    self.score3.setText(str(int(self.score3.text()) + 10))
                    self.exact3.setText("정답!")
                    # 테이블에 바로 결과 반영
                    self.questionList3.setItem(self.row, 1, QTableWidgetItem("정답"))
                    # 서버에 데이터 수정을 요청
                    self.client_socket.send(json.dumps(["hereAnswer",
                                                        now_tab, self.account, self.row + 1, '정답',
                                                        self.score3.text()]).encode('utf-8'))
                # 답이 틀리면
                else:
                    self.exact3.setText("땡!!")
                    # 테이블에 바로 결과 반영
                    self.questionList3.setItem(self.row, 1, QTableWidgetItem("오답"))
                    # 서버에 데이터 수정을 요청
                    self.client_socket.send(json.dumps(["hereAnswer",
                                                        now_tab, self.account, self.row + 1, '오답',
                                                        self.score3.text()]).encode('utf-8'))
                # 입력했던 답 지우기
                self.answerText3.clear()

    # 학습 진도 가져오기
    def load_study(self):
        print("불러오기")
        print(self.account, self.studyTab.currentIndex())
        self.client_socket.send(json.dumps(["giveStudy", self.account, self.studyTab.currentIndex()]).encode('utf-8'))

    # 받아온 학습 진도까지 교재 출력
    def study_list(self):
        self.extincList.clear()
        self.insectList.clear()
        self.mammaliaList.clear()
        self.birdList.clear()
        for i in range(int(self.study_index) + 1):
            if self.studyTab.currentIndex() == 0:
                self.extincList.addItem(self.extinctions[str(i)][1])
            elif self.studyTab.currentIndex() == 1:
                self.insectList.addItem(self.insects[str(i)][1])
            elif self.studyTab.currentIndex() == 2:
                self.mammaliaList.addItem(self.mammalias[str(i)][1])
            elif self.studyTab.currentIndex() == 3:
                self.birdList.addItem(self.birds[str(i)][1])

    # 멸종 위기 곤충 정리
    def study_extinction(self):
        self.extincList.clear()
        extinc_cont = []
        key = "jAB8gOQ%2BEjRxryPTRcGIWjS6sTl2FCowle%2Bb%2FVaRrcoCuQZTgCIEID85tLqWiPIfuY4%2FzUsqf81dQj6dYuTyYg%3D%3D"
        url = 'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctPrtctList?serviceKey=%s' % key
        content = requests.get(url).content
        diction = xmltodict.parse(content)
        index = 0
        for item in diction['response']['body']['items']['item']:
            url = 'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctIlstrInfo?serviceKey=' \
                  '%s&q1=%s' % (key, item['insctPilbkNo'])
            content = requests.get(url).content
            extinc = xmltodict.parse(content)['response']['body']['item']
            extinc_cont.append(extinc['imgUrl'])
            extinc_cont.append(extinc['insctOfnmKrlngNm'])
            extinc_cont.append(extinc['ordKorNm'])
            extinc_cont.append(extinc['familyKorNm'])
            extinc_cont.append(extinc['genusKorNm'])
            for i in range(0, 9):
                if isinstance(extinc['cont%d' % (i + 1)], str):
                    extinc_cont.append(extinc['cont%d' % (i + 1)])
            self.extinctions[str(index)] = extinc_cont
            extinc_cont = []
            index += 1

    # 선택한 멸종 위기 곤충의 정보 출력
    def extinc_info(self):
        self.extincInfo.clear()
        url = self.extinctions[str(self.extincList.currentRow())][0]
        insect = urllib.request.urlopen(url).read()
        pixmap = QPixmap()
        pixmap.loadFromData(insect)
        if pixmap.size().width() > pixmap.size().height():
            pixmap = pixmap.scaledToWidth(400)
        else:
            pixmap = pixmap.scaledToHeight(400)
        self.extincImage.setPixmap(pixmap)
        for i in range(1, len(self.extinctions[str(self.extincList.currentRow())])):
            self.extincInfo.append(self.extinctions[str(self.extincList.currentRow())][i] + "\n")

    # 곤충 도감 10마리 정리
    def study_insect(self):
        self.insectList.clear()
        insect_cont = []
        key = "XHef%2BpLCxnzMTQsT2fS%2BVkJ9blytTOQ28QVlhrTlfvBkNZaPyFGO6JYanPWEwzvo1%2B2I%2FIBuK1Bmm5FLk5Q0kw%3D%3D"
        url = 'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctIlstrSearch?serviceKey=' \
              '%s&st=1&sw=&numOfRows=10&pageNo=1' % key
        content = requests.get(url).content
        insects_list = xmltodict.parse(content)['response']['body']['items']['item']
        index = 0
        for insect in insects_list:
            url = 'http://openapi.nature.go.kr/openapi/service/rest/InsectService/isctIlstrInfo?serviceKey=' \
                  '%s&q1=%s' % (key, insect['insctPilbkNo'])
            content = requests.get(url).content
            insect_info = xmltodict.parse(content)['response']['body']['item']
            if insect_info['imgUrl'] != 'NONE':
                insect_cont.append(insect_info['imgUrl'])
            else:
                insect_cont.append('이미지 없음')
            insect_cont.append(insect_info['insctOfnmKrlngNm'])
            insect_cont.append(insect_info['ordKorNm'])
            insect_cont.append(insect_info['familyKorNm'])
            if isinstance(insect_info['genusKorNm'], str):
                insect_cont.append(insect_info['genusKorNm'])
            for i in range(0, 9):
                if isinstance(insect_info['cont%d' % (i + 1)], str):
                    insect_cont.append(insect_info['cont%d' % (i + 1)])
            self.insects[str(index)] = insect_cont
            insect_cont = []
            index += 1

    # 선택한 곤충 정보 출력
    def insect_info(self):
        self.insectInfo.clear()
        if self.insects[str(self.insectList.currentRow())][0] != '이미지 없음':
            url = self.insects[str(self.insectList.currentRow())][0]
            insect = urllib.request.urlopen(url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(insect)
            if pixmap.size().width() > pixmap.size().height():
                pixmap = pixmap.scaledToWidth(400)
            else:
                pixmap = pixmap.scaledToHeight(400)
            self.insectImage.setPixmap(pixmap)
        else:
            self.insectImage.setText("이미지 없음")
        for i in range(1, len(self.insects[str(self.insectList.currentRow())])):
            self.insectInfo.append(self.insects[str(self.insectList.currentRow())][i] + "\n")

    # 포유류 도감 10마리 정리
    def study_mammalia(self):
        self.mammaliaList.clear()
        mammalia_cont = []
        key = "XHef%2BpLCxnzMTQsT2fS%2BVkJ9blytTOQ28QVlhrTlfvBkNZaPyFGO6JYanPWEwzvo1%2B2I%2FIBuK1Bmm5FLk5Q0kw%3D%3D"
        url = 'http://apis.data.go.kr/1400119/MammService/mammIlstrSearch?serviceKey=%s&st=1&sw=&numOfRows=10&pageNo=1' \
              % key
        content = requests.get(url).content
        mammalias_list = xmltodict.parse(content)['response']['body']['items']['item']
        index = 0
        for mammalia in mammalias_list:
            url = 'http://apis.data.go.kr/1400119/MammService/mammIlstrInfo?serviceKey=%s&q1=%s' \
                  % (key, mammalia['anmlSpecsId'])
            content = requests.get(url).content
            mammalia_info = xmltodict.parse(content)['response']['body']['item']
            if mammalia_info['imgUrl'] != 'NONE':
                mammalia_cont.append(mammalia_info['imgUrl'])
            else:
                mammalia_cont.append('이미지 없음')
            mammalia_cont.append(mammalia_info['anmlGnrlNm'])
            mammalia_cont.append(mammalia_info['anmlPhlmKorNm'])
            mammalia_cont.append(mammalia_info['anmlClsKorNm'])
            mammalia_cont.append(mammalia_info['anmlOrdKorNm'])
            mammalia_cont.append(mammalia_info['anmlFmlyKorNm'])
            mammalia_cont.append(mammalia_info['eclgDpftrCont'])
            mammalia_cont.append(mammalia_info['gnrlSpftrCont'])
            self.mammalias[str(index)] = mammalia_cont
            mammalia_cont = []
            index += 1
        print(self.mammalias)

    # 선택한 포유류 정보 출력
    def mammalia_info(self):
        self.mammaliaInfo.clear()
        if self.mammalias[str(self.mammaliaList.currentRow())][0] != '이미지 없음':
            url = self.mammalias[str(self.mammaliaList.currentRow())][0]
            mammalia = urllib.request.urlopen(url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(mammalia)
            if pixmap.size().width() > pixmap.size().height():
                pixmap = pixmap.scaledToWidth(400)
            else:
                pixmap = pixmap.scaledToHeight(400)
            self.mammaliaImage.setPixmap(pixmap)
        else:
            self.mammaliaImage.setText("이미지 없음")
        for i in range(1, len(self.mammalias[str(self.mammaliaList.currentRow())])):
            self.mammaliaInfo.append(self.mammalias[str(self.mammaliaList.currentRow())][i] + "\n")

    # 조류 도감 10마리 정리
    def study_bird(self):
        self.birdList.clear()
        bird_cont = []
        key = "XHef%2BpLCxnzMTQsT2fS%2BVkJ9blytTOQ28QVlhrTlfvBkNZaPyFGO6JYanPWEwzvo1%2B2I%2FIBuK1Bmm5FLk5Q0kw%3D%3D"
        url = 'http://apis.data.go.kr/1400119/BirdService/birdIlstrSearch?serviceKey=%s&st=1&sw=&numOfRows=10&pageNo=1' \
              % key
        content = requests.get(url).content
        birds_list = xmltodict.parse(content)['response']['body']['items']['item']
        index = 0
        for bird in birds_list:
            url = 'http://apis.data.go.kr/1400119/BirdService/birdIlstrInfo?serviceKey=%s&q1=%s' \
                  % (key, bird['anmlSpecsId'])
            content = requests.get(url).content
            bird_info = xmltodict.parse(content)['response']['body']['item']
            if bird_info['imgUrl'] != 'NONE':
                bird_cont.append(bird_info['imgUrl'])
            else:
                bird_cont.append('이미지 없음')
            bird_cont.append(bird_info['anmlGnrlNm'])
            bird_cont.append(bird_info['anmlPhlmKorNm'])
            bird_cont.append(bird_info['anmlClsKorNm'])
            bird_cont.append(bird_info['anmlOrdKorNm'])
            bird_cont.append(bird_info['anmlFmlyKorNm'])
            bird_cont.append(bird_info['eclgDpftrCont'])
            bird_cont.append(bird_info['gnrlSpftrCont'])
            self.birds[str(index)] = bird_cont
            bird_cont = []
            index += 1

    # 선택한 조류 정보 출력
    def bird_info(self):
        self.birdInfo.clear()
        if self.birds[str(self.birdList.currentRow())][0] != '이미지 없음':
            url = self.birds[str(self.birdList.currentRow())][0]
            bird = urllib.request.urlopen(url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(bird)
            if pixmap.size().width() > pixmap.size().height():
                pixmap = pixmap.scaledToWidth(400)
            else:
                pixmap = pixmap.scaledToHeight(400)
            self.birdImage.setPixmap(pixmap)
        else:
            self.birdImage.setText("이미지 없음")
        for i in range(1, len(self.birds[str(self.birdList.currentRow())])):
            self.birdInfo.append(self.birds[str(self.birdList.currentRow())][i] + "\n")

    def save_study(self):
        print("진도 저장")
        self.client_socket.send(json.dumps
                                (["saveStudy", self.account, self.studyTab.currentIndex(),
                                  str(self.study_index)]).encode('utf-8'))

    # 서버에서 데이터 받는 스레드
    def listen_thread(self):
        # 데이터 수신 Tread를 생성하고 시작한다
        t = Thread(target=self.receive_message, args=(self.client_socket,))
        t.start()

    # 서버에서 받은 데이터를 처리하는 함수
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
                    if self.classTab.tabText(self.classTab.currentIndex()) == "곤충":
                        self.questionList.setRowCount(len(self.questions))
                        for row in range(len(self.questions)):
                            self.questionList.setItem(row, 0, QTableWidgetItem("%s" % self.questions[row][2]))
                    elif self.classTab.tabText(self.classTab.currentIndex()) == "포유류":
                        self.questionList2.setRowCount(len(self.questions))
                        for row in range(len(self.questions)):
                            self.questionList2.setItem(row, 0, QTableWidgetItem("%s" % self.questions[row][2]))
                    elif self.classTab.tabText(self.classTab.currentIndex()) == "조류":
                        self.questionList3.setRowCount(len(self.questions))
                        for row in range(len(self.questions)):
                            self.questionList3.setItem(row, 0, QTableWidgetItem("%s" % self.questions[row][2]))
                # hereRate = 학생의 퀴즈 진도 코드
                elif identifier == "hereRate":
                    self.rate = message_log[0][0]
                    if self.classTab.tabText(self.classTab.currentIndex()) == "곤충":
                        self.correct.clear()
                        self.exact.clear()
                        self.score.setText(str(self.rate[1]))
                        for row in range(len(self.rate) - 2):
                            self.questionList.setItem(row, 1, QTableWidgetItem("%s" % self.rate[row + 2]))
                        self.questionList.resizeColumnsToContents()
                    elif self.classTab.tabText(self.classTab.currentIndex()) == "포유류":
                        self.correct2.clear()
                        self.exact2.clear()
                        self.score2.setText(str(self.rate[1]))
                        for row in range(len(self.rate) - 2):
                            self.questionList2.setItem(row, 1, QTableWidgetItem("%s" % self.rate[row + 2]))
                        self.questionList2.resizeColumnsToContents()
                    elif self.classTab.tabText(self.classTab.currentIndex()) == "조류":
                        self.correct3.clear()
                        self.exact3.clear()
                        self.score3.setText(str(self.rate[1]))
                        for row in range(len(self.rate) - 2):
                            self.questionList3.setItem(row, 1, QTableWidgetItem("%s" % self.rate[row + 2]))
                        self.questionList3.resizeColumnsToContents()
                elif identifier == 'success_login':
                    self.clPage.setCurrentIndex(0)
                elif identifier == 'failed_login':
                    self.fail_message.setText('로그인 실패')
                elif identifier == 'send_qna_data':
                    self.show_all_qna(message_log)
                elif identifier == 'send_studentChat_data':
                    self.show_chattingLog(message_log)
                elif identifier == 'send_teacher_message':
                    self.show_teacherMessage(message_log)
                elif identifier == 'hereStudyLoad':
                    self.study_index = message_log[0]
                    self.study_list()
                elif identifier == 'not_access_counseling':
                    self.cant_Counseling.setText('지금은 상담 시간이 아닙니다')
                elif identifier == 'access_counseling':
                    one_chat = f"[{datetime.now().strftime('%D %T')}]\n[{self.studentName.text()}] : {self.send_chat.text()}"
                    self.chat_list.addItem(one_chat)
                    self.send_chat.clear()
                    self.chat_list.scrollToBottom()
                    self.cant_Counseling.clear()

    # 선생이 메시지 보내면 메시지 창에 띄우기
    def show_teacherMessage(self, teacher_message):
        print(teacher_message)
        one_chat = f"[{datetime.now().strftime('%D %T')}]\n[{teacher_message[0]}] : {teacher_message[1]}"
        self.chat_list.addItem(one_chat)
        time.sleep(0.000000000001)
        self.chat_list.scrollToBottom()

    # 서버에서 받아온 chatting 데이터 불러오기
    def show_chattingLog(self, chatting_log):
        one_chat = f"[{chatting_log[0]}]\n[{chatting_log[1]}] : {chatting_log[2]}"
        self.chat_list.addItem(one_chat)
        time.sleep(0.000000000001)
        self.chat_list.scrollToBottom()

    # 서버에서 받아온 qna데이터 불러오기
    def show_all_qna(self, qna_data):
        self.list_qna_data.append(qna_data)

        # 테이블 위젯 헤더를 제외하고 한 번 초기화
        self.question_table.clearContents()

        # 테이블 위젯의 row 개수 정해주기
        self.question_table.setRowCount(len(self.list_qna_data))

        for i in range(len(self.list_qna_data)):
            self.question_table.setItem(i, 0, QTableWidgetItem(str(self.list_qna_data[i][0])))
            self.question_table.setItem(i, 1, QTableWidgetItem(str(self.list_qna_data[i][1])))
            self.question_table.setItem(i, 2, QTableWidgetItem(str(self.list_qna_data[i][2])))
            self.question_table.setItem(i, 3, QTableWidgetItem(str(self.list_qna_data[i][7])))

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
    app.exec_()
