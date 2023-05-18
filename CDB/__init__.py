from common.globals import DEBUG, DB_PATH, SEMESTER, GUILD_ID, SEED

SEMESTER_DB_PATH = DB_PATH / f'{SEMESTER}_test.db' if DEBUG else DB_PATH / f'{SEMESTER}.db'
GUILD_DB_PATH = DB_PATH / f'{GUILD_ID}.db'

from CLogger import CLogger
import sqlite3
import discord
from hashlib import md5
from time import asctime

LOGGER = CLogger(name="CDB")

class CDB():
    STUDENT = 0
    ACADEMIC = 1
    AWAY = 2
    RESEARCHER = 3
    
    STUDENT_NAME = 'Öğrenci'
    ACADEMIC_NAME = 'Görevli'
    AWAY_NAME = 'Mezun'
    RESEARCHER_NAME = ACADEMIC_NAME

    def __init__(self):

        self.init_d_cursor()
        self.init_s_cursor()

    def init_s_cursor(self):
        self.s_conn = sqlite3.connect(SEMESTER_DB_PATH)
        self.s_cursor = self.s_conn.cursor()
        self.s_cursor.execute("PRAGMA foreing_keys = ON")

        tableCodes = {
            "DEPARTMENT":'''(
                        id              TEXT        PRIMARY KEY,
                        name            TEXT        NOT NULL
                        );''',
            "ACADEMIC":'''(
                        id          TEXT        PRIMARY KEY,
                        name        TEXT        NOT NULL,
                        surname     TEXT        NOT NULL,
                        department  TEXT,
                        title       TEXT        NOT NULL,
                        job         TEXT        NOT NULL,
                        tel         TEXT
                        );''',
            "MANAGE":'''(
                        name        TEXT        NOT NULL,
                        surname     TEXT        NOT NULL,
                        department  TEXT,
                        title       TEXT        NOT NULL,
                        job         TEXT        NOT NULL,
                        tel         TEXT
                        );''',
            "STUDENT":'''(
                        id          TEXT        PRIMARY KEY,
                        name        TEXT        NOT NULL,
                        surname     TEXT        NOT NULL,
                        department  TEXT        NOT NULL
                        );''',
            "LECTURE":'''(
                        name            TEXT        NOT NULL,
                        code            TEXT        NOT NULL,
                        branch          TEXT        NOT NULL,
                        quota           INT         NOT NULL,
                        subscriber      INT         NOT NULL,
                        department      TEXT        NOT NULL   REFERENCES  DEPARTMENT(id),
                        hours           TEXT,
                        PRIMARY KEY (code, branch)
                        );''',
            "STUDENT_LECTURE":'''(
                        studentID     TEXT        NOT NULL          REFERENCES  STUDENT(id),
                        lectureCode   TEXT        NOT NULL          REFERENCES LECTURE(code),
                        lectureBranch TEXT        NOT NULL          REFERENCES LECTURE(branch)
                        );''',
            "ACADEMIC_LECTURE":'''(
                        academicID    TEXT        NOT NULL          REFERENCES  ACADEMIC(id),
                        lectureCode   TEXT        NOT NULL          REFERENCES LECTURE(code),
                        lectureBranch TEXT        NOT NULL          REFERENCES LECTURE(branch)
                        );'''
        }

        self.__create_tables(self.s_cursor, tableCodes)
        LOGGER.info(f"Connected to {SEMESTER_DB_PATH}")

    def init_d_cursor(self):
        self.d_conn = sqlite3.connect(GUILD_DB_PATH)
        self.d_cursor = self.d_conn.cursor()
        self.d_cursor.execute("PRAGMA foreing_keys = ON")

        tableCodes = {
            "LECTURE":'''(
                        code            TEXT        PRIMARY KEY,
                        channelID       INT         NOT NULL UNIQUE,
                        roleID          INT         NOT NULL UNIQUE,
                        name            TEXT        NOT NULL
                        );''',
            "MEMBER":'''(
                        id          INTEGER     PRIMARY KEY,
                        nick        TEXT        NOT NULL,
                        userID      TEXT        NOT NULL    UNIQUE,
                        hash        TEXT        UNIQUE,
                        time        DATETIME    NOT NULL,
                        type        int         NOT NULL --öğrenci, görevli/araş gör., mezun,
                        );''',
            "SUBLIST":'''(
                        memberID    INTEGER     NOT NULL,
                        lectureCode TEXT        NOT NULL
                        );''',
            "BANNED":'''(
                        userID      TEXT        NOT NULL    UNIQUE,
                        memberID    INTEGER     NOT NULL    UNIQUE
                        );'''
        }

        self.__create_tables(self.d_cursor, tableCodes)
        LOGGER.info(f"Connected to {GUILD_DB_PATH}")

    def __create_tables(self, cursor : sqlite3.Cursor, tableCodes : dict):
        for tableName, tableColumn in tableCodes.items():
            query = f'CREATE TABLE IF NOT EXISTS {tableName}{tableColumn}'
            cursor.execute(query)

    def d_commit(self):
        self.d_conn.commit()   
    
    def select_user(self, type, userID : str, required = '*'):
        
        type_condition = ''
        if type == CDB.STUDENT:
            type_condition = 'STUDENT'
        elif type == CDB.ACADEMIC or type == CDB.RESEARCHER:
            type_condition = 'ACADEMIC'
        else:
            raise Exception(f'Student (type={CDB.STUDENT}), Academic (type={CDB.ACADEMIC})')

        query = f'''SELECT {required} FROM {type_condition} WHERE {type_condition}.id == ?;'''
        
        try:
            self.s_cursor.execute(query, (userID,))
            user = self.s_cursor.fetchone()
        except sqlite3.OperationalError as oe:
            if 'no such column' in str(oe):
                raise ColumnValueError(f'No such column as {required}')
            raise oe
        
        if user is None: raise UserNotFoundError(f'User ({userID}) not Found')

        return user

    def select_member(self, memberID : int, required = '*'):
        query = f'''SELECT {required} FROM MEMBER WHERE MEMBER.id = ?;'''
        
        try:
            self.d_cursor.execute(query, (memberID,))
            member = self.d_cursor.fetchone()
        except sqlite3.OperationalError as oe:
            if 'no such column' in str(oe):
                raise ColumnValueError(f'No such column as {required}')
            raise oe
        if member is None: raise MemberNotFoundError(f'Member (id: {memberID}) not Found')
        return member

    def select_department(self, departmentID : str, required = '*'):
        query = f'''SELECT {required} FROM DEPARTMENT WHERE DEPARTMENT.id == ?;'''
        try:
            self.s_cursor.execute(query, (departmentID,))
            department = self.s_cursor.fetchone()
        except sqlite3.OperationalError as oe:
            if 'no such column' in str(oe):
                raise ColumnValueError(f'No such column as {required}')
            raise oe
        if department is None: raise DepartmentNotFoundError(f"Department ({departmentID}) not Found")
        return department

    def select_user_lectures(self, userID : str, type):
        if type == CDB.STUDENT:
            type_condition_table = 'STUDENT_LECTURE'
            type_condition_column = 'studentID'
        elif type == CDB.ACADEMIC or type == CDB.RESEARCHER:
            type_condition_table = 'ACADEMIC_LECTURE'
            type_condition_column = 'academicID'
        else:
            raise Exception('Student (type=0), Academic (type=1)')
        
        query = f'''SELECT lectureCode, lectureBranch FROM {type_condition_table} WHERE {type_condition_column} == ?;'''
    
        self.s_cursor.execute(query, (userID,))
        lectures = self.s_cursor.fetchall()
        
        #if lectures[0] is None: raise LectureNotFoundError(f"User's ({userID}) lectures are not Found!")

        return lectures

    def select_lecture(self, code, branch, required = '*'):
        query = f'''SELECT {required} FROM LECTURE WHERE LECTURE.code == ? and LECTURE.branch == ?;'''

        try:
            self.s_cursor.execute(query, (code,branch,))
            lecture = self.s_cursor.fetchone()
        except sqlite3.OperationalError as oe:
            if 'no such column' in str(oe):
                raise ColumnValueError(f'No such column as {required}')
            raise oe
        if lecture is None: raise LectureNotFoundError(f"Lecture ({code}) not Found")
        return lecture

    def select_guild_lecture(self, code : str, required = '*'):
        query = f'''SELECT {required} FROM LECTURE WHERE LECTURE.code == ?;'''
        try:
            self.d_cursor.execute(query, (code,))
            lecture = self.d_cursor.fetchone()
        except sqlite3.OperationalError as oe:
            if 'no such column' in str(oe):
                raise ColumnValueError(f'No such column as {required}')
            raise oe
        if lecture is None: raise GuildLectureNotFoundError(f"Lecture ({code}) not Found")
        return lecture

    def select_sublist(self, lectureCode : str):
        query = f'''SELECT memberID FROM SUBLIST WHERE SUBLIST.lectureCode == ?;'''
        
        self.d_cursor.execute(query, (lectureCode,))
        return self.d_cursor.fetchmany()     

    def update_member(self, memberID : int, required : str = '', value = 0):
        if required == '':
            raise ColumnValueError('You need to specify update column')
        
        query = f'''
                UPDATE MEMBER
                SET {required} = ?
                WHERE MEMBER.id == ?;
            '''
        try:    
            self.d_cursor.execute(query, (value, memberID, ))
            self.d_commit()
        except sqlite3.OperationalError as oe:
            if 'no such column' in str(oe):
                raise ColumnValueError(f'No such column as {required}')
            raise oe

    def update_lecture_sub(self, code : str, value : int = 0):
        query = f'''
                UPDATE LECTURE
                {'SET subscriber = ?' if value else 'SET subscriber = subscriber + 1'}
                WHERE LECTURE.code == ?;
            '''
        if value:
            self.s_cursor.execute(query, (value, code,))
        else:
            self.s_cursor.execute(query, (code,))
        self.s_conn.commit()
    def make_sub(self, code : str, memberID : int):
        query = f'''
                INSERT INTO SUBLIST (memberID, lectureCode)
                VALUES (?,?)'''
        values = (memberID, code)
        self.d_cursor.execute(query, (values,))
        self.d_commit()
    def remove_sublist(self, lectureCode : str):
        query = f'''
                DELETE FROM SUBLIST WHERE lectureCode = ?
                '''
        values = (lectureCode)
        self.d_cursor.execute(query, (values,))
        self.d_commit()

    def delete_member(self, member : discord.Member):
        query = f'''
                DELETE FROM MEMBER WHERE id = ?
                '''
        values = (member.id)
        self.d_cursor.execute(query, (values,))
        self.d_commit()

    def insert_member(self, member: discord.Member, userID: str, type: int):
        query = f'''INSERT INTO MEMBER (id, nick, userID, time, type)
                    VALUES (?,?,?,?,?)'''
        values = (member.id, member.nick, userID, asctime(), type)
        self.d_cursor.execute(query, values)
        self.d_commit()
    def insert_guild_lecture(self, code : str, role : discord.Role, channel : discord.TextChannel):
        query = f'''INSERT INTO LECTURE (code, channelID, roleID, name)
                    VALUES (?,?,?,?)'''

        values = (code, channel.id, role.id, channel.topic)
        self.d_cursor.execute(query, values)
        self.d_commit()

    def insert_banned(self, member : discord.Member):
        userID = self.select_member(memberID=member.id, required="userID")[0]

        query = f'''INSERT INTO BANNED (userID, memberID)
                    VALUES (?,?)'''
        
        values = (userID, member.id)
        self.d_cursor.execute(query, (values,))
        self.d_commit()
    def delete_banned(self, member: discord.Member):
        query = f'''
                DELETE FROM BANNED WHERE memberID = ?
                '''
        values = (member.id)
        self.d_cursor.execute(query, (values,))
        self.d_commit()

    ##UTILS:

    def get_member_anonName(self, member : discord.Member) -> str:
        memberAnonName = self.select_member(memberID=member.id, required='hash')
        if memberAnonName[0] is None:
            md5hash = md5(f'{SEED}{member.id}'.encode('ASCII')).hexdigest()
            self.update_member(memberID=member.id, required='hash', value=md5hash)
            return md5hash
        else:
            return memberAnonName[0]
    def is_member_exist(self, member : discord.Member) -> bool:
        query = f'''SELECT EXISTS(SELECT id FROM MEMBER WHERE MEMBER.id = ?);'''
        self.d_cursor.execute(query, (member.id,))

        return bool(self.d_cursor.fetchone()[0])
    def is_user_exist(self, userID: str) -> bool:
        query = f'''SELECT EXISTS (
                    SELECT id FROM STUDENT WHERE id = ?
                    UNION
                    SELECT id FROM ACADEMIC WHERE id = ?
                    );'''
        self.s_cursor.execute(query, (userID,userID,))

        return bool(self.s_cursor.fetchone()[0])
    def is_user_registered(self, userID: str) -> bool:
        query = f'''SELECT EXISTS(SELECT userID FROM MEMBER WHERE MEMBER.userID = ?);'''
        self.d_cursor.execute(query, (userID,))

        return bool(self.d_cursor.fetchone()[0])
    def is_user_banned(self, userID: str) -> bool:
        query = f'''SELECT EXISTS(SELECT userID FROM BANNED WHERE BANNED.userID = ?);'''
        self.d_cursor.execute(query, (userID,))

        return self.d_cursor.fetchone()[0]
    def is_academic_researcher(self, userID: str) -> bool:
        query = f'''SELECT title FROM ACADEMIC WHERE ACADEMIC.id = ?;'''
        self.s_cursor.execute(query, (userID,))
        if self.s_cursor.fetchone()[0] == 'ARAŞTIRMA GÖREVLİSİ':
            return True
        return False

class ColumnValueError(ValueError):
    pass

class UserNotFoundError(ValueError):
    pass

class MemberNotFoundError(UserNotFoundError):
    pass

class DepartmentNotFoundError(ValueError):
    pass

class LectureNotFoundError(ValueError):
    pass
class GuildLectureNotFoundError(ValueError):
    pass