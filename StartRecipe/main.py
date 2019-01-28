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

        # set your optional utterance parameters to response
        if req['action']['parameters'].get('food') != None:
            self.set_parameters(
                {'food': req['action']['parameters']['food']['value']})

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
            try:
                HTTPresponse = HTTPrequest.get(url, headers=header)
                self.set_parameters({
                    'ID': HTTPresponse.json()['id']
                })
            except:
                print('Login failed. Maybe AT expired.')
                self.res['resultCode'] = 'LoginFailed'

    def get_food_status(self, req):
        if req['action']['parameters'].get('food') == None:
            self.set_parameters({
                'status': 'nofood',
                'foodList': 'null',
                'foodList1': 'null'
            })
        else:
            p_food = req['action']['parameters']['food']['value']
            p_food = p_food.replace(' ', '')
            ptype_food = req['action']['parameters']['food']['type']

            if ptype_food == 'FOOD':
                try:
                    conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, charset='utf8')
                    cur = conn.cursor()
                    sql = """select * from food where replace(food, ' ','') = %s"""
                    cur.execute(sql, (p_food, ))
                    rows = cur.fetchone()
                    if rows == None:
                        self.set_parameters({
                            'status': 'notready',
                            'foodList': 'null',
                            'foodList1': 'null'
                        })
                    else:
                        self.set_parameters({
                            'status': 'food',
                            'foodList': 'null',
                            'foodList1': 'null'
                        })
                except:
                    print('DB Error')
                    self.res['resultCode'] = 'DBerror'
                finally:
                    conn.close()

            elif ptype_food == 'FOODGROUP':
                try:
                    conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, charset='utf8')
                    cur = conn.cursor()
                    sql = """select * from food where replace(foodgroup, ' ','') = %s order by likes desc"""
                    cur.execute(sql, (p_food, ))
                    rows = cur.fetchall()

                    foodList = []
                    foodListStr = ''

                    for food in rows:
                        foodList.append(food[0])

                    foodListStr = ', '.join(foodList)

                    self.set_parameters({
                        'status': 'foodgroup',
                        'foodList': foodListStr,
                        'foodList1': rows[0][0]
                    })
                except:
                    print('DB Error')
                    self.res['resultCode'] = 'DBerror'
                finally:
                    conn.close()

def main(args, event):
    print(args)
    response = Response(args)
    response.get_ID(args)
    response.get_food_status(args)
    print(response.res)
    return response.res
