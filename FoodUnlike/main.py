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
            {'FU_food': req['action']['parameters']['FU_food']['value']})
            

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


    def make_response(self, req, ID):
        if ID == 'null':
            self.set_parameters({
                'FU_response': '음식 좋아요 기능은 계정을 연동하셔야 사용하실 수 있어요. 누구 앱 좌측 메뉴에서 집밥 요정 Play를 찾아 계정을 연동해 주세요. 집밥 요정에 익숙하지 않으시다면 도움말 들려줘. 라고 말씀해 보세요'
            })
        elif ID == 'expired':
            self.set_parameters({
                'FU_response': '죄송합니다. 계정 정보를 가져오는 과정에서 오류가 발생했어요. 잠시 후에 다시 시도해 주세요.'
            })
        else:
            try:
                p_food = req['action']['parameters']['FU_food']['value']
                p_food = p_food.replace(' ', '')
                conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, 
                    charset='utf8', cursorclass=pymysql.cursors.DictCursor)
                cur = conn.cursor()

                sql = """select food from food where replace(food, ' ','') = %s"""
                cur.execute(sql, (p_food, ))
                rows = cur.fetchone()
                if rows == None: #food not ready
                    self.set_parameters({
                        'FU_response': '죄송합니다. 아직 배우고 있는 음식이에요.'
                    })
                else:
                    food_name = rows['food']

                    sql = """select * from food_logs 
                    where user = %s and type = 2 and 
                    replace(food, ' ', '') = %s"""
                    cur.execute(sql, (ID, p_food))
                    rows = cur.fetchone()
                    if rows == None:
                        res = food_name + ', 좋다고 하신 적이 없으세요.'
                        self.set_parameters({
                            'FU_response': res
                        })
                    else:
                        sql = """delete from food_logs where user = %s and type = 2 and food = %s;"""
                        cur.execute(sql, (ID, food_name))
                        conn.commit()
                        res = food_name + ', 이제는 안 좋아하시는 것으로 알고 있을게요.'
                        self.set_parameters({
                            'FU_response': res
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
    response.make_response(args, ID)
    print(response.res)
    return response.res
