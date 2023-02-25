import re
import imaplib
import email
from email import utils
from email.header import decode_header
import webbrowser
import os
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status as st
from .models import *
from .serializers import *

# Create your views here.

# use your email provider's IMAP server, you can look for your provider's IMAP server on Google
# or check this page: https://www.systoolsgroup.com/imap/
# for office 365, it's this:
imap_server = "imap.gmail.com"


# create an IMAP4 class with SSL


def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)


@api_view(['POST'])
@permission_classes([AllowAny])
def unseenmail(request):
    input_serializer = InputSerializer(data=request.data)
    if input_serializer.is_valid():
        pass
    else:
        return Response(input_serializer.errors, status=st.HTTP_400_BAD_REQUEST)
        # authenticate
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(request.data['username'], request.data['password'])
    status, messages = imap.select("INBOX")
    (retcode, newmessages) = imap.search(None, '(UNSEEN)')
    dec_msg = newmessages[0].decode('ascii').strip()
    new_msg_list = []
    if dec_msg:
        new_msg_list = dec_msg.split(' ')

    for i in new_msg_list:
        from_mail = ''
        text_body = ''
        html_body = ''
        subject = ''
        received_at = ''
        attachment = {}
        res, msg = imap.fetch(i, "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                received_at = utils.parsedate_to_datetime(msg['date'])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                # Make a directory to store a body
                folder = clean(subject) + ''.join(e for e in str(received_at) if e.isalnum())
                folder_name = os.path.join('media', folder)
                if not os.path.isdir(folder_name):
                    os.mkdir(folder_name)
                # decode email sender
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    From = From.decode(encoding)
                from_mail = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', From)[0]
                # if the email message is multipart
                if msg.is_multipart():
                    # iterate over email parts
                    for part in msg.walk():
                        # extract content type of email
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            # get the email body
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            bodypath = os.path.join(folder_name, 'body.txt')
                            open(bodypath, "w").write(body)
                            text_body = 'media/' + folder + "/" + "body.txt"
                        elif content_type == "text/html" and "attachment" not in content_disposition:
                            bodypath = os.path.join(folder_name, 'body.html')
                            open(bodypath, "w").write(body)
                            html_body = 'media/' + folder + "/" + "body.html"
                        elif "attachment" in content_disposition:
                            # download attachment
                            filename = part.get_filename()
                            if filename:
                                filepath = os.path.join(folder_name, filename)
                                attachment.update({i: '{}media/{}/{}'.format(settings.PROJECT_URL, folder, filename)})
                                # download attachment and save it
                                open(filepath, "wb").write(part.get_payload(decode=True))
                else:
                    # extract content type of email
                    content_type = msg.get_content_type()
                    # get the email body
                    body = msg.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        # print only text email parts
                        bodypath = os.path.join(folder_name, 'body.txt')
                        open(bodypath, "w").write(body)
                        text_body = 'media/' + folder + "/" + "body.txt"
                    elif content_type == "text/html":
                        filename = "body.html"
                        bodypath = os.path.join(folder_name, filename)
                        # write the file
                        open(bodypath, "w").write(body)
                        html_body = 'media/' + folder + "/" + "body.html"
                        # open in the default browser
                        # webbrowser.open(filepath)
        mail_data = {
            "subject": subject,
            "from_mail": from_mail,
            "text_body": text_body,
            "html_body": html_body,
            "received_at": received_at,
            "attachments": attachment
        }
        serializer = MailDetailSerializer(data=mail_data)
        if serializer.is_valid():
            serializer.save()
            email_backend = EmailBackend(
                host='smtp.gmail.com',
                use_tls=True,
                port=587,
                username=request.data['username'],
                password=request.data['password']
            )
            email_message = "id: {}\nsubject: {}\nfrom_mail: {}\ntext_body: {}\nhtml_body: {}\nattachments: {}\n" \
                            "received_at: {} ".format(
                serializer.data['id'], serializer.data['subject'], serializer.data['from_mail'],
                settings.PROJECT_URL + serializer.data['text_body'],
                settings.PROJECT_URL + serializer.data['html_body'],
                serializer.data['attachments'], serializer.data['received_at']
            )
            EmailMessage(
                # title:
                "Email task",
                # message:
                email_message,
                # from:
                request.data['username'],
                # to:
                [from_mail],
                connection=email_backend
            ).send()
        else:
            return Response(serializer.errors, status=st.HTTP_400_BAD_REQUEST)
    imap.close()
    imap.logout()
    return Response({"message": "Success"}, status=st.HTTP_200_OK)
