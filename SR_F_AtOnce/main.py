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
            'ID': req['action']['parameters']['ID']['value']
        })

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)

    def get_recipe(self, req):
        p_food = req['action']['parameters']['food']['value']
        p_food = p_food.replace(' ', '')
        
        try:
            conn = pymysql.connect(host=rds_host, user=name, passwd=password, db=db_name, charset='utf8')
            cur = conn.cursor()
            sql = """select recipe from food join recipe_atonce on food.food = recipe_atonce.food where replace(food.food, ' ', '') = %s"""
            cur.execute(sql, (p_food, ))
            rows = cur.fetchone()
            self.set_parameters({
                'SR_F_AO_response': rows[0]
            })
        except:
            print('DB Error')
            self.res['resultCode'] = 'DBerror'
        finally:
            conn.close()

def main(args, event):
    print(args)
    response = Response(args)
    response.get_recipe(args)
    print(response.res)
    return response.res