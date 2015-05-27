import github3
import re
import bitcoinaddress as btcAdr
import sqlite3
import string
import time

def getAllUsersAddresses():
	token='yourTokenHere'
	gh= github3.login(token=token)
	users= gh.all_users()
	userCount=0
	conn = sqlite3.connect( 'btcGitDB.db')
	cursor = conn.cursor()
	cursor.execute("CREATE TABLE IF NOT EXISTS usernames(username TEXT, btcAddress TEXT)")
	cursor.execute("CREATE TABLE IF NOT EXISTS checkedUsers(username TEXT)")

	def addressInText(text):
		#gets rid of candidates that are too small and cleans for punctuation
		regex = re.compile('[%s]' % re.escape(string.punctuation))
		possibleKeys= [regex.sub('', x) for x in text.split() if len(x)>23]
		keys=[]
		for x in possibleKeys:
			if btcAdr.validate(x)== True:
				keys.append(x)
		if len(keys)>0:
			return ', '.join(keys)
		else:
			return False
			
	tries=0
	while tries <= 100 :
		try:
			for user in users:
				userCount += 1
				#user.refresh()
				username= str(user)
				cursor.execute("SELECT count(*) FROM checkedUsers WHERE username = ?", (username,))
				data=cursor.fetchone()[0]
				
				if data==0:
					cursor.execute("INSERT INTO checkedUsers(username) VALUES (?)",(username,))
					conn.commit
					userRepos= gh.repositories_by(username)
					print "on user: " + str(userCount)
					repoCount=0
					for repo in userRepos:
						repoCount+=1
						print "repo # : " + str(repoCount)
						sqlQuery= "INSERT INTO usernames(username, btcAddress) VALUES (?,?)"
						try:
						   readMe= repo.readme()
						   knownAddr= addressInText(readMe.decoded)
						   
						except Exception as e:
						   # Rollback in case there is any error
						   tries +=1
						   print 'on try: ' + str(tries)
						   print 'exception: ' +str(e)
						   if 'limit' in str(e):
						   		print 'sleeping for 10 minutes'
						   		time.sleep(600)
						if knownAddr:
							cursor.execute(sqlQuery,(username, knownAddr))
						   # Commit your changes in the database
							print '\n added to db \n'
							conn.commit()
							
		except Exception as e:
		   # Rollback in case there is any error
		   tries +=1
		   print 'on try: ' + str(tries)
		   print 'exception: ' +str(e)
		   if 'limit' in str(e):
		   		print 'sleeping for 10 minutes'
		   		time.sleep(600)


	print 'data collection over' 
getAllUsersAddresses()
			
