from CLogger import CLogger
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class CMail():
    port = 465
    smtp_server_domain_name = "smtp.gmail.com"
    def __init__(self, MAILADD, MAILADD_PASS, logger : CLogger):
        
        global LOGGER
        LOGGER = logger
        

        self.sender_mail = MAILADD
        self.password = MAILADD_PASS
        self.ssl_context = ssl.create_default_context()
        self.service = smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=self.ssl_context)
        

    def sendVerCode(self, emailTo, name, verCode):
        self.service.login(self.sender_mail, self.password)
        
        
        mail = MIMEMultipart('alternative')
        mail['Subject'] = 'CBOT Doğrulama Kodu'
        mail['From'] = self.sender_mail
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

        self.service.sendmail(self.sender_mail, emailTo, mail.as_string())
        self.service.login(self.sender_mail, self.password)
