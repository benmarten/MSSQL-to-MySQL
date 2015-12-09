#!/usr/bin/python

#mssql connections string 
odbcConString = 'DSN=MYSERVER;UID=sa;PWD=Password1!'

#mysql connections info
MYSQL_host="localhost"
MYSQL_user="root"
MYSQL_passwd=""
MYSQL_db="LogicWash"

#tables to retrieve and recreate
list_of_tables = [
		['CreditCardLog', 'CreditCardLog'],
	['CreditCardTransactions', 'CreditCardTransactions'],
	['Customers', 'Customers'],
	['CustomerUnlimitedTransactions', 'CustomerUnlimitedTransactions'],
	['CustomerVisitBackup', 'CustomerVisitBackup'],
	['Payments', 'Payments'],
	['PCCWTrans', 'PCCWTrans'],
	['PrepaidBooks', 'PrepaidBooks'],
	['ShiftJournal', 'ShiftJournal'],
	['Tickets', 'Tickets'],
	['TicketsDetails', 'TicketsDetails'],
	['Vehicles', 'Vehicles'],
]
blacklist_tables = []
