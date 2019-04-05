import pymysql
import requests as HTTPrequest
import credentials

rds_host = credentials.rds_host
name = credentials.name
password = credentials.password
db_name = credentials.db_name

def matmult(a,b):
    zip_b = zip(*b)
    zip_b = list(zip_b)
    return [[sum(ele_a*ele_b for ele_a, ele_b in zip(row_a, col_b)) 
             for col_b in zip_b] for row_a in a]


def zero_matrix(row_size,col_size):
    mat = list()
    for i in range(row_size):
        row = list()
        for j in range(col_size):
            row.append(0)
        mat.append(row)
    return mat

def transpose(mat):
    col_size = len(mat[0])
    row_size = len(mat)
    new_mat = list()
    for i in range(col_size):
        new_row = list()
        for j in range(row_size):
            new_row.append(mat[j][i])
        new_mat.append(new_row)
    return new_mat


def food2seq(food):
    return {'소고기 미역국':0, '들깨 미역국': 1, '시금치 무침': 2, '알리오 올리오': 3}.get(food)


def type2seq(type):
    return {'한식':0,'양식':1,'국 요리':2,'반찬':3,'면 요리':4}.get(type)


def seq2type(seq):
    return {0:'한식',1:'양식',2:'국 요리',3:'반찬',4:'면 요리'}.get(seq)


def get_best_food(ID, cur):
    sql = """select food, type, count(*) count from food_logs where user = %s group by food, type"""
    cur.execute(sql, (ID, ))
    rows = cur.fetchall()
    log_count = 0
    for r in rows:
       log_count = log_count + r['count']
    if log_count == 0:
        return None

    food_count = 4
    log_type_count = 3
    food_type_count = 5
    food_log = zero_matrix(food_count,log_type_count)
    for r in rows:
        food_log[food2seq(r['food'])][r['type']] = r['count']
    w = zero_matrix(3,1)
    w[0][0] = 1
    w[1][0] = 3
    w[2][0] = 9
    res = matmult(food_log, w)
    res = transpose(res)
    sql = """select food, type from food_type"""
    cur.execute(sql)
    rows = cur.fetchall()
    w_type = zero_matrix(food_count, food_type_count)
    for r in rows:
        w_type[food2seq(r['food'])][type2seq(r['type'])] = 1
    res = matmult(res, w_type)
    score_list = res[0]
    best_type_name = seq2type(score_list.index(max(score_list)))

    sql = """select food.food from food 
    left join food_logs on food.food = food_logs.food 
    join food_type on food.food = food_type.food 
    where food_type.type = %s 
    and (food_logs.user= %s or ifnull(food_logs.user, '0') = '0' )
    group by food.food 
    order by count(user)"""

    cur.execute(sql, (best_type_name, ID))
    rows = cur.fetchone()

    return (best_type_name, rows['food'])


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
                'RF_response': '음식 추천 기능은 계정을 연동하셔야 사용하실 수 있어요. 누구 앱 좌측 메뉴에서 집밥 요정 Play를 찾아 계정을 연동해 주세요. 집밥 요정에 익숙하지 않으시다면 도움말 들려줘. 라고 말씀해 보세요'
            })
        elif ID == 'expired':
            self.set_parameters({
                'RF_response': '죄송합니다. 계정 정보를 가져오는 과정에서 오류가 발생했어요. 잠시 후에 다시 시도해 주세요.'
            })
        else:
            try:
                conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, 
                    charset='utf8', cursorclass=pymysql.cursors.DictCursor)
                cur = conn.cursor()
                best_food = get_best_food(ID, cur)
                if best_food == None:
                    self.set_parameters({
                        'RF_response': '당신의 취향 정보가 없어서 아직은 추천해 드리기 어려워요. 집밥 요정을 더 사용하시다가 다시 물어봐 주시면 알려 드릴게요.'
                    })
                else:
                    res = best_food[0] + ' 좋아하시는 것 같아요. ' + best_food[1] + ' 어떠세요?'
                    self.set_parameters({
                        'RF_response': res
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
