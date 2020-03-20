import smtplib
from os.path import basename
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

def get_creds():
    f=open("smtp.creds",'r')
    user,password=f.readline().strip().split(',')
    f.close()
    return user,password

def send_email(subject,body,pngfiles=[]):
    sender,passwd = get_creds()
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(sender,passwd)
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = 'mouse9911@gmail.com'
    msg.preamble = 'Not sure what goes here'
    msg.attach(MIMEText(body))
    for file in pngfiles:
        with open(file, 'rb') as fp:
            img = MIMEImage(fp.read())
        msg.attach(img)
    server.send_message(msg)
    server.quit()

send_email('this sub','here bod')
