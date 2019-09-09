from flask import Flask, jsonify, abort, make_response, render_template, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import MySQLdb
import qrcode
import time
import subprocess

# Define someone
baseurl='http://airmark.kaniyama.net:37564'


# Initiarize Of Flask
api = Flask(__name__)
CORS(api)  # CORS有効化
api.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
api.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 #1024MB = 1GB OK!


# --------------------------------------------------
# /
#
# > Root
# --------------------------------------------------
@api.route('/', methods=['POST','GET'])
def mainpage():
    log_info(str(session.get('userId')))
    return render_template('index.html')

# --------------------------------------------------
# /regist
#
# > Regist
# --------------------------------------------------
@api.route('/regist', methods=['POST','GET'])
def regist():
    if request.method == 'GET':
        return render_template('register.html')
    
    # 1. get form
    email    = request.form['email']
    twitter  = request.form.get('twitter')
    facebook = request.form.get('facebook')
    github   = request.form.get('github')
    password = request.form['password']

    # 2. connect sql db
    connection = MySQLdb.connect(
        host = 'localhost',
        user = 'hacku',
        password = 'hacku',
        db = 'hacku')
    cursor = connection.cursor()

    # 3. generate user ID
    cursor.execute(
        "SELECT MAX(user_id) FROM user;"
    )
    addingId = cursor.fetchall()[0][0]
    api.logger.info('IDsrc: %s ', addingId)
    addingId = addingId+1
    cursor.close()
    api.logger.info('newId: %s ', addingId)

    # 4. regist (inserting user info to db)
    cursor = connection.cursor()
    timestmp = time.strftime("%Y-%m-%d %H:%M:%S")
    api.logger.info('timestamp: %s ', timestmp)
    cursor.execute(
            "INSERT INTO user(" +
                "user_id," +
                "email," +
                "password," +
                "sns_twitter," +
                "sns_facebook," +
                "sns_github," +
                "created_at" +
            ") VALUE(" +
              "'" + str(addingId) + "', " +
              "'" + email + "', " +
              "'" + password + "', " +
              "'" + twitter + "', " +
              "'" + facebook + "', " +
              "'" + github + "', "+
              "'" + timestmp + "');")
    cursor.close()

    # 5. commit user info
    connection.commit()
    connection.close()

    # 6. return result
    session['userId'] = addingId
    return redirect(baseurl+'/qr_list',code=307)


# --------------------------------------------------
# /login
#
# > login
# --------------------------------------------------
@api.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # login process
    # 1. get form data
    email = request.form['email']
    password = request.form['pass']
    # 2. connect sql
    connection = MySQLdb.connect(
        host = 'localhost',
        user = 'hacku',
        password = 'hacku',
        db = 'hacku')
    cursor = connection.cursor()

    # 3. search account
    cursor.execute("SELECT user_id FROM user WHERE email='" + email + "' and password='" +password+"';" )

    # 4. clear objects
    connection.commit()
    connection.close()

    result = cursor.fetchall()
    log_info(str(result))
#    cnt = len(list(result))

    # 5. ログイン可否判定
    if len(result) > 0:
        # 6. add session & redirect main_pagei
        session['userId'] = result[0][0]
        return redirect(baseurl+'/qr_list', code=307)
    else:
        # 6-2. show login with message
        ### TODO: show message
        return render_template('login.html')


# --------------------------------------------------
# /qr_list
#
# > [PAGE] Show QRLIST Page
# --------------------------------------------------
@api.route('/qr_list', methods=['POST','GET'])
def showQrList():
    # 1. check logged in.
    if session.get('userId') != None:
        # 2. connect db
        connection = MySQLdb.connect(
            host = 'localhost',
            user = 'hacku',
            password = 'hacku',
            db = 'hacku')
        cursor = connection.cursor()

        # 3. search qr of thems.
        cursor.execute("SELECT * FROM qr WHERE user_id='" + str(session['userId']) + "';" )
        result = cursor.fetchall()

        # 4. create HTML For List
        insertList = ""
        for item in result:
            insertList = insertList + "<tr>\n" + "  <th>" + str(item[0]) + "</th>\n" + "  <td>" + item[2] + "</td>\n" + "  <td>" + "{0:%Y-%m-%d %H:%M:%S}".format(item[5]) + "</td>\n" + "  <td>" + "<img src='http://airmark.kaniyama.net:37564/qr_img/" + str(item[0]) + "' style='width:100px;'/>" + "</td>\n" + "  <td>" + "<a href='http://airmark.kaniyama.net:37564/qr_edit/" + str(item[0]) + "'>Edit</a>" + "</td>\n" + "</tr>\n"
        return render_template('qr_list.html',qrlist_html=insertList)
    else:
        return render_template('index.html')

