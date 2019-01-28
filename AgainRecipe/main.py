import pymysql
import requests as HTTPrequest
import credentials

def get_sequence(seq):
    return {
        1: '첫', 2: '두', 3: '세', 4: '네', 5: '다섯', 6: '여섯', 7:'일곱', 8:'여덟', 9:'아홉',10:'열', 11:'열한', 12:'열두', 13:'열세', 14:'열네',15:'열다섯', 16:'열여섯'
    }.get(seq)

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

    def make_response(self, req, ID):
        if ID == 'null':
            self.set_parameters({
                'AR_response': '한 단계씩 도와드리는 기능은 계정을 연동하셔야 사용하실 수 있어요. 누구 앱 좌측 메뉴에서 집밥 요정 Play를 찾아 계정을 연동해 주세요. 집밥 요정에 익숙하지 않으시다면 도움말 들려줘. 라고 말씀해 보세요'
            })
        elif ID == 'expired':
            self.set_parameters({
                'AR_response': '죄송합니다. 계정 정보를 가져오는 과정에서 오류가 발생했어요. 잠시 후에 다시 시도해 주세요.'
            })
        else:
            try:
                conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, 
                    charset='utf8', cursorclass=pymysql.cursors.DictCursor)
                cur = conn.cursor()
                sql = """select user.food, recipe, seq from user join recipe_onebyone on user.food = recipe_onebyone.food and user.cur = recipe_onebyone.seq where id = %s"""
                cur.execute(sql, (ID, ))
                rows = cur.fetchone()
                if rows == None:
                    self.set_parameters({
                        'AR_response': '현재 진행 중인 요리가 없습니다. 집밥 요정에 익숙하지 않으시다면 도움말 들려줘. 라고 말씀해 보세요.'
                    })
                else:
                    res = rows['food'] + '의 ' + get_sequence(rows['seq']) + ' 번째 단계입니다. ' + rows['recipe']
                    self.set_parameters({
                        'AR_response': res
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
