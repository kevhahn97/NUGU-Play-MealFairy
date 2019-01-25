import pymysql
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

        self.set_parameters({
            'food': req['action']['parameters']['food']['value'],
            'foodList': req['action']['parameters']['foodList']['value'],
            'status': req['action']['parameters']['status']['value'],
            'ID': req['action']['parameters']['ID']['value'],
            'foodSelected': req['action']['parameters']['foodSelected']['value'],
            'statusSelected': req['action']['parameters']['statusSelected']['value']
        })

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)

    def make_response(self, req):
        ID = req['action']['parameters']['ID']['value']
        if ID == 'null':
            self.set_parameters({
                'SR_FG_FS_F_OBO_response': '한 단계씩 도와드리는 기능은 계정을 연동하셔야 사용하실 수 있어요. 누구 앱 좌측 메뉴에서 집밥 요정 Play를 찾아 계정을 연동해 주세요.'
            })
        else:
            p_food_selected = req['action']['parameters']['foodSelected']['value']
            p_food_selected = p_food_selected.replace(' ','')
            try:
                conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, 
                    charset='utf8', cursorclass=pymysql.cursors.DictCursor)
                cur = conn.cursor()
                sql = """select * from food join recipe_onebyone on food.food = recipe_onebyone.food where replace(food.food, " ", "") = %s and recipe_onebyone.seq = 1;"""
                cur.execute(sql, (p_food_selected, ))
                rows = cur.fetchone()

                sql_replace = """replace user values (%s, %s, %s, 1);"""
                cur.execute(sql_replace, (ID, rows['food'], rows['len']))
                conn.commit()

                res = rows['food'] + ' ' + str(rows['people']) + '인분 기준으로 예상 조리 시간은 ' + str(rows['time']) + '분입니다. ' + rows['recipe']
                self.set_parameters({
                    'SR_FG_FS_F_OBO_response': res
                })
            except:
                print('DB Error')
                self.res['resultCode'] = 'DBerror'
            finally:
                conn.close()

def main(args, event):
    print('HTTP request', args)
    response = Response(args)
    ID = response.make_response(args)
    print('HTTP request', response.res)
    return response.res
