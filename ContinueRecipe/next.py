import pymysql
import requests as HTTPrequest
import credentials

rds_host = credentials.rds_host
name = credentials.name
password = credentials.password
db_name = credentials.db_name
default_ad_id = 1
default_ad_url = 'https://s3.ap-northeast-2.amazonaws.com/mealfairy/music/%EC%97%B0%EB%91%90'

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


def get_best_ad(ID, cur):
    sql = """select food, type, count(*) count from food_logs where user = %s group by food, type"""
    cur.execute(sql, (ID, ))
    rows = cur.fetchall()
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
    while True:
        best_type_name = seq2type(score_list.index(max(score_list)))
        print(best_type_name)
        sql = """select ad_ment.ad, ad_ment.url, count(user) count 
        from ad_ment left 
        join ad_logs on ad_ment.ad = ad_logs.ad 
        join ad_food_type on ad_ment.ad = ad_food_type.ad 
        where ad_food_type.foodtype = %s 
        and (ad_logs.user= %s
        or ifnull(ad_logs.user, '0') = '0' )
        group by ad_ment.ad 
        order by count(user);"""
        cur.execute(sql, (best_type_name, ID))
        rows = cur.fetchone()
        if rows == None:
            print('not exists')
            score_list.remove(max(score_list))
            if len(score_list) == 0:
                return default_ad_id, default_ad_url
            continue
        else:
            return rows['ad'], rows['url']


class Response:
    def __init__(self, req):
        self.res = {'version': req['version']}
        self.res['resultCode'] = 'OK'
        self.res['output'] = {}
        self.res['directives'] = []

    def set_parameters(self, key_values):
        self.res['output'].update(key_values)
    
    def set_audio_stop(self):
        directive = {
            "type": "AudioPlayer.Stop"
        }
        self.res['directives'].append(directive)

    def set_active_timer(self, time, food, seq):
        offset = (469 - time) * 1000
        token = 'mf_' + food + '_' + str(seq)
        e_token = 'mf_' + food + '_' + str(seq-1)
        directive = {
            "type": "AudioPlayer.Play",
            "audioItem": {     
                "stream": {
                    "url": "https://s3.ap-northeast-2.amazonaws.com/mealfairy/music/mozart+sonata+for+two+piano.m4a",
                    "offsetInMilliseconds": offset,
                    "progressReport": {},
                    "token": token,
                    "expectedPreviousToken": e_token
                }
            }
        }
        self.res['directives'].append(directive)

    def set_ad(self, ad, url):
        token = 'mf_' + 'ad_' + str(ad)
        directive = {
            "type": "AudioPlayer.Play",
            "audioItem": {     
                "stream": {
                    "url": url,
                    "offsetInMilliseconds": 0,
                    "progressReport": {},
                    "token": token,
                    "expectedPreviousToken": token + 'e'
                }
            }
        }
        self.res['directives'].append(directive)

    def set_finish_ad(self, url):
        token = 'mf_' + 'ad_fin'
        directive = {
            "type": "AudioPlayer.Play",
            "audioItem": {     
                "stream": {
                    "url": url,
                    "offsetInMilliseconds": 0,
                    "progressReport": {},
                    "token": token,
                    "expectedPreviousToken": token + 'e'
                }
            }
        }
        self.res['directives'].append(directive)

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
                'CR_response_B': '한 단계씩 도와드리는 기능은 계정을 연동하셔야 사용하실 수 있어요. 누구 앱 좌측 메뉴에서 집밥 요정 Play를 찾아 계정을 연동해 주세요. 집밥 요정에 익숙하지 않으시다면 도움말 들려줘. 라고 말씀해 보세요'
            })
        elif ID == 'expired':
            self.set_parameters({
                'CR_response_B': '죄송합니다. 계정 정보를 가져오는 과정에서 오류가 발생했어요. 잠시 후에 다시 시도해 주세요.'
            })
        else:
            try:
                conn = pymysql.connect(
                    host=rds_host, user=name, passwd=password, db=db_name, 
                    charset='utf8', cursorclass=pymysql.cursors.DictCursor)
                cur = conn.cursor()
                sql = """select user.len, user.food, seq, timer, recipe, ad_ment.ad, ment, url from recipe_onebyone
                join user on user.food = recipe_onebyone.food and user.cur+1 = recipe_onebyone.seq
                left outer join ad_ment on recipe_onebyone.ad = ad_ment.ad
                where id = %s and cur < len"""
                cur.execute(sql, (ID, ))
                rows = cur.fetchone()
                if rows == None:
                    self.set_parameters({
                        'CR_response_B': '현재 진행 중인 요리가 없습니다. 집밥 요정에 익숙하지 않으시다면 도움말 들려줘. 라고 말씀해 보세요.'
                    })
                else:
                    crresponse = rows['recipe']
                    recipe_len = rows['len']
                    recipe_seq = rows['seq']
                    sql = """update user set cur = cur + 1 where id = %s"""
                    cur.execute(sql, (ID, ))
                    conn.commit()
                    if rows['timer'] != None:
                        self.set_active_timer(rows['timer'], rows['food'], rows['seq'])
                    elif rows['ad'] != None:
                        self.set_ad(rows['ad'], rows['url'])
                        crresponse = crresponse + ' ' + rows['ment']
                        sql = """insert into ad_logs values(%s, %s, default)"""
                        cur.execute(sql, (rows['ad'], ID))
                        conn.commit()
                    elif recipe_len == recipe_seq: #recipe done
                        ad_id, url = get_best_ad(ID, cur)
                        self.set_finish_ad(url)
                        sql = """insert into ad_logs values(%s, %s, default)"""
                        cur.execute(sql, (ad_id, ID))
                        conn.commit()
                    elif req['context'].get('supportedInterfaces') != None:
                        token = req['context']['supportedInterfaces']['AudioPlayer']['token']
                        if req['context']['supportedInterfaces']['AudioPlayer']['playerActivity'] == 'PLAYING' and token[:2] == 'mf':
                            self.set_audio_stop()
                    self.set_parameters({
                        'CR_response_B': crresponse
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
