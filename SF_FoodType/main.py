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
            'foodtype': req['action']['parameters']['foodtype']['value']
        })

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)

    def make_response(self, req):
        p_foodtype = req['action']['parameters']['foodtype']['value']
        p_foodtype = p_foodtype.replace(' ', '')
        try:
            conn = pymysql.connect(
                host=rds_host, user=name, passwd=password, db=db_name, 
                charset='utf8', cursorclass=pymysql.cursors.DictCursor)
            cur = conn.cursor()
            sql = """select food.food as food from food join food_type on food.food = food_type.food where replace(type, ' ', '') = %s order by likes desc"""
            cur.execute(sql, (p_foodtype, ))
            rows = cur.fetchall()
            food_list = []
            for food in rows:
                food_list.append(food['food'])
            res = '. '.join(food_list)
            self.set_parameters({
                'SF_FT_response': res,
                'SF_FT_sample': rows[0]['food']
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