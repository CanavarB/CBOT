from settings.globals import *
from CLogger import CLogger
import sqlite3
from hashlib import md5
from time import asctime


class CDB():
    STUDENT = 0
    ACADEMIC = 1
    AWAY = 2
    RESEARCHER = 3
    
    STUDENT_NAME = 'Öğrenci'
    ACADEMIC_NAME = 'Görevli'
    AWAY_NAME = 'Mezun'
    RESEARCHER_NAME = ACADEMIC_NAME
    def __init__(self, semesterDBPath, guildDBPath, logger : CLogger):
        global LOGGER
        LOGGER = logger
        
        self.s_conn = sqlite3.connect(semesterDBPath)
        LOGGER.info(f"Connected to {semesterDBPath}")
        self.s_cursor = self.s_conn.cursor()
        
        self.d_conn = sqlite3.connect(guildDBPath)
        LOGGER.info(f"Connected to {guildDBPath}")
        self.d_cursor = self.d_conn.cursor()

    def d_commit(self):
        self.d_conn.commit()   
    
    def select_user(self, type, userID : str, required = '*'):
        
        type_condition = ''
        if type == CDB.STUDENT:
            type_condition = 'STUDENT'
        elif type == CDB.ACADEMIC or type == CDB.RESEARCHER:
            type_condition = 'ACADEMIC'
        else:
            raise Exception('Student (type=0), Academic (type=1)')

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
        lectures = self.s_cursor.fetchmany()
        
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
                WHERE MEMBER.id == {memberID};
            '''
        try:    
            self.d_cursor.execute(query, (value,))
            self.d_commit()
        except sqlite3.OperationalError as oe:
            if 'no such column' in str(oe):
                raise ColumnValueError(f'No such column as {required}')
            raise oe

    def __update_lecture_sub(self, code : str, value : int = 0):
        query = f'''
                UPDATE LECTURE
                {'SET subscriber = ?' if value else 'SET subscriber = subscriber + 1'}
                WHERE LECTURE.code == {code};
            '''
        if value:
            self.s_cursor.execute(query, (value,))
        else:
            self.s_cursor.execute(query)
        self.s_conn.commit()
    def make_sub(self, code : str, member : discord.Member):
        self.__update_lecture_sub(code=code)
        query = f'''
                INSERT INTO SUBLIST (memberID, lectureCode)
                VALUES (?,?)'''
        values = (member.id, code)
        self.d_cursor.execute(query, (values,))
        self.d_commit()


    def insert_member(self, member: discord.Member, userID: str, type: int):
        query = f'''INSERT INTO MEMBER (id, name, userID, time, type)
                    VALUES (?,?,?,?,?)'''
        values = (member.id, member.nick, asctime(), userID, type)
        self.d_cursor.execute(query, (values,))
        self.d_commit()
    def insert_guild_lecture(self, role : discord.Role, channel : discord.TextChannel):
        query = f'''INSERT INTO LECTURE (code, channelID, roleID, name)
                    VALUES (?,?,?,?)'''

        values = (channel.name, channel.id, role.id, channel.topic)
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

        return self.d_cursor.fetchone()[0]
    def is_user_exist(self, userID: str) -> bool:
        query = f'''SELECT EXISTS(SELECT id FROM USER WHERE USER.id = ?);'''
        self.s_cursor.execute(query, (userID,))

        return self.s_cursor.fetchone()[0]
    def is_user_registered(self, userID: str) -> bool:
        query = f'''SELECT EXISTS(SELECT userID FROM MEMBER WHERE MEMBER.userID = ?);'''
        self.d_cursor.execute(query, (userID,))

        return self.d_cursor.fetchone()[0]
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