import asyncio
import websockets
import pymysql
import json
import re

def logincheck(usrnamestr,passwdstr):
    '''将登录信息发送至数据库进行查找'''

    conn=pymysql.connect(host='127.0.0.1',user='root',passwd='root',port=3306,db='lovechatroom',charset='utf8')
    cur=conn.cursor()
            
    sql="SELECT * FROM user WHERE uid='%s' and pwd='%s'"%(usrnamestr,passwdstr)
    #SELECT * FROM user WHERE uid='1' or 1=1 or '1' and pwd=md5('%s')
    cur.execute(sql)
    data=cur.fetchall()
    cur.close()
    conn.close()
    return data

def checkusrin(usrnamestr):
    '''查看用户账号是否在数据库中'''

    conn=pymysql.connect(host='127.0.0.1',user='root',passwd='root',port=3306,db='lovechatroom',charset='utf8')
    cur=conn.cursor()
            
    #检查是否存在用户名被占用
    sql="SELECT * FROM user WHERE uid='%s'"%(usrnamestr)
    cur.execute(sql)
    data=cur.fetchall()
    return data

def register(usrnamestr,passwdstr):
    '''将注册信息发送至数据库进行注册'''

    data=checkusrin(usrnamestr) #检查用户名是否出现占用
    if data: 
        return 0            #用户名被占用
    else:
        conn=pymysql.connect(host='127.0.0.1',user='root',passwd='root',port=3306,db='lovechatroom',charset='utf8')
        cur=conn.cursor()
        sql="INSERT INTO user(uid,pwd) VALUES('%s','%s')"%(usrnamestr,passwdstr)
        result=-1
        try:
            cur.execute(sql)
            result=1        #注册成功
        except:
            result=-1       #注册失败
    cur.close()
    conn.close()   
    return result

async def echo(websocket,path):
    async for message in websocket:
        logindict=json.loads(message)
        print(logindict)
        if(logindict['type']==1):
            #正则表达式去除数字字母以外的东西，防止SQL注入
            pa=re.compile(r'\w+')
            usrnamelist=pa.findall(logindict['usrname'])
            usrnamestr=''.join(usrnamelist)
            passwdlist=pa.findall(logindict['passwd'])
            passwdstr=''.join(passwdlist)

            data=logincheck(usrnamestr,passwdstr)
            if data: 
                await websocket.send(usrnamestr)
            else:
                await websocket.send('0')

            
        elif(logindict['type']==2):
            #正则表达式检查输入,不得出现字母数字以外的字符
            pa=re.compile(r'\w+')
            usrnamelist=pa.findall(logindict['usrname'])
            usrnamestr=''.join(usrnamelist)
            passwdlist=pa.findall(logindict['passwd'])
            passwdstr=''.join(passwdlist)
                            
            if len(usrnamestr)==len(logindict['usrname']) and len(passwdstr)==len(logindict['passwd']) and len(usrnamestr)<=10 and (len(usrnamestr)!=0 and len(passwdstr)!=0):
                result=register(usrnamestr,passwdstr)
                if result==1:                   #注册成功
                    await websocket.send('1')
                elif result==0:                 #用户名被占用
                    await websocket.send('0')
                elif result==-1:                #数据库内部错误
                    await websocket.send('-1')

            #不得出现特殊字符
            elif len(usrnamestr)!=len(logindict['usrname']) or len(passwdstr)!=len(logindict['passwd']):
                await websocket.send('2')

            #不得多于10字符
            elif len(usrnamestr)>10:
                await websocket.send('3')

            #用户名或密码为空
            elif len(usrnamestr)==0 or len(passwdstr)==0:
                await websocket.send('4')       

asyncio.get_event_loop().run_until_complete(websockets.serve(echo,"localhost",2021))
asyncio.get_event_loop().run_forever()