# --------------------------------------------------
# /qr/<ID>
#
# [RESOURCE]
# --------------------------------------------------
@api.route('/qr_img/<int:qrId>')
def showQrImage(qrId):
    log_info(str(qrId))
    return send_from_directory('data/qr/', str(qrId)+".png", as_attachment=True)  


@api.route('/qr_reg', methods=['POST','GET'])
def registQrCode():
    if request.method == 'GET':
        return render_template('qr_reg.html',post_to="./qr_reg",file_visible="visible",submit_text="Regist",delete_visible="hidden")

    qr_title = request.form['qr_title']
    qr_file = request.files['qr_file']
    qr_header_name = request.form['qr_header_name']
    qr_header_description = request.form['qr_header_description']

    connection = MySQLdb.connect(
            host= 'localhost',
            user= 'hacku',
            password= 'hacku',
            db= 'hacku')
    cursor = connection.cursor()

    # 3. generate user ID
    cursor.execute(
        "SELECT MAX(qr_id) FROM qr;"
    )
    addingId = cursor.fetchall()[0][0]
    api.logger.info('IDsrc: %s ', addingId)
    addingId = addingId+1
    cursor.close()
    api.logger.info('newId: %s ', addingId)

    # 4. generate QR Code
    qr = qrcode.QRCode()
    qr.add_data('http://airmark.kaniyama.net:37564/qr/'+str(addingId))
    qr.make()
    img = qr.make_image(fill_color=request.form['qr_color'])
    img.save('data/qr/'+str(addingId)+'.png')

    # . Save Object Data
    qr_file.save('/home/hsui2x/data/tmp/old_obj/'+str(addingId)+'.fbx')

    # 5. convert 3D Object
    convert3DFileToSfb(addingId)

    # 6. insert QR Data to db of qr
    # 4. regist (inserting user info to db)                                                                 
    cursor = connection.cursor()                                                                            
    timestmp = time.strftime("%Y-%m-%d %H:%M:%S")                                                           
    api.logger.info('timestamp: %s ', timestmp)                                                             
    cursor.execute(                                                                                         
            "INSERT INTO qr(" +                                                                           
                "qr_id," +                                                                                
                "user_id," +                                                                                  
                "fname," +
                "qr_name,"+
                "qr_desc,"+
                "created_at" +                                                                             
            ") VALUE(" +                                                                                    
              "'" + str(addingId) + "', " +                                                                 
              "'" + str(session['userId']) + "', " +                                                                         
              "'" + qr_title + "', " +
              "'" + qr_header_name + "', " +
              "'" + qr_header_description + "', " +
              "'" + timestmp + "');")                                                                       
    cursor.close()                                                                                          
                                                                                                            
    # 5. commit user info                                                                                   
    connection.commit()                                                                                     
    connection.close()                                                                                      
                                                                                                            
    # 6. return result                                                                                      
    return redirect(baseurl+'/qr_list',code=307)


@api.route('/qr_edit/<int:qrId>',methods=['POST','GET'])
def editQR(qrId):
    if request.method == 'GET':
        connection = MySQLdb.connect(
            host = 'localhost',
            user = 'hacku',
            password = 'hacku',
            db = 'hacku'
            )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM qr WHERE qr_id='"+str(qrId)+"' ;")
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template(
                'qr_reg.html',
                post_to="http://airmark.kaniyama.net:37564/qr_edit/"+str(qrId),
                name_value=result[0][3],
                title_value=result[0][2],
                desc_value=result[0][4],
                file_visible="hidden",
                submit_text="Modify",
                delete_visible="show")

    if request.form['submit_button'] == "Modify":
        qr_title = request.form['qr_title']
        qr_file = request.files['qr_file']
        qr_header_name = request.form['qr_header_name']
        qr_header_description = request.form['qr_header_description']

        connection = MySQLdb.connect(
            host = 'localhost',
            user = 'hacku',
            password = 'hacku',
            db = 'hacku'
            )

        log_info("UPDATE qr "+
            "SET qr_name='"+ qr_header_name + "', " +
            "qr_desc='" + qr_header_description + "', " +
            "fname='" + qr_title + "'" +
            " WHERE qr_id="+str(qrId)+";")
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE qr "+
            "SET qr_name='"+ qr_header_name + "', " + 
            "qr_desc='" + qr_header_description + "', " +
            "fname='" + qr_title + "'" +
            " WHERE qr_id="+str(qrId)+";")
        connection.commit()
        result = cursor.fetchall()
        cursor.close()
        connection.close()
    else:
        connection = MySQLdb.connect(
            host = 'localhost',
            user = 'hacku',
            password = 'hacku',
            db = 'hacku'
            )
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM qr WHERE qr_id='"+str(qrId)+"';")
        connection.commit()
        result = cursor.fetchall()
        cursor.close()
        connection.close()
    return redirect(baseurl+'/qr_list',code=307)


