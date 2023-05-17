from common.globals import CBOT_MAIL_ADD, CBOT_MAIL_PASS

from CLogger import CLogger
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

LOGGER = CLogger(name="CMAIL")

class CMail():
    port = 465
    smtp_server_domain_name = "smtp.gmail.com"

    __instance = None
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):        
        self.address = CBOT_MAIL_ADD
        self.ssl_context = ssl.create_default_context()
        self.service = smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=self.ssl_context)
        

    def sendVerCode(self, emailTo, name, verCode):
        self.service.login(self.address, CBOT_MAIL_PASS)

        mail = MIMEMultipart('alternative')
        mail['Subject'] = 'CBOT Doğrulama Kodu'
        mail['From'] = self.address
        mail['To'] = emailTo

        text_template = f"""
        CBOT

        Merhaba {name},
        Doğrulama kodu: {str(verCode)}
        """
        html_template = f"""
        <h1>CBOT</h1>

        <p>Merhaba {name},</p>
        <p>Doğrulama kodu: <b>{str(verCode)}</b></p>
        """

        html_content = MIMEText(html_template, 'html')
        text_content = MIMEText(text_template, 'plain')

        mail.attach(text_content)
        mail.attach(html_content)

        self.service.sendmail(self.address, emailTo, mail.as_string())

        self.service.quit()
        


