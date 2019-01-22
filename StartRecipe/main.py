import pymysql
import requests as HTTPrequest
import credentials

rds_host    = credentials.rds_host
name        = credentials.name    
password    = credentials.password
db_name     = credentials.db_name 

class Response:
    def __init__(self, req):
        self.res = {'version': req['version']}
        self.res['resultCode'] = 'OK'
        self.res['output'] = {}

        # set your optional utterance parameters to response
        if req['action']['parameters'].get('food') != None:
            self.set_parameters(
                {'gu': req['action']['parameters']['food']['value']})

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)

    def get_ID(self, req):
        if req['context']['session'].get('accessToken') == None:
            self.set_parameters({'ID': 'null'})
        else:
            at = req['context']['session']['accessToken']
            
            #send GET HTTP request
            url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            header = {
                'Authorization': 'Bearer ' + at
            }

            HTTPresponse = HTTPrequest.get(url, headers = header)
            self.set_parameters({'ID': HTTPresponse.json()['id']})

    def get_food_status(self, req):
        if req['action']['parameters'].get('food') == None:
            self.set_parameters({
                'status': 'nofood',
                'foodList': 'null'
            })
        else:
            p_food = req['action']['parameters']['food']['value']
            ptype_food = req['action']['parameters']['food']['type']
            conn = pymysql.connect(host = rds_host, user = name, passwd=password, db = db_name, charset='utf8')
            cur = conn.cursor()

            if ptype_food == 'FOOD':    
                sql = 'select * from user where food = "' + p_food + '"'
                cur.execute(sql)
                rows = cur.fetchone()
                
            elif ptype_food == 'FOODGROUP':
                sql = 'select * from user where foodgroup = "' + p_food + '"'
                cur.execute(sql)
                rows = cur.fetchone()

            conn.close()


        self.set_parameters({
            'status': 'food',
            'foodList': 'null'
            })

           
def main(args, event):
    response = Response(args)
    response.get_food_status(args)
    response.get_ID(args)
    return response.res
