import asyncio
from pymysql.connections import SSL_ENABLED
import websockets
import pymysql
import json

def ifDelete():
    '''消息数量不能超过30，查询是否需要删除之前的消息记录'''

    conn=pymysql.connect(host='127.0.0.1',user='root',passwd='root',port=3306,db='lovechatroom',charset='utf8')
    cur=conn.cursor()
    sql="SELECT * FROM message"
    result=-1
    cur.execute(sql)
    result=cur.fetchall()
    resultlen=len(result)

    cur.close()
    conn.close()   
    return resultlen

def deleteMessage():
    '''删除遥远消息记录，减少数据库负担'''

    ifdel=ifDelete()
    if(ifdel>30):
        conn=pymysql.connect(host='127.0.0.1',user='root',passwd='root',port=3306,db='lovechatroom',charset='utf8')
        cur=conn.cursor()
        sql="DELETE FROM message ORDER BY time LIMIT 1"
        try:
            cur.execute(sql)
            return 1        #删除成功
        except:
            return -1       #删除失败
    else:
        return 1

def insertMessage(uid,msg,time,msgTo):
    '''插入消息信息'''

    delresult=deleteMessage()
    if delresult==1:
        conn=pymysql.connect(host='127.0.0.1',user='root',passwd='root',port=3306,db='lovechatroom',charset='utf8')
        cur=conn.cursor()
        sql="INSERT INTO message(uid,msg,time,msgTo) VALUES('%s','%s','%s','%s')"%(uid,msg,time,msgTo)
        try:
            cur.execute(sql)
            result=1        #插入成功
        except:
            result=-1       #插入失败

        cur.close()
        conn.close()   
        return result
    else:
        return -2

def updatePassword(uid,pwd):
    '''修改密码'''

    conn=pymysql.connect(host='127.0.0.1',user='root',passwd='root',port=3306,db='lovechatroom',charset='utf8')
    cur=conn.cursor()
    sql="UPDATE user set pwd='%s' where uid='%s'"%(pwd,uid)
    result=-1
    try:
        cur.execute(sql)
        conn.commit()
        result=1        #修改成功
    except:
        result=-1       #修改失败

    cur.close()
    conn.close()   
    return result

users={}                            #字典，保存账号和socket一一映射关系
async def chat(websocket,path):
    async for message in websocket:
        msgdict=json.loads(message) #解析message的json信息成为一个字典
        msgstr=json.dumps(msgdict)  #重新封装message信息为json字符串

        #插入消息信息到数据库
        if(msgdict['time']!=''):
            insertres=insertMessage(msgdict['uid'],msgdict['msg'],msgdict['time'],msgdict['msgTo'])
            if insertres!=1:
                await websocket.send("-2")

        #当得到用户上线信息时，在users字典里面加入一项信息
        if msgdict['type']=='message' and msgdict['msgTo']=='chatserver':
            if msgdict['uid'] in list(users.keys()):    #防止用户重复登录
                await users[msgdict['uid']].send("2")
                users[msgdict['uid']]=websocket
            else:
                users[msgdict['uid']]=websocket
            print(users)
        
        #用户关闭连接，从users字典中移除该用户
        elif msgdict['type']=='message' and msgdict['msgTo']=='chatserverclose':
            del users[msgdict['uid']]
            print(users)

        #用户修改密码
        elif msgdict['type']=='updatepwd':
            updateres=updatePassword(msgdict['uid'],msgdict['msg'])
            if updateres==1:
                await websocket.send("3")
            else:
                await websocket.send("-3")

        #用户在线列表生成 后端代码
        userslist=list(users.keys())        #获取所有用户账号
        userslistlength=len(userslist)      #获取在线用户数量
        usersdict={}                        #构造字典，以便之后传输到前端
        usersdict['type']='userslist'       #表头信息：type:userslist
        usersdict['length']=userslistlength #用户数量参数
        for i in range(0,len(userslist)):   #构造用户字典，_0:用户1, _1:用户2...
            j="_"+str(i)
            usersdict[str(j)]=userslist[i]
        print(usersdict)
        usersstr=json.dumps(usersdict)      #封装用户列表json字符串
        
        if len(users)>0:
            await asyncio.wait([user.send(msgstr) for user in users.values()])      #群发消息
            await asyncio.wait([user.send(usersstr) for user in users.values()])    #群发用户列表信息

asyncio.get_event_loop().run_until_complete(websockets.serve(chat,"localhost",2020))
asyncio.get_event_loop().run_forever()