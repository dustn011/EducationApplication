import json
import socketserver
import pymysql
import threading
import time
from datetime import datetime


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
		self.now_connected_name = []

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
				identifier = self.received_message.pop(0)  # identifier = 식별자 -> 추출
				if not incoming_message:  # 연결이 종료됨
					print('클라이언트에서 빈 메시지가 왔습니다')
					break
				# ---------------------연수---------------------
				# 로그인 요청
				elif identifier == 'plzCheckAccount':
					account_info = self.method_checkAccount()
					self.loginAccess_message(client_socket, account_info)
				# 클라이언트 종료
				elif identifier == 'plzDisconnectSocket':
					self.disconnect_socket(client_socket)
				# 로그아웃 요청
				elif identifier == 'plzLogoutAccount':
					self.logoutAccount(client_socket)
				# 질문 입력 요청
				elif identifier == 'plzInsertQuestion':
					self.insertQuestion()
				# 질문 내역 불러오기 요청
				elif identifier == 'plzGiveQuestionLog':
					self.method_getQuestionLog(client_socket)
				# 학생 상담 채팅 들어오면 DB에 저장하는 요청
				elif identifier == 'plzInsertStudentChat':
					# [self.studentName.text(), self.send_chat.text()]
					self.method_insStudentMessage(client_socket)
				# 상담 로그 요청 들어오면 DB에서 꺼내서 보내주기
				elif identifier == 'plzGiveChattingLog':
					student_chatting_log = self.method_getChattingLog()
					self.method_sendChattingLog(client_socket, student_chatting_log)
				# ---------------------성경---------------------
				# 문제 출제 DB 저장
				elif identifier == 'teacher_update':
					con = pymysql.connect(host='10.10.21.102', user='lilac', password='0000', db='education_application')
					with con:
						with con.cursor() as cur:
							sql = f"insert into `education_application`.`question`(FIeld, Title, Content, Answer) values \
										   ('{self.received_message[0]}','{self.received_message[1]}','{self.received_message[2]}','{self.received_message[3]}')"
							cur.execute(sql)
							con.commit()

				# QNA 클라이언트로 보내기
				elif identifier == 'teacher_QNA':
					qna_list = self.QNA_DB()
					client_socket.send((json.dumps(qna_list)).encode())

				# QNA 답변 저장 및 QNA 저장된 내역 보내기
				elif identifier == 'teacher_qna_answer':
					con = pymysql.connect(host='10.10.21.102', user='lilac', password='0000',db='education_application')
					with con:
						with con.cursor() as cur:
							sql = f"update `education_application`.`qna` set answer='{self.received_message[0]}',answer_dt={'now()'}, state='{self.received_message[1]}' where number={self.received_message[2]}"
							cur.execute(sql)
							con.commit()
					qna_list = self.QNA_DB()
					client_socket.send((json.dumps(qna_list)).encode())

				# 이전내역 클라이언트로 보내기
				elif identifier == 'teacher_consulting_ch':
					self.pre_chat_send(client_socket)

				# 선생 접속시 리스트에 소켓내용, 이름 집어넣기
				elif identifier == 'teacher_account':
					self.teacher_account(client_socket)

				# 실시간채팅 전송받앗을 때 DB저장및 학생한테 보내기
				elif identifier == 'teacher_send_message':
					# self.received_message = [manager, send_message, student_name]

					self.chat_dbsave()

				# ---------------------민석---------------------
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

	# ---------------------연수---------------------
	# DB에서 상담 채팅 내역 불러오기 해당 학생만
	def method_getChattingLog(self):
		print('클라이언트에서 상담채팅 내역 요청이 들어왔습니다')
		chat = pymysql.connect(host='10.10.21.102', user='edu', password='0000', db='education_application',
							   charset='utf8')
		# DB와 상호작용하기 위해 연결해주는 cursor 객체 만듬
		chattingLog = chat.cursor()
		# 클라이언트가 요청한 상담채팅 내역 불러오기
		sql = f"SELECT * FROM chat WHERE receiver='{self.received_message[0]}' OR sender = '{self.received_message[0]}' ORDER BY send_dt"
		# execute 메서드로 db에 sql 문장 전송
		chattingLog.execute(sql)
		qna_info = chattingLog.fetchall()  # 회원 정보 저장
		# DB 닫아주기
		chat.close()
		return qna_info

	# 불러온 상담내역 보내기
	def method_sendChattingLog(self, sender_socket, student_chatting_log):
		# DB에서 가져온 튜플 리스트화
		for i in range(len(student_chatting_log)):
			student_chat_data = ['send_studentChat_data']
			for j in range(len(student_chatting_log[i])):
				if type(student_chatting_log[i][j]) == datetime:
					student_chat_data.append(student_chatting_log[i][j].strftime('%D %T'))
				else:
					student_chat_data.append(student_chatting_log[i][j])
			send_accessChat = json.dumps(student_chat_data)
			sender_socket.send(send_accessChat.encode('utf-8'))  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌
			time.sleep(0.00000000000001)

	# DB에 학생 상담 채팅 저장하기
	def method_insStudentMessage(self, sender_socket):
		student_name = self.received_message[0]
		student_chat = self.received_message[1]
		# DB 열기
		ins_ch = pymysql.connect(host='10.10.21.102', user='lilac', password='0000', db='education_application',
								 charset='utf8')
		# DB와 상호작용하기 위해 연결해주는 cursor 객체 만듬
		insert_chat = ins_ch.cursor()

		# insert문 넣어주기(언제 누가 메시지를 누구에게 보냇습니다)
		insert_sql = f"insert into chat VALUES(now(), '{student_name}', '{student_chat}', 'manager')"

		# execute 메서드로 db에 sql 문장 전송
		insert_chat.execute(insert_sql)
		# insert문 실행
		ins_ch.commit()
		# DB 닫아주기
		ins_ch.close()
		print('질문이 등록됐습니다')

	# DB에서 질문 내역 가져오기
	def method_getQuestionLog(self, sender_socket):
		print('질문내역 요청 메시지가 왔습니다')
		qna = pymysql.connect(host='10.10.21.102', user='edu', password='0000', db='education_application',
							  charset='utf8')
		# DB와 상호작용하기 위해 연결해주는 cursor 객체 만듬
		all_qna = qna.cursor()
		# 클라이언트가 입력한 계정 정보가 일치하는지 확인
		sql = f"SELECT * FROM qna"
		# execute 메서드로 db에 sql 문장 전송
		all_qna.execute(sql)
		qna_info = all_qna.fetchall()  # 회원 정보 저장
		# DB 닫아주기
		qna.close()

		# DB에서 가져온 튜플 리스트화
		for i in range(len(qna_info)):
			all_qna_data = ['send_qna_data']
			for j in range(len(qna_info[i])):
				if type(qna_info[i][j]) == datetime:
					all_qna_data.append(qna_info[i][j].strftime('%D %T'))
				else:
					all_qna_data.append(qna_info[i][j])
			send_accessQna = json.dumps(all_qna_data)
			sender_socket.send(send_accessQna.encode('utf-8'))  # 연결된 소켓(서버)에 채팅 로그 데이터 보내줌
			time.sleep(0.0000000000001)

	# DB에 질문 등록하기
	def insertQuestion(self):
		student_name = self.received_message[0]
		question_title = self.received_message[1]
		question_content = self.received_message[2]

		# DB 열기
		ins_qu = pymysql.connect(host='10.10.21.102', user='lilac', password='0000', db='education_application',
								 charset='utf8')
		# DB와 상호작용하기 위해 연결해주는 cursor 객체 만듬
		insert_question = ins_qu.cursor()

		# insert문 넣어주기(누가 (제목과내용으로구성된)질문을 언제 했습니다)
		insert_sql = f"call insertQna('{student_name}', '{question_title}', '{question_content}')"

		# execute 메서드로 db에 sql 문장 전송
		insert_question.execute(insert_sql)
		# insert문 실행
		ins_qu.commit()
		# DB 닫아주기
		ins_qu.close()
		print('질문이 등록됐습니다')

	# 모든 클라이언트로 갱신된 질문 리스트 보내주기
	def sendallQnA(self):
		pass

	# 접속중인 account 리스트에서 빼주기
	def logoutAccount(self, sender_socket):
		self.now_connected_account.remove([sender_socket, self.received_message[0]])
		self.now_connected_name.remove(self.received_message[0])
		print('현재 접속한 account:', self.now_connected_account)

	# DB에서 account정보와 일치하는지 확인
	def method_checkAccount(self):
		print('회원 정보 확인 메시지가 왔습니다')
		account = pymysql.connect(host='10.10.21.102', user='edu', password='0000', db='education_application',
								  charset='utf8')
		# DB와 상호작용하기 위해 연결해주는 cursor 객체 만듬
		all_account = account.cursor()
		# 클라이언트가 입력한 계정 정보가 일치하는지 확인
		sql = f"SELECT * FROM account WHERE name = '{self.received_message[0]}'"
		# execute 메서드로 db에 sql 문장 전송
		all_account.execute(sql)
		account_info = all_account.fetchall()  # 회원 정보 저장
		# DB 닫아주기
		account.close()
		return account_info

	def loginAccess_message(self, sender_socket, account_info):
		# print(account_info[0][0])
		if account_info and (account_info[0][0] not in self.now_connected_name):  # 회원정보를 옳게 입력했다면
			access_message = ['success_login']
			self.now_connected_account.append([sender_socket, account_info[0][0]])
			self.now_connected_name.append(account_info[0][0])
			print('로그인 성공')
			print('현재 접속한 account:', self.now_connected_account)
		else:  # 회원정보를 옳게 입력하지 않았다면
			access_message = ['failed_login']
			print('로그인 실패')
		send_accessMessage = json.dumps(access_message)
		sender_socket.send(send_accessMessage.encode('utf-8'))  # 연결된 소켓(서버)에 로그인 확인 메시지 보내줌

	# 클라이언트에서 연결 끊는다고 시그널 보내면 소켓 리스트에서 해당 클라이언트 연결 소켓 지움
	def disconnect_socket(self, senders_socket):
		for client in self.clients:
			socket, (ip, port) = client
			if socket is senders_socket:
				self.clients.remove(client)  # 전체 클라이언트 소켓 리스트에서 해당 소켓 제거
				print(f"{datetime.now().strftime('%D %T')}, {ip} : {port} 연결이 종료되었습니다")
				socket.close()
				print(self.clients)

	# ---------------------성경---------------------

	# QNA DB 내역 불러오기
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

	# 채팅이전내역 보내기
	def pre_chat_send(self, sender_socket):
		con = pymysql.connect(host='10.10.21.102', user='lilac', password='0000', db='education_application')
		with con:
			with con.cursor() as cur:
				sql = f"select * from `education_application`.`chat` where receiver='{self.received_message[0]}' or sender='{self.received_message[0]}' order by send_dt"
				cur.execute(sql)
				temp = cur.fetchall()
		print(temp)
		consulting = []
		for i in range(len(temp)):
			temp1 = []
			for j in range(len(temp[0])):
				if type(temp[i][j]) == datetime:
					temp1.append(temp[i][j].strftime('%D,%T'))
				else:
					temp1.append(temp[i][j])
			consulting.append(temp1)
		print(consulting)
		consulting_chat = ['teacher_consulting_ch', consulting]
		sender_socket.send((json.dumps(consulting_chat)).encode())

	# 선생클라이언트로 입장눌렀을 때 리스트에 집어넣기 QNA 리스트, 학생접속명단 보내기
	def teacher_account(self, sender_socket):
		self.now_connected_account.append([sender_socket, 'manager'])
		self.now_connected_name.append('manager')
		print('로그인 성공')
		print('현재 접속한 account:', self.now_connected_account)
		print('현재 접속 명단:', self.now_connected_name)

		# QNA리스트 보내기
		qna_list = self.QNA_DB()
		sender_socket.send((json.dumps(qna_list)).encode())

		# 학생접속명단 보내기
		name=[]
		for i in self.now_connected_name:
			if i =='manager':
				pass
			else:
				name.append(i)
		student = ['teacher_consulting_st', name]
		sender_socket.send((json.dumps(student)).encode())

	# 실시간 상담내역 저장
	def chat_dbsave(self):
		con = pymysql.connect(host='10.10.21.102', user='lilac', password='0000',
							  db='education_application')
		with con:
			with con.cursor() as cur:
				sql = f"insert into `education_application`.`chat`(send_dt, sender, chat_content, receiver) values ({'now()'},'{self.received_message[0]}','{self.received_message[1]}','{self.received_message[2]}')"
				cur.execute(sql)
				con.commit()

	# ---------------------민석---------------------
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
	host, port = '10.10.21.124', 9015
	'''
		# 아래 코드와 비슷하게 돌아감. with를 사용해서 만들어보고 싶었음
		server = ThreadedTCPServer((host, port), TCPHandler)
		server.serve_forever()
	'''
	# socketserver을 이용해서 TCP 서버 소켓 객체 생성
	with ThreadedTCPServer((host, port), TCPHandler) as server:
		server.serve_forever()  # 서버를 실행하고 서비스를 무한 반복한다
