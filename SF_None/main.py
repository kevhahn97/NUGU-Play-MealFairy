import pymysql
import credentials

rds_host = credentials.rds_host
name = credentials.name
password = credentials.password
db_name = credentials.db_name

def get_count(seq):
    return {
        1: '한', 2: '두', 3: '세', 4: '네', 5: '다섯', 6: '여섯', 7: '일곱', 8: '여덟', 9: '아홉', 10: '열', 11: '열한', 12: '열두', 13: '열세', 14: '열네', 15: '열다섯', 16: '열여섯',
        17: '열일곱', 18: '열여덟', 19: '열아홉', 20: '스무', 21: '스물 한', 22: '스물 두', 23: '스물 세', 24: '스물 네', 25: '스물 다섯', 26: '스물 여섯', 27: '스물 일곱', 28: '스물 여덟', 
    }.get(seq)

class Response:
    def __init__(self, req):
        self.res = {'version': req['version']}
        self.res['resultCode'] = 'OK'
        self.res['output'] = {}

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)

    def make_response(self, req):
        try:
            conn = pymysql.connect(
                host=rds_host, user=name, passwd=password, db=db_name, 
                charset='utf8', cursorclass=pymysql.cursors.DictCursor)
            cur = conn.cursor()
            #sql = """select type, COUNT(*) as type_count from food join food_type on food.food = food_type.food group by type"""
            sql = """select food from food order by likes desc limit 3"""
            cur.execute(sql)
            rows = cur.fetchall()
            food_list = []
            for row in rows:
                food_list.append(row['food'])
            food_list = '. '.join(food_list)
            res = food_list
            self.set_parameters({
                'SF_N_response': res
            })
        except:
            print('DB Error')
            self.res['resultCode'] = 'DBerror'
        finally:
            conn.close()

def main(args, event):
    print(args)
    response = Response(args)
    response.make_response(args)
    print(response.res)
    return response.res