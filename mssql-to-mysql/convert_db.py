#!/usr/bin/python

from __future__ import print_function

import MySQLdb
import pyodbc
import sys
import datetime
import includes.config as config
import includes.functions as functions
import includes.sqlserver_datatypes as data_types
import pprint
from termcolor import colored, cprint

reload(sys);
sys.setdefaultencoding("utf8")

#connection for MSSQL. (Note: you must have FreeTDS installed and configured!)
try:
    ms_conn = pyodbc.connect(config.odbcConString)
    ms_cursor = ms_conn.cursor()
except:
    print("Unexpected error in bagging area in MsSQL")
    sys.exit(1)

#connection for MySQL
try:
    my_conn = MySQLdb.connect(host=config.MYSQL_host,user=config.MYSQL_user, passwd=config.MYSQL_passwd, db=config.MYSQL_db)
    my_cursor = my_conn.cursor()
except:
    print("Unexpected error in bagging area in Mysql")
    sys.exit(1)

my_cursor.execute("SET SESSION sql_mode='ALLOW_INVALID_DATES';");

def main(argv):
    for arg in argv:
        if arg == 'test':
            if(ms_cursor):
                print('Connected to MSSQL')
            if(my_cursor):
                print('Connected to MYSQL')
            sys.exit()

if __name__ == "__main__":
    main(sys.argv[1:])

final_table_list = []
final_new_table_names = {}
if config.list_of_tables:
    for in_tables in config.list_of_tables:
        final_table_list.append(in_tables[0])
        final_new_table_names[in_tables[0]] = in_tables[1]

    ms_tables = "','".join(map(str, final_table_list))
    ms_tables = "WHERE name in ('"+ms_tables+"')"
else:
    ms_tables = "WHERE type in ('U')" #tables are 'U' and views are 'V' 

ms_cursor.execute("SELECT * FROM sysobjects %s;" % ms_tables ) #sysobjects is a table in MSSQL db's containing meta data about the database. (Note: this may vary depending on your MSSQL version!)
ms_tables = ms_cursor.fetchall()
noLength = [173, 165, 34, 58, 61, 35, 241] #list of MSSQL data types that don't require a defined lenght ie. datetime
isDecimal = [60, 106, 108, 122] #list of MSSQL data types that are decimal
isInt = [48, 52, 56, 104, 127] #list of MSSQL data types that are integers

for tbl in ms_tables:
    if config.list_of_tables:
        crtTable = final_new_table_names[tbl[0]]
    else:
        crtTable = tbl[0]
    print('Table: '+crtTable)
    crtTable = tbl[0]
    ms_cursor.execute("SELECT * FROM syscolumns WHERE id = OBJECT_ID('%s')" % crtTable) #syscolumns: see sysobjects above.
    columns = ms_cursor.fetchall()
    attr = ""
    sattr = ""
    for col in columns:
        mysqlColType = data_types.data_types[str(col.xtype)] #retrieve the column type based on the data type id

        #Removing data types from found records
        if col.xtype == 189:
            text = colored('Ignoring Timestamp Column: ' + col.name, 'red')
            print(text);
        elif col.xtype in isDecimal:
            attr += "`"+col.name +"` "+ mysqlColType + "(" + str(col.xprec) + "," + str(col.xscale) + "), "
            sattr += "["+col.name+"], "
        elif col.xtype in noLength:
            attr += "`"+col.name +"` "+ mysqlColType + ", "
            sattr += "["+col.name+"], "
        else:
            length = col.length
            if length < 1:
                length = 255

            attr += "`"+col.name.strip() +"` "+ mysqlColType + "(" + str(length) + "), "
            sattr += "["+col.name+"], "

    attr = attr[:-2]
    sattr = sattr[:-2]

    if crtTable not in config.blacklist_tables:
        # if functions.check_table_exists(my_cursor, crtTable):
            # my_cursor.execute("drop table "+crtTable)

            f = open('out/' + crtTable + '.sql','w')

            f.write('CREATE DATABASE IF NOT EXISTS ' + config.MYSQL_db + ';\n')
            f.write('USE ' + config.MYSQL_db + ';\n')
            f.write("SET SESSION sql_mode='ALLOW_INVALID_DATES';\n")

            sql = "CREATE TABLE " + crtTable + " (" + attr + ") ENGINE = MYISAM;"
            print(sql)
            # my_cursor.execute(sql) #create the new table and all columns
            f.write(sql + '\n')

            text = colored('Created Table: ' + crtTable, 'green')
            print(text);

            ms_cursor.execute("SELECT "+sattr+" FROM "+ crtTable)
            tbl_data = ms_cursor.fetchall()

            total_rows = 0

            for row in tbl_data:
                new_row = list(row)

                for i in functions.common_iterable(new_row):
                    if new_row[i] == None:
                       new_row[i] = 0
                    elif type(new_row[i]) == datetime.datetime:
                        new_row[i] = new_row[i].date().isoformat()+' '+new_row[i].time().isoformat()
                    elif type(new_row[i]) == datetime.date:
                        new_row[i] = new_row[i].date().isoformat()
                    elif type(new_row[i]) == datetime.time:
                        new_row[i] = new_row[i].time().isoformat()
                    elif new_row[i] == False:
                        new_row[i] = 0
                    elif new_row[i] == True:
                        new_row[i] = 1
                    elif type(new_row[i]) == unicode:
                        new_row[i] = str(new_row[i]).encode('utf-8')
                    else:
                        new_row[i] = str(new_row[i])

                my_conn.ping(True)

                if len(new_row)>1:
                    query_string = "INSERT INTO `" + crtTable + "` VALUES %r;" % (tuple(new_row),)
                else:
                    query_string = "INSERT INTO `" + crtTable + "` VALUES (%r);" % new_row[0]

                # print(query_string)
                f.write(query_string + '\n')
                # my_cursor.execute(query_string)
                # my_conn.commit() #mysql commit changes to database
                total_rows = total_rows + 1

            f.close()
            text = colored('Imported All Data For Table: ' + crtTable, 'green')
            print(text)
            text = colored('Total Imported Rows: ' + str(total_rows), 'green')
            print(text)
        # else:
        #     text = colored('Table Exists: ' + crtTable, 'cyan')
        #     print(text);
    else:
        text = colored('Table Blacklisted: ' + crtTable, 'red')
        print(text)
        
my_cursor.close()
my_conn.close() #mysql close connection
ms_conn.close() #mssql close connection
