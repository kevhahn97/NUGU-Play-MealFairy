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

        # set your optional utterance parameters to response
        if req['action']['parameters'].get('food') != None:
            self.set_parameters({
                'food': req['action']['parameters']['food']['value'],
                'foodList': req['action']['parameters']['foodList']['value'],
                'status': req['action']['parameters']['status']['value'],
                'ID': req['action']['parameters']['ID']['value'],
                'foodSelected': req['action']['parameters']['foodSelected']['value']
            })

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)

    def get_food_status(self, req):
        p_food_selected = req['action']['parameters']['foodSelected']['value']
        p_food_selected = p_food_selected.replace(' ', '')
        try:
            conn = pymysql.connect(
                host=rds_host, user=name, passwd=password, db=db_name, charset='utf8')
            cur = conn.cursor()
            sql = """select * from food where replace(food, ' ','') = %s"""
            cur.execute(sql, (p_food_selected, ))
            rows = cur.fetchone()
            if rows == None:
                self.set_parameters({
                    'statusSelected': 'notready'
                })
            else:
                self.set_parameters({
                    'statusSelected': 'food'
                })
        except:
            print('DB Error')
            self.res['resultCode'] = 'DBerror'
        finally:
            conn.close()

def main(args, event):
    print(args)
    response = Response(args)
    response.get_food_status(args)
    print(response.res)
    return response.res
