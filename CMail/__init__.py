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
        self.password = CBOT_MAIL_PASS
        

    def sendVerCode(self, emailTo, name, verCode):

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


        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.address, self.password)
                server.send_message(mail)
            LOGGER.info(f"Ver code send to {emailTo}")
        except:
            LOGGER.critical("Email error")
    
        


