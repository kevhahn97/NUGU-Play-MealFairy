import pymysql
import requests as HTTPrequest
import credentials

rds_host = credentials.rds_host
name = credentials.name
password = credentials.password
db_name = credentials.db_name

class Response:
    def __init__(self, req):
        self.res = {'version': req['version']}
        self.res['resultCode'] = 'OK'
        self.res['output'] = {}

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)

    def get_ID(self, req):
        if req['context']['session'].get('accessToken') == None:
            return 'null'
        else:
            at = req['context']['session']['accessToken']

            #send GET HTTP request
            url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            header = {
                'Authorization': 'Bearer ' + at
            }
            try:
                HTTPresponse = HTTPrequest.get(url, headers=header)
                return HTTPresponse.json()['id']
            except:
                print('Login failed. Maybe AT expired.')
                self.res['resultCode'] = 'LoginFailed'
                return 'expired'

    def check_skipped(self, req, ID):
        if ID == 'null':
            self.set_parameters({
                'TD_response': '',
                'skipped': 'yes'
            })
        elif ID == 'expired':
            self.set_parameters({
                'TD_response': '',
                'skipped': 'yes'
            })
        else:
            try:
                conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, 
                    charset='utf8', cursorclass=pymysql.cursors.DictCursor)
                cur = conn.cursor()
                sql = """select food, cur from user where id = %s"""
                cur.execute(sql, (ID, ))
                rows = cur.fetchone()
                if rows == None:
                    self.set_parameters({
                        'TD_response': '',
                        'skipped': 'yes'
                    })
                else:
                    tokens = req['context']['supportedInterfaces']['AudioPlayer']['token'].split('_')
                    if rows['food'] == tokens[1] and str(rows['cur']) == tokens[2]:
                        sql = """select ment from timer_ment where food = %s and seq = %s"""
                        cur.execute(sql, (rows['food'], rows['cur']))
                        rows = cur.fetchone()
                        self.set_parameters({
                            'TD_response': rows['ment'],
                            'skipped': 'no'
                        })
                    else:
                        self.set_parameters({
                            'TD_response': '',
                            'skipped': 'yes'
                        })
            except:
                print('DB Error')
                self.res['resultCode'] = 'DBerror'
            finally:
                conn.close()

def main(args, event):
    print(args)
    response = Response(args)
    ID = response.get_ID(args)
    response.check_skipped(args, ID)
    print(response.res)
    return response.res
