import os
import zipfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication


def login_gmail_smtp(username, password):
    """
    登录谷歌SMTP服务器
    :param username: 邮箱账号
    :param password: 邮箱密码
    :return: 已登录的SMTP服务器对象
    """
    smtp_ssl_host = 'smtp.qq.com'
    smtp_ssl_port = 465
    smtp_server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
    smtp_server.login(username, password)
    return smtp_server


def send_email(smtp_server, sender, recipients, subject, body, attachments=None):
    """
    发送邮件
    :param smtp_server: SMTP服务器对象
    :param sender: 发件人
    :param recipients: 收件人，可以是一个字符串，也可以是一个列表
    :param subject: 邮件主题
    :param body: 邮件正文
    :param attachments: 附件路径列表
    """
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipients if isinstance(recipients, str) else ', '.join(recipients)
    msg['Subject'] = subject
    # 创建HTML格式的正文
    body_html = f"""
    <html>
      <head></head>
      <body style="font-family: Arial, sans-serif;">
        <p style="color: #333; text-indent: 2em;">{body}</p>
      </body>
    </html>
    """

    # 将HTML格式的正文转换为MIMEText对象，并添加到邮件中
    msg.attach(MIMEText(body_html, 'html'))

    if attachments:
        for attachment in attachments:
            attachment_file = MIMEApplication(open(attachment, 'rb').read())
            attachment_file.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
            msg.attach(attachment_file)
    smtp_server.sendmail(sender, recipients, msg.as_string())
    smtp_server.quit()

def compressFiles(files,outfile):
    '''
    多个文件压缩为zipfile
    :param files: list[str] 待压缩文件
    :param outfile: str zipfile
    '''
    zip_obj = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
    for f in files:
        zip_obj.write(f)
    zip_obj.close()

if __name__ == '__main__':
    # 登录谷歌SMTP服务器
    username = 'cccccm21@gmail.com'
    password = 'jcstqircqvimoclg'
    smtp_server = login_gmail_smtp(username, password)

    # 发送邮件
    sender = 'cccccm21@gmail.com'
    recipients = 'yangjia@tech-5d.com'
    # recipients ='taomengyao@tech-5d.com'
    subject = 'TEST'

    # 设置邮件正文
    body = '你好<br>换行<br>1111'
    #添加附件
    attachment = [r'C:\Users\Administrator\Desktop\20230411\东荆河_shape.shp',r'C:\Users\Administrator\Desktop\20230411\东荆河_shape.dbf']
    send_email(smtp_server, sender, recipients, subject, body, attachment)