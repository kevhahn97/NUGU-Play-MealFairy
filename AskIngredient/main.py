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
        self.set_parameters(
            {'AI_food': req['action']['parameters']['AI_food']['value']})
            

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)


    def get_ID(self, req):
        if req['context']['session'].get('accessToken') == None:
            return 'id_from_AWS'
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


    def make_response(self, req, ID):
        try:
            p_food = req['action']['parameters']['AI_food']['value']
            p_food = p_food.replace(' ', '')
            conn = pymysql.connect(
                host=rds_host, user=name, passwd=password, db=db_name, 
                charset='utf8', cursorclass=pymysql.cursors.DictCursor)
            cur = conn.cursor()
            sql = """select food.food, ment from food join ingredient_ment on food.food = ingredient_ment.food where replace(food.food, ' ','') = %s"""
            cur.execute(sql, (p_food, ))
            rows = cur.fetchone()
            if rows == None: #food not ready
                self.set_parameters({
                    'AI_response': '죄송합니다. 아직 배우고 있는 음식이에요.'
                })
            else:
                if ID != 'null':
                    sql = """insert into food_logs values (%s, default, 0, %s)"""
                    cur.execute(sql, (ID, rows['food']))
                    conn.commit()

                self.set_parameters({
                    'AI_response': rows['ment']
                })
        except Exception as e:
            print('DB Error', e)
            self.res['resultCode'] = 'DBerror'
        finally:
            conn.close()


def main(args, event):
    print(args)
    response = Response(args)
    ID = response.get_ID(args)
    response.make_response(args, ID)
    print(response.res)
    return response.res