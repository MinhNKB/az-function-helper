import logging

import azure.functions as func

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import os

from .df_decorate import df_decorate_tohtml

# get from req_body, if none then get from os env, if none then return default value
def get_param_default_behavior(key, req_body, default_value):
    value = req_body.get(key)
    value = os.getenv(key) if value is None else value
    value = default_value if value is None else value
    return value

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('Python HTTP trigger SendEmail function processed a request.')
        
        req_body = req.get_json()
        logging.info(req_body)
        # some config are not nested json yet since feature are being added after the app are deployed and using
        # will have v2 with better config group after requirement is stable
        # TODO: multiple receiver, CC, BCC
        # Sample body
        # {
        #     "from": "",
        #     "from_password": "",
        #     "to": "",
        #     "subject": "",
        #     "header": "", 
        #     "message": "", 
        #     "json_table": "", 
        #     "message_type": "", # plain / html
        #     "footer": "",
        #     "smtp_server": "smtp.office365.com",
        #     "smtp_port": 587,
        # }
        
        # check required params
        for i in ["to", "header"]:
            if req_body.get(i) is None:
                msg = f"Please pass field '{i}' in the request body"
                logging.error(msg)
                return func.HttpResponse(
                    json.dumps({'status': msg}),
                    status_code=400
                )
        msg_type = req_body.get('message_type', 'plain')
        if msg_type not in ['plain', 'html']:
            msg = 'message_type support plain or html only'
            logging.error(msg)
            return func.HttpResponse(
                json.dumps({'status': msg}),
                status_code=400
            )

        # connect sftp
        smtp_server = get_param_default_behavior('smtp_server', req_body, 'smtp.office365.com')
        smtp_port = get_param_default_behavior('smtp_port', req_body, '587')
        if type(smtp_port) == str and not smtp_port.isdigit():
            msg = 'smtp_port must be int'
            logging.error(msg)
            return func.HttpResponse(
                json.dumps({'status': msg}),
                status_code=400
            )
        try:
            smtp_port = int(smtp_port)
        except Exception as e:
            msg = f"smtp_port convert to int error: {str(e)}"
            logging.error(msg)
            return func.HttpResponse(
                json.dumps({'status': msg}),
                status_code=400
            )

        # build email body
        message = MIMEMultipart("alternative")
        message["Subject"] = req_body.get('subject', 'Automatic Email From Function App')
        message["From"] = get_param_default_behavior('from', req_body, None)
        message["To"] = req_body.get('to')
        
        # a dict to hold all message and concatenate later
        msg_body_dict = {
            'html': [],
            'plain': [],
        }

        if req_body.get('header'):
            msg_body_dict.get(msg_type).append(req_body.get('header'))

        if req_body.get('message'):
            msg_body_dict.get(msg_type).append(req_body.get('message'))

        if req_body.get('json_table'):
            body_json = req_body.get('json_table')

            # this is for supporting both json array or json escaped string
            if type(body_json) == list:
                body_json = json.dumps(body_json).replace('null','"N/A"')

            table_df = pd.read_json(body_json)
    

            # apple some styling
            # TODO: extend config
            html_table = df_decorate_tohtml(table_df)
            msg_body_dict.get('html').append(html_table)

        if req_body.get('footer'):
            msg_body_dict.get(msg_type).append(req_body.get('footer'))

        # join all msg plain
        msg_plain = MIMEText('\n'.join(msg_body_dict.get('plain')), 'plain')
        message.attach(msg_plain)

        # join all msg html
        msg_html = MIMEText('\n'.join(msg_body_dict.get('html')), 'html')
        message.attach(msg_html)

        mailserver = smtplib.SMTP(smtp_server, smtp_port)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(get_param_default_behavior('from', req_body, None), get_param_default_behavior('from_passwordw', req_body, None))
        mailserver.sendmail(get_param_default_behavior('from', req_body, None), req_body.get('to').split(','),msg=message.as_string())
        mailserver.quit()

        return func.HttpResponse(
            json.dumps({"status": "success"}),
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"status": f"Internal Server error: {str(e)}"}),
            status_code=500
        )