@api.route('/profile', methods=['POST','GET'])
def showUserInfo():
    connection = MySQLdb.connect(
            host = 'localhost',
            user = 'hacku',
            password = 'hacku',
            db = 'hacku'
            )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM user WHERE user_id='"+str(session['userId'])+"';")
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('user.html',
            userid=result[0][0],
            email=result[0][1],
            twitter=result[0][3],
            facebook=result[0][4],
            github=result[0][5],
            createdDate="{0:%Y-%m-%d %H:%M:%S}".format(result[0][6]))

# ログアウト API
@api.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    return redirect('http://airmark.kaniyama.net:37564/')


@api.route('/qr/<int:qrId>', methods=['POST','GET'])
def qrOverviewWindow(qrId):
    if request.method == 'GET':
        return redirect('./index')
    connection = MySQLdb.connect(
            host = 'localhost',
            user = 'hacku',
            password = 'hacku',
            db = 'hacku'
            )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM qr WHERE qr_id='"+str(qrId)+"';")
    qrresult = cursor.fetchall()[0]
    cursor.close()

    cursor = connection.cursor()
    cursor.execute("SELECT sns_twitter,sns_facebook,sns_github FROM user WHERE user_id='"+str(qrresult[1])+"';")
    userresult = cursor.fetchall()[0]
    log_info(str(userresult))
    cursor.close()
    connection.close()

    return jsonify({
        "name":qrresult[3],
        "desc":qrresult[4],
        "sns_twitter":userresult[0],
        "sns_facebook":userresult[1],
        "sns_github":userresult[2],
        "3DObjURL":"http://airmark.kaniyama.net:37564/obj/"+str(qrresult[0])
        })


@api.route('/obj/<int:qrId>',methods=['POST'])
def getObj(qrId):
    return send_from_directory('data/obj/', str(qrId)+".sfb", as_attachment=True)


# QR 登録処理
@api.route('/genqr', methods=['POST'])
def genqr():
    email = request.form['email']
    qrname = request.form['qrname']
    
    # SQL 実行
    connection = MySQLdb.connect(
        host = 'localhost',
        user = 'hacku',
        password = 'hacku',
        db = 'hacku')
    cursor = coonection.cursor()

    cursor.execute("INSERT INTO hacku.user VALUE")

    connection.commit()
    connection.close()

    # 実行結果処理

# QR 一覧表示
@api.route('/listqr', methods=['POST'])
def listqr():
    email = request.form['email']
    
    # SQL 実行
    connection = MySQLdb.connect(
        host = 'localhost',
        user = 'hacku',
        password = 'hacku',
        db = 'hacku')
    cursor = coonection.cursor()

    cursor.execute("INSERT INTO hacku.user VALUE")

    connection.commit()
    connection.close()

    return cursor

# 登録成功時の処理
@api.route('/regist_success', methods=['POST'])
def regist_success():
    pass
    # メール送信等

def convert3DFileToSfb(qrId):
    outputFolder = '/home/hsui2x/data/obj/'
    filePath = '/home/hsui2x/data/tmp/old_obj/'+str(qrId)+'.fbx'
    result=subprocess.check_output(["/home/hsui2x/public_html/google-ar-asset-converter/sceneform_sdk/linux/converter","-a","-d","--mat","/home/hsui2x/public_html/google-ar-asset-converter/sceneform_sdk/default_materials/fbx_material.sfm","--outdir" , outputFolder , filePath])
    print(result)
    outputObjPath = outputFolder + filePath[(filePath.rfind('/')):(filePath.rfind('.'))] + ".sfb"
    print(outputObjPath)
    return outputObjPath

def log_info(message):
    api.logger.info(message)

# 37564番ポートでWebサーバを起動する
if __name__ == '__main__':
    api.run(host='0.0.0.0', port=37564, debug=True)
