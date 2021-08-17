from flask import Flask, render_template, request, redirect, url_for, session, send_file, Response
from forms import *
import Member_Completion, GenerateOrderNum, random, logging
from flask_mysqldb import MySQL
import MySQLdb.cursors
import datetime
# import socket
from flask_mail import Mail, Message    # To Send Email
import os
from twilio.rest import Client  # To Send SMS
import bcrypt   # For Hashing

import os.path
import pathlib
import json
import google.auth.transport.requests
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol

# Ernest Audit
import csv
from handler import error   # pip install handler
# from functools import wraps # don't need to pip install
# import splunklib.client as client # pip install splunk-sdk

# Joel File Encryption
# import rsa (SQL cnnt store rsa format)
from cryptography.fernet import Fernet
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import PyPDF2
from zipfile import ZipFile
import requests
import pyminizip
import io


# Akif's Google Login
def get_user_email(access_token):
    r = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            params={'access_token': access_token})
    return r.json()

# Zhi Yang Watchdog/Backup
import time
from watchdog.observers import Observer
import file_monitoring as wd
import backup_and_restore as br
import pickle
from googleapiclient.errors import HttpError


app = Flask(__name__)
# For Session
app.secret_key = 'Secret'

# For SQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # Enter Your Own SQL Information
app.config['MYSQL_DB'] = 'piquant'  # Load Up piquant schema
mysql = MySQL(app)

# For Captcha
app.config['SECRET_KEY'] = 'Thisisasecret!'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Ld8DSsbAAAAAKwzOf-7wqEtMrn4s-wzWGId70tk'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Ld8DSsbAAAAAGaCbG6u8jdfT1BIHCm3HHN_X2vV'
app.config['TESTING'] = False

# To Send Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# To Send SMS
# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = ''
auth_token = ''
twilioclient = Client(account_sid, auth_token)


# To Upload Files
# app.config['UPLOAD_EXTENSIONS'] = ['.jpg']
app.config['UPLOAD_FOLDER'] = 'static/accountsecpic'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 4MB max-limit.

# Ernest Loggers
app.register_blueprint(error)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(pathname)s:%(name)s:%(message)s')
file_handler = logging.FileHandler('piquant.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

'''
#for splunk
service = client.connect(
    host='localhost',
    port=8089,
    username='admin',
    password='Iaminmumbai21!'
)
'''

# Akif Google Login
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = "743542317835-ohu4pjoo7ajuhcda7genrnjd3k06cttq.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email","openid"],
    redirect_uri="http://127.0.0.1:5000/googlelogincallback"
)

# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return os.abort(401)  # Authorization required
        else:
            return function()

    return wrapper

# Role-Based Access Control
# only manager can update and delete user
# staff could only retrieve reservation and update their own profile
'''
def man(manager):
    @wraps(manager)
    def wrap(*args, **kwargs):
        if 'loggedIn' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM account WHERE manager_id IS NOT NULL')
            account = cursor.fetchone()
            if account:
                session['loggedIn'] = True
                session['manager_id'] = account['manager_id']
                session['stafflogged'] = account['full_name']
                if account['manager_id']:
                    return manager(*args, **kwargs)
                else:
                    return render_template('error.html')
    return wrap

def role(staff):
    @wraps(staff)
    def wrap(*args, **kwargs):
        if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM account WHERE staff_id IS NOT NULL')
            account = cursor.fetchone()
            if account:
                session['loggedIn'] = True
                session['staff_id'] = account['staff_id']
                session['stafflogged'] = account['full_name']
                if account['staff_id']:
                    return staff(*args, **kwargs)
                else:
                    return render_template('error.html')
    return wrap

def mem(member):
    @wraps(member)
    def wrap(*args, **kwargs):
        if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM account WHERE email IS NOT NULL')
            account = cursor.fetchone()
            if account:
                session['loggedin'] = True
                session['email'] = account['email']
                if account['email']:
                    return member(email, *args, **kwargs)
                else:
                    return render_template('500.html')
    return wrap
'''

#Email To Be Passed into codes to check wether users are login or not
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Joel New
@app.route('/download_reciept')
def download_reciept():
    path = "ProtectedReceipt.zip"
    return send_file(path, as_attachment=True)
def upload_form():
    return render_template('download.html')


# Customer Pages
@app.route('/Reservation', methods=['GET','POST'])
def create_user():
    try:
        session['email']
    except:
        return redirect(url_for('member_login'))
    create_user_form = ReservationForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE email = %s', [session['email']])       # Look For Account Information
    account = cursor.fetchone()
    if request.method == 'POST':
        # add in update user action here
        # Joel New
        symmetrickey = Fernet.generate_key() # Generate symetric key
        f = Fernet(symmetrickey) # Load key to crypto API

        cns = str(create_user_form.cn.data)
        cvvs = str(create_user_form.cvv.data)

        encryptcreditcard = f.encrypt(cns.encode())
        encryptcvv = f.encrypt(cvvs.encode())

        useremail = create_user_form.email.data.lower()
        selfie = request.files[create_user_form.selfie.name].read()  # Get Image 1 In Pure Data Format
        filename = str(useremail).replace('@', '') + "_mempic" + '1' + ".jpg"
        open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename)), 'wb').write(selfie)  # Save The Picture 1 That Is Uploaded By The User

        rdate = create_user_form.date.data
        rfullname = create_user_form.full_name.data
        rtime = create_user_form.time.data
        rphone = create_user_form.phone_number.data
        newemail = create_user_form.email.data.lower()
        password = rphone + newemail    # Password for Zip (Phone + Email)

        # PDF
        DATA = [
            ["Date", "Full name", "Time", "Phone Number"],
            [rdate, rfullname, rtime, rphone],
        ]
        pdf = SimpleDocTemplate("PReceipt.pdf", pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        title_style.alignment = 1
        title = Paragraph("PIQUANT", title_style)
        style = TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("GRID", (0, 0), (4, 4), 1, colors.black),
                ("BACKGROUND", (0, 0), (3, 0), colors.white),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ]
        )
        table = Table(DATA, style=style)

        # For Locking PDF
        pdf.build([title, table])
        pdf_in_file = open("PReceipt.pdf", 'rb')    # Open Reciepts File that is not locked
        inputpdf = PyPDF2.PdfFileReader(pdf_in_file)    # Read content of PDF
        pages_no = inputpdf.numPages    # Find number of pages
        for i in range(pages_no):
            inputpdf = PyPDF2.PdfFileReader(pdf_in_file)
            output = PyPDF2.PdfFileWriter()
            output.addPage(inputpdf.getPage(i))
            output.encrypt(password)    # Lock File With Password

            with open("PReceiptProtected.pdf", "wb") as outputStream:
                output.write(outputStream)

        # Zip File with Password
        inpt = "PReceiptProtected.pdf"

        # output zip file path
        oupt = "ProtectedReceipt.zip"

        # compress level
        com_lvl = 5

        # Password for Zip
        zippassword = rphone + str(rdate)

        # compressing file
        pyminizip.compress(inpt, None, oupt,zippassword, com_lvl)

        # Scan Photo Uploaded for Virus
        endpoint = "https://api.virusscannerapi.com/virusscan"
        picfilename = 'static/accountsecpic/' + str(useremail).replace('@', '') + "_mempic" + '1' + ".jpg"
        headers2 = {
            'X-ApplicationID': 'e725e24f-6c29-4c01-93a9-6f4b0c1ed03d',
            'X-SecretKey': 'b50a1340-ad8e-4af9-93e4-38f78341e5ea'
        }
        file2 = open(picfilename, "rb")
        data2 = {
            'async': 'false',
        }
        files2 = {
            'inputFile': (picfilename, file2.read())
        }
        r = requests.post(url=endpoint, data=data2, headers=headers2, files=files2)
        response = r.text
        print(response)

        cursor.execute('INSERT INTO reservation VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (create_user_form.full_name.data, useremail, create_user_form.phone_number.data, create_user_form.date.data, str(create_user_form.time.data + ':00'), create_user_form.card_name.data, encryptcreditcard, str(create_user_form.expire.data + '-01'), encryptcvv, create_user_form.Additional_note.data, symmetrickey))
        mysql.connection.commit()   #Update SQL Database
        logger.info('{} has made a reservation'.format(create_user_form.full_name.data))
        return redirect(url_for('retrieve_users'))

    if account != None:     # Pre Fill Form if user is logged in
        create_user_form.full_name.data = account['full_name']
        create_user_form.email.data = account['email']
        create_user_form.phone_number.data = account['phone_num']
    return render_template('Reservation.html', form=create_user_form)


@app.route('/Confirmation')
def retrieve_users():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation')
    users_list = cursor.fetchall()  # Get everything in reservation
    getuser = users_list[-1]    # Get Most Recent Record Only
    return render_template('Reservation_Confirmation.html', count=len(users_list), get_user=getuser)


@app.route('/thanks')
def number():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation')
    users_list = cursor.fetchall()
    reservationid = users_list[-1].get('reservation_id')
    return render_template('Reservation_thanks.html', reservationid=reservationid)


# Online Menu/Cart
@app.route('/onlineorder')
def orderpage1():
    try:
        session['email']
    except:
        return redirect(url_for('member_login'))
    try:
        session['tablealloc']
    except:
         session['tablealloc'] = True
         session['tablenum'] = 1
    try:
        session['onlineorder']
        session['ordersess']
    except:
        session['onlineorder'] = True
        now = datetime.datetime.now()
        curtime = now.strftime("%H_%M_%S")
        session['ordersess'] = str(session['tablenum']) + '_' + curtime
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM menu')
    allitem = cursor.fetchall()
    return render_template('Menu_OrderPage.html', allitem=allitem)


@app.route('/addingorder/<orderitem>')
def addingorder(orderitem):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    newordernum = session['ordersess'] + '_' + str(GenerateOrderNum.generateordernum()) # Generate A Random Order Number To Store
    cursor.execute('INSERT INTO cart VALUES (%s, %s, %s, %s, %s)', [newordernum, str(session['tablenum']), email, orderitem, 'Pending'])
    mysql.connection.commit()
     # add in update user action here
    # put mysql.connection.commit here
    logger.info('{} added {} to cart'.format(session['email'], orderitem))
    return redirect(url_for('orderpage1'))



@app.route('/cart')
def cart():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    total = 0
    cursor.execute('SELECT * FROM menu')
    iteminfo = cursor.fetchall()    # Get Everything From menu table
    # Get Order From Session (Current Cart)
    currentsession = '%' + session['ordersess'] + '%'
    cursor.execute('SELECT order_num, item_code, count(*) quantity FROM cart WHERE order_num LIKE %s GROUP BY item_code', [currentsession])
    order_list = cursor.fetchall()
    # Get Order From Previous Session (Past Order)
    cursor.execute('SELECT item_code, count(*) quantity FROM cart WHERE table_num = %s AND order_num NOT LIKE %s GROUP BY item_code', [session['tablenum'], currentsession])
    oldorder_list = cursor.fetchall()
    # Fetch All Order From This Table
    cursor.execute('SELECT item_code, count(*) quantity FROM cart WHERE table_num = %s GROUP BY item_code', [session['tablenum']])
    allorder_list = cursor.fetchall()
    # To Find Total Price
    for a in allorder_list: # Loop Through Cart
        for b in iteminfo:  # Loop Thorugh Menu To Find Item Info (Must Use Loop as it is a tuple)
            if b['item_code'] == a['item_code']:    # if Item Code from cart matches the one in menu, Item Info Is Found
                total += (int(b['item_price']) * a['quantity'])     # Calculate Total
    # add in update user action here
    # put mysql.connection.commit here
    logger.info('{} viewed cart items'.format(session['email']))
    return render_template('Menu_Cartpage.html', order_list=order_list, oldorder_list=oldorder_list, iteminfo=iteminfo, total=total)


@app.route('/deleteitem/<ordernum>')
def deleteitem(ordernum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM cart WHERE order_num = %s', [ordernum])
    mysql.connection.commit()
    # add in update user action here
    # put mysql.connection.commit here
    logger.info('{} deleted order item'.format(session['email']))
    return redirect(url_for('cart'))

@app.route('/submit')
def submit():
    session.pop('onlineorder', None)
    session.pop('ordersess', None)
    return render_template('Menu_Submit.html')


# Create User
@app.route('/createMember', methods=['GET', 'POST'])
def create_Member():
    msg = ''
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        signupdate = datetime.datetime.today()   # Get Today's date
        newdate = signupdate.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
        login_time = datetime.datetime.now().replace(microsecond=0)
        date_time = datetime.datetime(2021, 12, 31)
        expiry_date = signupdate + datetime.timedelta(days=90)
        pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        useremail = create_user_form.email.data.lower()
        cursor.execute('SELECT * FROM account WHERE email = %s or phone_num = %s', (useremail, create_user_form.phone_number.data))
        account = cursor.fetchone()
        if account:     # Ensure That there will be no duplicates (As Email is A Primary Key In The Database)
            msg = 'This Email/Phone Number Has Been Taken'
        else:

            # Password Hashing
            # Create a random number (Salt)
            salt = bcrypt.gensalt(rounds=16)
            # A hashed value is created with hashpw() function, which takes the cleartext value and a salt as parameters.
            hash_password = bcrypt.hashpw(create_user_form.password.data.encode(), salt)
            cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL, NULL, %s, NULL)', (useremail, create_user_form.full_name.data, hash_password, pwd_expiry, 'Member',  create_user_form.phone_number.data , "Regular", "1/5", newdate, 'unVerified'))
            cursor.execute('INSERT INTO audit VALUES (%s, %s, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)', (useremail, create_user_form.full_name.data))
            cursor.execute('UPDATE audit SET action = %s WHERE email = %s', ('Signed up as member', create_user_form.email.data,))
            logger.info('{} signed up as member'.format(create_user_form.full_name.data))
            # Store in Password History
            cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (useremail, hash_password))
            mysql.connection.commit()
            # Kick Session When Creating Account With Google
            try:
                if session['creategoogle'] == True:
                    session.pop('creategoogle', None)
                    session.pop('creategooglename', None)
                    session.pop('creategoogleemail', None)
            except:
                pass
            session['authemail'] = useremail     # For Authentication, Put User Email In Session
            session['authphone'] = create_user_form.phone_number.data   # For Authentication, Put Phone Number In Session
            session['authreason'] = 'registering'   # For Authentication, Set Reason to Registering
            return redirect(url_for('authenticate_account'))
    else:
        try:
            if session['creategoogle'] == True: # Pre Fill Form if user is logged in
                create_user_form.full_name.data = session['creategooglename']
                create_user_form.email.data = session['creategoogleemail']
        except:
            pass
    return render_template('Member_createUser.html', form=create_user_form, msg=msg)


# Login
@app.route('/Memberlogin', methods=['GET', 'POST'])
def member_login():
    # Log Out Everybody
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('stafflogged', None)
    session.pop('staff_id', None)
    session.pop('manager_id', None)
    # Timeout (Auto Logout, in non-incognito)
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)
    # New
    msg = ''
    # Check If There's A Login Attempt Session In Place
    try:
        # At 3 Attempt
        if session['loginattempt'] == 3:
            try:
                session['blktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            session['blktime'] = session['blktime'].replace(tzinfo=None)
            timeremain = str(session['blktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = session['loginattempt'] + 1   # To Unblock User
            else:
                msg = 'You account has been locked. You can try again after ' + timeremain
        # At 7 Attempt ( Have To Put 11 As Session Will +1 To Unblock User Earlier On)
        elif session['loginattempt'] >= 7:
            try:
                session['blktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=2)    # Block For 2 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            session['blktime'] = session['blktime'].replace(tzinfo=None)
            timeremain = str(session['blktime'] - datetime.datetime.now())   # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = 0  # To Unblock User
            else:
                msg = 'You account has been locked. You can try again after ' + timeremain
    except:
        session['loginattempt'] = 0

    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate() and session['loginattempt'] != 3 and session['loginattempt'] < 7:
        useremail = check_user_form.email.data.lower()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s ', (useremail,))
        account = cursor.fetchone()
        if account:     # If Account Exist In DataBase
            if account['account_status'] == "Blocked":
                msg = 'This Account Has Been Locked, Please Reset Your Password To Unlock Your Account'
            elif bcrypt.checkpw(check_user_form.password.data.encode(), account['password'].encode()):      # Check If Password Entered By User Is The Same As The One In The Database
                session.pop('loginattempt', None)

                # Check if account is verified or not
                if account['account_status'] == "unVerified":
                    session['authemail'] = account['email']     # For Authentication, Put User Email In Session
                    session['authphone'] = account['phone_num']    # For Authentication, Put Phone Number In Session
                    session['authreason'] = 'registering'   # For Authentication, Set Reason to Registering
                    return redirect(url_for('authenticate_account'))
                # For users With 2FA
                elif account['2fa_status'] == "Yes":
                    session['authemail'] = account['email']      # For Authentication, Put User Email In Session
                    session['authphone'] = account['phone_num']  # For Authentication, Put Phone Number In Session
                    session['authreason'] = 'login'    # For Authentication, Set Reason to Login
                    return redirect(url_for('authenticate_account'))
                # To Force User To Change Password
                elif account['pwd_expiry'] <= datetime.datetime.today().date():       # Compare Password Expiry Date To Current Date
                    session['acctrecoveremail'] = account['email']
                    return redirect(url_for('Change_Acct_Password'))   # Redirect to Password Change Page
                else:
                    session['loggedin'] = True
                    session['email'] = account['email']
                    now = str(datetime.datetime.now().replace(microsecond=0))
                    cursor.execute('UPDATE audit SET login_time = %s, action= %s WHERE email=%s', (now,'Logged in', session['email']))
                    logger.info('{} is logged in'.format(session['email']))
                    # Timeout (Auto Logout, in non-incognito)
                    session.permanent = True
                    app.permanent_session_lifetime = datetime.timedelta(minutes=1)
                    return redirect(url_for('referral', referral_state=" "))
            else:
                # Write to audit SQL Table
                cursor.execute('UPDATE audit SET failed_login = %s WHERE email = %s', (session['loginattempt'], useremail,))
                msg = "Incorrect Username/Password"     # Return Incorrect Username/Password as a message
        else:
            msg = "Incorrect Username/Password"     # Return Incorrect Username/Password as a message
        session['loginattempt'] = session['loginattempt'] + 1   # Increase Login Attempt By One
        if session['loginattempt'] == 11:    # If Login Attempt Reached 10, Account Will Be Locked [Needs to be equal to 11 as the system will add 1 attempt to allow user to try after the initial 3 failed attempt]
            cursor.execute('UPDATE account SET account_status = %s WHERE email = %s', ("Blocked", useremail,))     # Set Account Status To Blocked In SQL
            mysql.connection.commit()
    return render_template('Member_login.html', form=check_user_form, msg=msg)


# Akif New Feature (Google Login)
# Google Login
@app.route("/googlelogin")
def google_login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/googlelogincallback")
def googlelogin_callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        os.abort(500)  # state does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE email = %s', (id_info.get("email"),))
    account = cursor.fetchone()
    if account:
        # For Users With Account that is not verified
        if account['account_status'] == "unVerified":
            session['authemail'] = account['email']     # For Authentication, Put User Email In Session
            session['authphone'] = account['phone_num']    # For Authentication, Put Phone Number In Session
            session['authreason'] = 'registering'   # For Authentication, Set Reason to Registering
            return redirect(url_for('authenticate_account'))
        # For users With 2FA
        elif account['2fa_status'] == "Yes":
            session['authemail'] = account['email']      # For Authentication, Put User Email In Session
            session['authphone'] = account['phone_num']  # For Authentication, Put Phone Number In Session
            session['authreason'] = 'login'    # For Authentication, Set Reason to Login
            return redirect(url_for('authenticate_account'))
        # For Users With No 2FA
        else:
            # Timeout (Auto Logout, in non-incognito)
            session.permanent = True
            app.permanent_session_lifetime = datetime.timedelta(minutes=1)
            session["loggedin"] = True
            session['email'] = id_info.get("email")
            # For Audit
            now = str(datetime.datetime.now().replace(microsecond=0))
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE audit SET login_time = %s, action= %s WHERE email=%s', (now,'Logged in', session['email']))
            logger.info('{} is logged in'.format(session['email']))
            mysql.connection.commit()
            return redirect(url_for('referral', referral_state=" "))
    else:
        session['creategoogle'] = True
        session['creategoogleemail'] = id_info.get("email")
        session['creategooglename'] = id_info.get("name")
        return redirect(url_for('create_Member'))


# Referral
@app.route('/referral/<referral_state>', methods=['GET', 'POST'])
def referral(referral_state):
    try:
        session['email']
    except:
        return redirect(url_for('member_login'))
    claim_form = ClaimCode(request.form)
    # For Show Completion Part
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE email = %s', (session['email'],))        # From Pratical wk 4 line 101, To Change To Session
    account = cursor.fetchone()

    #For Claiming Codes
    if request.method == 'POST' and claim_form.validate():
        check = ''
        cursor.execute('SELECT * FROM rewards ')
        code_list = cursor.fetchall()       # Get all Codes From Database
        for a in code_list:
            if a['reward_code'] == claim_form.claim_code.data:
                if a['status'] == "Claimed":       # Check Status
                     check = "used"     # Return Variable To Let Webpage Know That The Code is Used
                else:
                    check = "claim"
                    cursor.execute('UPDATE rewards SET status = %s WHERE reward_code = %s', ('Claimed', a['reward_code']))  # Update Status To Update
                    mysql.connection.commit()

        if check == "used":     #Shows if code has been claimed before
            cursor.execute('UPDATE audit SET action = %s', ('Used referral code',))
            logger.info('{} used referral code {}'.format(email, claim_form.claim_code.data))
            mysql.connection.commit()
            return redirect(url_for('referral', referral_state="used"))
        elif check == "claim":
            newreward = Member_Completion.increase_completion(account['member_level'], account['member_completion'])     # Increase Completion Using Function
            cursor.execute('UPDATE account SET member_level = %s, member_completion = %s WHERE email = %s', (newreward[0], newreward[1], session['email'],))
            cursor.execute('UPDATE audit SET action = %s WHERE email=%s', ('Claimed referral code', email,))
            logger.info('{} claimed referral code {}'.format(email, claim_form.claim_code.data))
            mysql.connection.commit()
            return redirect(url_for('referral', referral_state="claim"))
        else:
            return redirect(url_for('referral', referral_state="unclaimed"))

    return render_template('Member_referral.html', form=claim_form, user=account, referral_state=referral_state)

# Updating Details Success Only
@app.route('/acctupdateinfosuccess')
def acct_updateinfosuccess():
    return render_template('Account_Selfupdateinfosuccess.html')

# Update Password Success
@app.route('/acctupdatesuccess')
def acct_updatesuccess():
    logout()
    return render_template('Account_Selfupdateinfosuccess.html')

@app.route('/logout')   # Universal Logout Function
def logout():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    logouttime = str(datetime.datetime.now().replace(microsecond=0))
    # For Audit
    if 'email' in session:  # To record if member is logout
        logger.info("{} is logged out".format(session['email']))
        cursor.execute('UPDATE audit SET action = %s, logout_time = %s WHERE email = %s ', ('Logged out', logouttime, session['email'],))
    if 'staff_id' in session:   # To record if staff Logout
        logger.info("{} is logged out".format(session['staff_id']))
        cursor.execute('UPDATE audit SET action = %s, logout_time = %s WHERE staff_id = %s ', ('Logged out', logouttime, session['staff_id'],))
    mysql.connection.commit()
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('stafflogged', None)
    session.pop('staff_id', None)
    session.pop('manager_id', None)
    return redirect(url_for('home'))


#Update Member (For Customers)
@app.route('/updateMember', methods=['GET', 'POST'])
def update_member():
    update_user_form = UpdatememberdetailForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        useremail = update_user_form.email.data.lower()
        cursor.execute('SELECT * FROM account WHERE email = %s', (useremail,))
        account = cursor.fetchone()     # Fetch Only 1 SQL Record (Since Email Is A Primary Key, There Should Be Only 1 Record)
        if session['email'] != account['email']:   # Check Wether Database has this email or not
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s WHERE email = %s', (useremail, update_user_form.full_name.data, update_user_form.phone_number.data, session['email'],))
            cursor.execute('UPDATE audit SET action = %s WHERE email=%s', ('Updated self profile', email))
            logger.info('{} updated self profile'.format(email))
            mysql.connection.commit()
            return redirect(url_for('acct_updateinfosuccess'))
    else:   # Pre Fill Information in the form
        cursor.execute('SELECT * FROM account WHERE email = %s', (session['email'],))
        account = cursor.fetchone()
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
    return render_template('Member_updateself.html', form=update_user_form, msg=msg)


@app.route('/updateMemberpass', methods=['GET', 'POST'])
def update_memberpass():
    update_user_form = ChangePasswordForm(request.form)
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s', (session['email'],))
        account = cursor.fetchone()

        # Password Hashing (New Password Entered)
        # Create a random number (Salt)
        salt = bcrypt.gensalt(rounds=16)
        # A hashed value is created with hashpw() function, which takes the cleartext value and a salt as parameters.
        newhash_password = bcrypt.hashpw(update_user_form.newpassword.data.encode(), salt)

        if bcrypt.checkpw(update_user_form.oldpassword.data.encode(), account['password'].encode()):   # Check If Old Password Entered Is The Same One Entered By The User
            cursor.execute('SELECT * FROM password_hist WHERE email = %s', (session['email'],))
            pwdhist = cursor.fetchall()
            if pwdhist:
                state = ''
                if bcrypt.checkpw(update_user_form.newpassword.data.encode(), pwdhist[0].get('password').encode()):
                    msg = ' This Password Has Been Used'
                    state = "used"
                if state != 'used':
                    if len(pwdhist) >= 2:
                        firstocc = pwdhist[0].get('serial_no')
                        cursor.execute('DELETE FROM password_hist WHERE serial_no = %s', [firstocc])
                        mysql.connection.commit()
                    curdate = datetime.date.today()   # Get Today's date
                    expiry_date = curdate + datetime.timedelta(days=90)
                    pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
                    # Store Password
                    cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (session['email'], newhash_password))
                    cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s WHERE email = %s', (newhash_password, pwd_expiry, session['email'],))   # Update SQL To New Password That User Entered
                    cursor.execute('UPDATE audit SET action = %s WHERE email=%s', ('Updated password', session['email'],))
                    logger.info("{} updated password".format(session['email']))
                    mysql.connection.commit()
                    logout()
                    return redirect(url_for('acct_updatesuccess'))
            else:
                curdate = datetime.date.today()   # Get Today's date
                expiry_date = curdate + datetime.timedelta(days=90)
                pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
                # Store Password
                cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (session['email'], update_user_form.newpassword.data))
                cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s WHERE email = %s', (update_user_form.newpassword.data, pwd_expiry, session['email'],))   # Update SQL To New Password That User Entered
                cursor.execute('UPDATE audit SET action = %s WHERE email=%s', ('Updated password', email,))
                logger.info("{} updated password".format(email))
                mysql.connection.commit()
                logout()
                return redirect(url_for('acct_updatesuccess'))
        else:
            msg = 'Incorrect Password'
    return render_template('Member_updateselfpass.html', form=update_user_form, email=email, msg=msg)


# Staff Pages
@app.route('/Stafflogin', methods=['GET','POST'])
def checkstaff():
    # Log Out Everybody
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('stafflogged', None)
    session.pop('staff_id', None)
    session.pop('manager_id', None)
    # Timeout (Auto Logout, in non-incognito)
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    msg = ' '
    # Check If There's A Login Attempt Session In Place
    try:
        # At 3 Attempt
        if session['loginattempt'] == 3:
            try:
                session['blktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            session['blktime'] = session['blktime'].replace(tzinfo=None)
            timeremain = str(session['blktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = session['loginattempt'] + 1   # To Unblock User
            else:
                msg = 'You account has been locked. You can try again after ' + timeremain
        # At 7 Attempt ( Have To Put 11 As Session Will +1 To Unblock User Earlier On)
        elif session['loginattempt'] >= 7:
            try:
                session['blktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=2)    # Block For 2 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            session['blktime'] = session['blktime'].replace(tzinfo=None)
            timeremain = str(session['blktime'] - datetime.datetime.now())   # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = 0  # To Unblock User
            else:
                msg = 'You account has been locked. You can try again after ' + timeremain
    except:
        session['loginattempt'] = 0

    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate() and session['loginattempt'] != 3 and session['loginattempt'] < 7:
        useremail = check_user_form.email.data.lower()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s ', (check_user_form.email.data,))
        account = cursor.fetchone()
        if account:
            if account['account_status'] == "Blocked":
                msg = 'This Account Has Been Locked, Please Reset Your Password To Unlock Your Account'
            elif account['staff_id'] == None:     # Only allow access if staff_id field in the account has information in it (If An Account is a member, The Staff_id field would not be filled up)
                msg = "Incorrect Username/Password"
            else:
                if bcrypt.checkpw(check_user_form.password.data.encode(), account['password'].encode()):
                    session.pop('loginattempt', None)   # Remove Login Attempt
                    # To Force User To Change Password
                    if account['pwd_expiry'] <= datetime.datetime.today().date():       # Compare Password Expiry Date To Current Date
                        session['acctrecoveremail'] = account['email']
                        return redirect(url_for('Change_Acct_Password'))   # Redirect to Password Change Page
                    # For users With 2FA
                    if account['2fa_status'] == "Yes":
                        session['authemail'] = account['email']      # For Authentication, Put User Email In Session
                        session['authphone'] = account['phone_num']  # For Authentication, Put Phone Number In Session
                        session['authreason'] = 'login'    # For Authentication, Set Reason to Login
                        return redirect(url_for('authenticate_account'))
                    else:
                        logintime = str(datetime.datetime.now().replace(microsecond=0))
                        session.pop('loginattempt', None)
                        session['stafflogged'] = account['full_name']  # Set Staff Login To True In Session
                        session['staff_id'] = account['staff_id']   # Put Staff Id in Session
                        logger.info("{} is logged in".format(account['staff_id']))
                        cursor.execute('UPDATE audit SET action = %s, login_time=%s, failed_login = %s WHERE email = %s', (['Logged in', logintime, 0, account['email'],]))
                        mysql.connection.commit()
                       # Timeout (Auto Logout, in non-incognito)
                        session.permanent = True
                        app.permanent_session_lifetime = datetime.timedelta(minutes=1)
                        if account['manager_id'] != None:
                            session['manager_id'] = account['manager_id']   # Put Manager Id in Session
                        return redirect(url_for('staffpage'))
                else:
                    # Write to audit
                    faillogincount = session['loginattempt'] + 1
                    cursor.execute('UPDATE audit SET failed_login = %s WHERE email = %s', ([faillogincount, useremail]))
                    mysql.connection.commit()
                    print(faillogincount)
                    msg = "Incorrect Username/Password"
        else:
            msg = "Incorrect Username/Password"
        session['loginattempt'] = session['loginattempt'] + 1   # Increase Login Attempt By One
        if session['loginattempt'] == 7:    # If Login Attempt Reached 7, Account Will Be Locked [Needs to be equal to 11 as the system will add 1 attempt to allow user to try after the initial 3 failed attempt]
            cursor.execute('UPDATE account SET account_status = %s WHERE email = %s', ("Blocked", useremail,))     # Set Account Status To Blocked In SQL
            mysql.connection.commit()

    return render_template('Staff_login.html', form=check_user_form, msg=msg)

@app.route('/Staffpage')
def staffpage():
    # Check If Staff (Not Manager) Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['staff_id']
    except:
        return redirect(url_for('checkstaff'))
    return render_template('Staff_Page.html')

# TBC
def manpage():
    # Check If Manager is Logged In
    try:
        session['manager_id']
    except:
        return redirect(url_for('checkstaff'))
    return render_template('Manager_Page.html')

# Reservation Form
@app.route('/retrieveReservation')
def retrieve_reserve():
    # Check If All Staff (includes managers) Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation')
    users_list = cursor.fetchall()     # Retrieve All Reservatio
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Retrieved reservation', session['staff_id']))
    logger.info("{} retrieved reservation".format(session['staff_id']))
    mysql.connection.commit()
    return render_template('Reservation_retrieveUser.html', count=len(users_list), users_list=users_list)


@app.route('/updateUser/<id>', methods=['GET', 'POST'])
def update_user(id):
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    update_user_form = RetriveReservationForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation WHERE reservation_id = %s', [id])       # Get Entire Row That Contains The Reservation ID
    account = cursor.fetchone()
    if request.method == 'POST' and update_user_form.validate():
        useremail = update_user_form.email.data.lower()
        symmetrickey = Fernet.generate_key() # Generate symetric key
        f = Fernet(symmetrickey) # Load key to crypto API

        cns = str(update_user_form.cn.data)
        cvvs = str(update_user_form.cvv.data)

        encryptcreditcard = f.encrypt(cns.encode())
        encryptcvv = f.encrypt(cvvs.encode())

        cursor.execute('UPDATE reservation SET full_name= %s, email = %s, phone_num= %s, reservation_date= %s, reservation_time= %s, card_name= %s, card_number= %s, expiry_date= %s, cvv= %s, additional_note= %s, encrypt_key = %s WHERE reservation_id = %s', (update_user_form.full_name.data, useremail, update_user_form.phone_number.data, update_user_form.date.data, update_user_form.time.data, update_user_form.card_name.data, encryptcreditcard ,str(update_user_form.expire.data + '-01'), encryptcvv, update_user_form.Additional_note.data, symmetrickey, id))
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Updated reservation', session['staff_id'],))
        logger.info("{} updated reservation".format(session['staff_id']))
        mysql.connection.commit()
        return redirect(url_for('retrieve'))
    else:   # Pre Fill Form
        # Decrypt Credit Card Number and CVV
        symmetrickey = account['encrypt_key'] # Generate symetric key
        f = Fernet(symmetrickey) # Load key to crypto API
        decrytcardnobinary = f.decrypt(account['card_number'].encode())
        decrytcardno = decrytcardnobinary.decode()
        decrytcvvbinary = f.decrypt(account['cvv'].encode())
        decryptcvv = decrytcvvbinary.decode()
        # Pre Fill Form
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
        update_user_form.date.data = account['reservation_date']
        update_user_form.time.data = account['reservation_time']
        update_user_form.card_name.data = account['card_name']
        update_user_form.cn.data = decrytcardno
        update_user_form.expire.data = str(account['expiry_date'])[0:7]     # Only Display Year and Month
        update_user_form.cvv.data = decryptcvv
        update_user_form.Additional_note.data = account['additional_note']
    filename = account['email'].replace('@', '')

    # Virus Scanner
    endpoint = "https://api.virusscannerapi.com/virusscan"
    picfilename = 'static/accountsecpic/' + filename + "_mempic" + '1' + ".jpg"
    headers2 = {
        'X-ApplicationID': 'e725e24f-6c29-4c01-93a9-6f4b0c1ed03d',
        'X-SecretKey': 'b50a1340-ad8e-4af9-93e4-38f78341e5ea'
    }
    file2 = open(picfilename, "rb")
    data2 = {
        'async': 'false',
    }
    files2 = {
        'inputFile': (picfilename, file2.read())
    }
    r = requests.post(url=endpoint, data=data2, headers=headers2, files=files2)
    response = r.text
    splitresponse = response.split(sep=",") # Convert To List, For All Parts
    getstatus = splitresponse[5].split(sep=':')    # Convert To List, Only For The Status Part
    virusresult = getstatus[1].replace('"', '')  # Get Only Status of file
    return render_template('Reservation_updateUser.html', form=update_user_form, filename=filename, virusresult=virusresult)


@app.route('/deleteUser/<id>', methods=['POST'])
def delete_user(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM reservation WHERE reservation_id = %s ', [id])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Deleted reservation', session['staff_id'],))
    logger.info("{} deleted reservation".format(session['staff_id']))
    mysql.connection.commit()
    return redirect(url_for('retrieve'))


# Staff Menu
@app.route('/changetable/<state>')
def changetable(state):
    if state == "T":    # Increase Table Number By 1
        session['tablenum'] = session['tablenum'] + 1
    elif state == "F":  # Decrease Table Number By 1
        if session['tablenum'] > 1:
            session['tablenum'] = session['tablenum'] - 1
    return redirect(url_for('orderpagestaff'))


@app.route('/orderpage_staff')
def orderpagestaff():
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    # Start tablealloc
    try:
        session['tablealloc']
    except:
        session['tablealloc'] = True
        session['tablenum'] = 1
    # To Get Orders
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Get All Menu Information
    cursor.execute('SELECT * FROM menu')
    iteminfo = cursor.fetchall()
    # Retrieve Carts From All Table
    cursor.execute('SELECT * FROM cart ORDER BY table_num')
    allorders = cursor.fetchall()
    # Count The Number Of Tables That Exist In Database
    cursor.execute('SELECT DISTINCT table_num FROM cart')
    counttable = cursor.fetchall()
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Viewed order', session['staff_id'],))
    logger.info("{} viewed order".format(session['staff_id']))
    return render_template('Menu_Stafforderpage.html', allorders=allorders, counttable=counttable, iteminfo=iteminfo)


# Change State To Served
@app.route('/stateorderpage_staff/<ordernum>')
def stateorderpagestaff(ordernum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Retrieve Carts From All Table
    cursor.execute('UPDATE cart SET status= %s WHERE order_num= %s', ['Served', ordernum])
    mysql.connection.commit()
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Served order item', session['staff_id'],))
    logger.info("{} served order item".format(session['staff_id']))
    return redirect(url_for('orderpagestaff'))

# Delete Order Items
@app.route('/delorderpage_staff/<ordernum>')
def delorderpagestaff(ordernum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Retrieve Carts From All Table
    cursor.execute('DELETE FROM cart WHERE order_num = %s', [ordernum])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted order item', session['staff_id'],))
    logger.info("{} deleted order item".format(session['staff_id']))
    mysql.connection.commit()
    return redirect(url_for('orderpagestaff'))


# Add Item To Menu:
@app.route('/staffadditem', methods=['GET', 'POST'])
def staffadditem():
    msg = ''
    add_item_form = addmenu(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM menu')
    allmenu = cursor.fetchall()
    if request.method == 'POST' and add_item_form.validate():
        add_item_form.itemcode.data = add_item_form.itemcode.data.upper()
        cursor.execute('SELECT * FROM menu WHERE item_code = %s', [add_item_form.itemcode.data])
        item = cursor.fetchone()
        if add_item_form.itemcode.data[0] not in ['S', 'M', 'D', 'E', 'W']:
            msg = 'Invalid Item Code'
        elif item:
            msg = 'This Item Code Exist In The Database'
        else:
            print(add_item_form.itemprice.data)
            cursor.execute('INSERT INTO menu VALUES (%s, %s, %s, %s)', (add_item_form.itemcode.data, add_item_form.itemname.data, add_item_form.itemdesc.data, add_item_form.itemprice.data ))
            mysql.connection.commit()
            return redirect(url_for('staffadditem'))
    return render_template('Menu_Additem.html', form=add_item_form, msg=msg, allmenu=allmenu)


# Edit Item On Menu:
@app.route('/staffedititem/<itemcode>', methods=['GET', 'POST'])
def staffedititem(itemcode):
    edit_item_form = addmenu(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    msg = ''
    if request.method == 'POST' and edit_item_form.validate():
        edit_item_form.itemcode.data = edit_item_form.itemcode.data.upper()
        cursor.execute('SELECT * FROM menu WHERE item_code = %s', (edit_item_form.itemcode.data,))
        checkitem = cursor.fetchone()
        try:
            if checkitem['item_code'] != itemcode:
                msg = 'This Item Code Exist In The Database'
            elif edit_item_form.itemcode.data[0] not in ['S', 'M','D', 'E', 'W']:
                msg = 'Invalid Item Code'
            else:
                cursor.execute('UPDATE menu SET item_code= %s, item_name = %s, item_desc= %s, item_price= %s WHERE item_code = %s', (edit_item_form.itemcode.data, edit_item_form.itemname.data, edit_item_form.itemdesc.data, edit_item_form.itemprice.data, itemcode,))
                mysql.connection.commit()
                return redirect(url_for('staffadditem'))
        except:
            if edit_item_form.itemcode.data[0] not in ['S', 'M','D', 'E', 'W']:
                msg = 'Invalid Item Code'
            else:
                cursor.execute('UPDATE menu SET item_code= %s, item_name = %s, item_desc= %s, item_price= %s WHERE item_code = %s', (edit_item_form.itemcode.data, edit_item_form.itemname.data, edit_item_form.itemdesc.data, edit_item_form.itemprice.data, itemcode,))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Edit menu item', session['staff_id'],))
                logger.info("{} deleted menu item".format(session['staff_id']))
                mysql.connection.commit()
                return redirect(url_for('staffadditem'))
    else:
        cursor.execute('SELECT * FROM menu WHERE item_code = %s', (itemcode,))  # Get Item Info based on the item code choosen
        item = cursor.fetchone()
        edit_item_form.itemcode.data = item['item_code']
        edit_item_form.itemname.data = item['item_name']
        edit_item_form.itemdesc.data = item['item_desc']
        edit_item_form.itemprice.data = item['item_price']

    return render_template('Menu_Edititem.html', form=edit_item_form, msg=msg)


# Remove Menu Item
@app.route('/staffdelitem/<itemcode>', methods=['GET', 'POST'])
def staffdelitem(itemcode):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM menu WHERE item_code = %s ', [itemcode])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted menu item', session['staff_id'],))
    logger.info("{} deleted menu item".format(session['staff_id']))
    mysql.connection.commit()
    return redirect(url_for('staffadditem'))


# Retrieve Member
@app.route('/retrieveMembers')
def retrieve_Members():
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account where member_level is not null ')     # Get Only Members (Staff has no member Level (AKA NULL value), Therefore, it won't be displayed'
    users_list = cursor.fetchall()
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Retrieved members', session['staff_id'],))
    logger.info("{} retrieved members".format(session['staff_id']))
    mysql.connection.commit()
    return render_template('Member_retrieveUsers.html', count=len(users_list), users_list=users_list)


# Update Member Details for Staff
@app.route('/updateMemberstaff/<mememail>', methods=['GET', 'POST'])
def update_memberstaff(mememail):
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    update_user_form = UpdatememberdetailstaffForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        useremail = update_user_form.email.data.lower()
        cursor.execute('SELECT * FROM account WHERE email = %s', (useremail,))
        account = cursor.fetchone()
        if mememail != account['email']:   # Do Not Allow Change Of Email if The Email Address Entered Is Found In The Database
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, sign_up_date = %s WHERE email = %s', (useremail, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.signup_date.data, mememail,))
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated member', session['staff_id'],))
            logger.info("{} updated member".format(session['staff_id']))
            mysql.connection.commit()
            return redirect(url_for('acct_updateinfosuccess'))
    else:   # Pre Fill Form
        cursor.execute('SELECT * FROM account WHERE email = %s', (mememail,))
        account = cursor.fetchone()
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
        update_user_form.signup_date.data = account['sign_up_date']

    return render_template('Member_updateUser.html', form=update_user_form, msg=msg)


# Delete Member
@app.route('/deleteMember/<mememail>', methods=['POST'])
def delete_Member(mememail):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM account WHERE email = %s ', [mememail])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted member', session['staff_id'],))
    logger.info("{} deleted member".format(session['staff_id']))
    mysql.connection.commit()
    return redirect(url_for('retrieve_Members'))


# Staff Referal Codes
@app.route('/Referalcodes', methods=['GET','POST'])
def referal_codes():
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    msg = ''
    createcode = CreateCode(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM rewards ')
    code_list = cursor.fetchall()
    if request.method == 'POST' and createcode.validate():
        createcode.code.data.upper()
        cursor.execute('SELECT * FROM rewards WHERE reward_code = %s', (createcode.code.data,))
        code = cursor.fetchone()
        if code:    # Do Not Allow Duplicated Codes (By Checking if code number exist in the database)
            msg = 'This Code Exist In Database'
        else:
            cursor.execute('INSERT INTO rewards VALUES (%s, %s)', (createcode.code.data, 'Unclaimed'))
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Created referral code', session['staff_id'],))
            logger.info("{} created referral code".format(session['staff_id']))
            mysql.connection.commit()
            return redirect(url_for('referal_codes'))

    return render_template('Member_StaffReferalCodes.html', form=createcode, count=len(code_list), code_list=code_list, msg = msg)

# Delete Referal Codes
@app.route('/deleteReferal/<codenum>', methods=['GET', 'POST'])
def delete_code(codenum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM rewards WHERE reward_code = %s ', [codenum])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted referral code', session['staff_id'],))
    logger.info("{} deleted referral code".format(session['staff_id']))
    mysql.connection.commit()
    return redirect(url_for('referal_codes'))


# Create Staff User (Only Manager)
@app.route('/CreateStaff', methods=['GET','POST'])
def create_staff():
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    msg = ''
    create_user_form = CreateStaff(request.form)
    if request.method == 'POST' and create_user_form.validate():
        hire_date = datetime.date.today()    # Get Today's Date
        newdate = hire_date.strftime("%Y-%m-%d")    # To Format Date Into SQL Readable Format (YYYY-MM-DD)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        useremail = create_user_form.email.data.lower()

        # Password Hashing
        # Create a random number (Salt)
        salt = bcrypt.gensalt(rounds=16)
        # A hashed value is created with hashpw() function, which takes the cleartext value and a salt as parameters.
        hash_password = bcrypt.hashpw(create_user_form.password.data.encode(), salt)

        # Check If Email Exist In Database
        cursor.execute('SELECT * FROM account WHERE email = %s', (useremail,))
        account = cursor.fetchone()
        # Check If Staff ID Exist In Database
        cursor.execute('SELECT * FROM account WHERE staff_id = %s', (create_user_form.staff_id.data,))
        staffid = cursor.fetchone()
        if account:
            msg = 'This Email Has Been Taken'
        else:
            if staffid:
                msg = 'This Staff ID Has Been Taken'
            else:
                curdate = datetime.date.today()   # Get Today's date
                expiry_date = curdate + datetime.timedelta(days=90)
                pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
                if len(create_user_form.manager_id.data) == 0:  # For Normal Staff
                    cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, NULL, %s, NULL, %s, %s, NULL, NULL)', ([useremail, create_user_form.full_name.data, hash_password, pwd_expiry, 'Staff',  create_user_form.phone_number.data , create_user_form.staff_id.data, newdate, create_user_form.job_title.data]))
                    cursor.execute('INSERT INTO audit VALUES (%s, %s, %s, NULL, NULL, NULL, NULL, NULL, %s, %s)', (useremail, create_user_form.full_name.data, create_user_form.staff_id.data, 'Staff', 0))
                else:   # For Those With Manager ID
                    cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, NULL, %s, %s, %s, %s, NULL)', ([useremail, create_user_form.full_name.data, hash_password, pwd_expiry, 'Staff',  create_user_form.phone_number.data , create_user_form.staff_id.data, create_user_form.manager_id.data, newdate, create_user_form.job_title.data]))
                    cursor.execute('INSERT INTO audit VALUES (%s, %s, %s, NULL, NULL, NULL, NULL, NULL, %s, %s)', (useremail, create_user_form.full_name.data, create_user_form.staff_id.data, 'Manager', 0))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Created new staff', session['staff_id'],))
                # Store in Password History
                cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (useremail, hash_password))
                mysql.connection.commit()
                return redirect(url_for('confirmstaff', newuser=useremail))
    return render_template('Staff_Create.html', form=create_user_form, msg=msg)


@app.route('/confirmstaff/<newuser>')
def confirmstaff(newuser):
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    return render_template('Staff_Confirm.html', newuser=newuser)


@app.route('/staffRetrieve')
def staffretrieve():
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account where staff_id is not null ')     # Get Staff (Members will not be included as their staff_id is a null value)
    users_list = cursor.fetchall()
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Retrieved staff',session['staff_id'],))
    logger.info("{} retrieved staff".format(session['staff_id']))
    mysql.connection.commit()
    return render_template('Staff_Userslist.html', count=len(users_list), users_list=users_list)

# Update Staff Details
@app.route('/updateStaff/<toupdate>', methods=['GET', 'POST'])
def update_staff(toupdate):  # toupdate Variable Is Used in a case where 1 staff Member is editing another Staff Member's Information). toupdate is the staff memeber's name
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    update_user_form = UpdateStaff(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE full_name = %s and staff_id is not NULL', (toupdate,))  # Get Staff Email based on the staff name entered
    staff = cursor.fetchone()
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        useremail = update_user_form.email.data.lower()
        cursor.execute('SELECT * FROM account WHERE email = %s', (useremail,))
        account = cursor.fetchone()
        if staff['email'] != account['email']:
            msg = "This Email Has Been Used"
        else:
            if len(update_user_form.manager_id.data) == 0: # For Those Without Manager ID
                cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, staff_id=%s, hire_date= %s, manager_id=NULL, job_title= %s WHERE email = %s', (useremail, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.staff_id.data, update_user_form.hire_date.data, update_user_form.job_title.data, staff['email'],))
            else:   # For Those With Manager ID
                cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, staff_id=%s, manager_id=%s, hire_date= %s, job_title= %s WHERE email = %s', (useremail, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.staff_id.data, update_user_form.manager_id.data, update_user_form.hire_date.data, update_user_form.job_title.data, staff['email'],))
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self profile', session['staff_id'],))
            logger.info("{} updated self profile".format(session['staff_id']))
            mysql.connection.commit()
            return redirect(url_for('acct_updateinfosuccess'))
    else:
        cursor.execute('SELECT * FROM account WHERE email = %s', (staff['email'],))     # Get Account Information
        account = cursor.fetchone()
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
        update_user_form.staff_id.data = account['staff_id']
        update_user_form.manager_id.data = account['manager_id']
        update_user_form.hire_date.data = account['hire_date']
        update_user_form.job_title.data = account['job_title']

    return render_template('Staff_updateuser.html', form=update_user_form, msg=msg)


@app.route('/deleteStaff/<delstaffemail>/', methods=['POST'])
def delete_staff(delstaffemail):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM account WHERE email = %s ', [delstaffemail])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted staff', session['staff_id'],))
    logger.info("{} deleted staff {}".format(session['staff_id'], delstaffemail))
    mysql.connection.commit()
    return redirect(url_for('staffretrieve'))


@app.route('/updatestaffpass', methods=['GET', 'POST'])
def Changepass_staff():
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    update_user_form = ChangePasswordForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE staff_id = %s and staff_id is not NULL', (session['staff_id'],))
    staff = cursor.fetchone()
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s', (staff['email'],))
        account = cursor.fetchone()

        # Password Hashing (New Password Entered)
        # Create a random number (Salt)
        salt = bcrypt.gensalt(rounds=16)
        # A hashed value is created with hashpw() function, which takes the cleartext value and a salt as parameters.
        newhash_password = bcrypt.hashpw(update_user_form.newpassword.data.encode(), salt)

        if bcrypt.checkpw(update_user_form.oldpassword.data.encode(), account['password'].encode()):   # Ensure Old Password Matches The Password That The User Entered
            cursor.execute('SELECT * FROM password_hist WHERE email = %s', (staff['email'],))
            pwdhist = cursor.fetchall()
            if pwdhist:
                state = ''
                oldpass = pwdhist[0].get('password')
                if bcrypt.checkpw(update_user_form.newpassword.data.encode(), oldpass.encode()):
                    msg = ' This Password Has Been Used'
                    state = "used"
                if state != 'used':
                    if len(pwdhist) >= 2:
                        firstocc = pwdhist[0].get('serial_no')
                        cursor.execute('DELETE FROM password_hist WHERE serial_no = %s', [firstocc])
                        mysql.connection.commit()
                    curdate = datetime.date.today()   # Get Today's date
                    expiry_date = curdate + datetime.timedelta(days=90)
                    pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format

                    # Store Password
                    cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (staff['email'], newhash_password))
                    cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s WHERE email = %s', (newhash_password, pwd_expiry, staff['email'],))   # Update SQL To New Password That User Entered
                    cursor.execute('UPDATE audit SET action = %s WHERE email=%s', ('Updated password', staff['email'],))
                    logger.info("{} updated password".format(staff['email']))
                    mysql.connection.commit()
                    logout()
                    return redirect(url_for('acct_updatesuccess'))
            else:
                curdate = datetime.date.today()   # Get Today's date
                expiry_date = curdate + datetime.timedelta(days=90)
                pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
                # Store Password
                cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (session['email'], update_user_form.newpassword.data))
                cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s WHERE email = %s', (update_user_form.newpassword.data, pwd_expiry, session['email'],))   # Update SQL To New Password That User Entered
                cursor.execute('UPDATE audit SET action = %s WHERE email=%s', ('Updated password', email,))
                logger.info("{} updated password".format(email))
                mysql.connection.commit()
                logout()
                return redirect(url_for('acct_updatesuccess'))
        else:
            msg = 'Incorrect Password'
    return render_template('Staff_updateselfpass.html', form=update_user_form, msg=msg)


# New Features (Account Manage) -- Ian
# Forgot Password
@app.route('/Acctforgotpass', methods=['GET', 'POST'])
def acct_forgotpass():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    msg = ''
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['acctrecoveryattempt'] >= 3:
            try:
                session['acctrecblktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['acctrecblktime'] = blktill       # Block Attempts Till This Time
            session['acctrecblktime'] = session['acctrecblktime'].replace(tzinfo=None)
            timeremain = str(session['acctrecblktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('acctrecblktime', None)
                msg = ''
                session['acctrecoveryattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called loginattempt
        session['acctrecoveryattempt'] = 0

    check_user_form = Acctforgotpassword(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and check_user_form.validate() and session['acctrecoveryattempt'] < 3:
        useremail = check_user_form.email.data.lower()
        cursor.execute('SELECT * FROM account WHERE email = %s', (useremail ,))
        account = cursor.fetchone()
        if account:
            session['OTP'] = generate_otp('email', account['email'], 'forgot')
            session['acctrecoveremail'] = account['email']
            curtime = datetime.datetime.now()
            validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
            session['otpvalidtime'] = validtill       # Block Attempts Till This Time
            session.pop('acctrecoveryattempt', None)
            return redirect(url_for('acctenter_otp'))
        else:
            print("Account Not Found")
            session['acctrecoveryattempt'] = session['acctrecoveryattempt'] + 1
            return redirect(url_for('acct_forgotpass'))
    return render_template('Account_ForgotPassword.html', form=check_user_form, msg=msg)


# Forgot Account
@app.route('/acctforgotacct', methods=['GET', 'POST'])
def acct_forgotacct():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    msg = ''
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['acctrecoveryattempt'] >= 3:
            try:
                session['acctrecblktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['acctrecblktime'] = blktill       # Block Attempts Till This Time
            session['acctrecblktime'] = session['acctrecblktime'].replace(tzinfo=None)
            timeremain = str(session['acctrecblktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('acctrecblktime', None)
                msg = ''
                session['acctrecoveryattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called loginattempt
        session['acctrecoveryattempt'] = 0

    check_user_form = Acctforgotaccount(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and check_user_form.validate() and session['acctrecoveryattempt'] < 3:
        cursor.execute('SELECT * FROM account WHERE phone_num = %s', (check_user_form.phone_number.data,))
        account = cursor.fetchone()
        if account:
            session['acctrecoveremail'] = account['email']       # Put Email In A Session For Use Later
            session['acctrecoverphone'] = check_user_form.phone_number.data
            cursor.execute('SELECT * FROM security_qn WHERE email = %s', ([account['email']],))
            checkgotpic = cursor.fetchone()
            if checkgotpic is None:
                session['OTP'] = generate_otp('phone', str('+65' + session['acctrecoverphone'], 'forgot'))
                curtime = datetime.datetime.now()
                validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
                session['otpvalidtime'] = validtill       # Block Attempts Till This Time
                session.pop('acctrecoveryattempt', None)
                return redirect(url_for('forgotacctenter_otp'))
            else:
                session['choosesecpicattempt'] = 0
                session.pop('acctrecoveryattempt', None)
                return redirect(url_for('acctsecqn'))
        else:
            print("Account Not Found")
            session['acctrecoveryattempt'] = session['acctrecoveryattempt'] + 1
            return redirect(url_for('acct_forgotacct'))

    return render_template('Account_ForgotAccount.html', form=check_user_form, msg=msg)


# Enter Email OTP (For Forgot Password)
@app.route('/acctforgotpassotp', methods=['GET', 'POST'])
def acctenter_otp():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    check_user_form = EnterOTP(request.form)
    msg = ''
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['enterotpattempt'] >= 3:
            try:
                session['enterotpblktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['enterotpblktime'] = blktill       # Block Attempts Till This Time
            session['enterotpblktime'] = session['enterotpblktime'].replace(tzinfo=None)
            timeremain = str(session['enterotpblktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('enterotpblktime', None)
                msg = ''
                session['enterotpattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called enterotpattempt
        session['enterotpattempt'] = 0

    session['otpvalidtime'] = session['otpvalidtime'].replace(tzinfo=None)
    timeremain = str(session['otpvalidtime'] - datetime.datetime.now())       # Calculate Time Remaining
    timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
    if timeremain == ' day,':       # If Block Time Is Up
        session['OTP'] = 'Invalid'  # Set OTP to invalid

    if request.method == 'POST' and check_user_form.validate() and session['enterotpattempt'] < 3:
        if session['OTP'] == 'Invalid':
            msg = 'OTP Timeout, Please request for a new otp'
        elif int(check_user_form.OTP.data) == int(session['OTP']):
            session.pop('OTP', None)
            session.pop('enterotpattempt', None)
            session.pop('otpvalidtime', None)  # Remove otpvalidtime From Session
            return redirect(url_for('Change_Acct_Password'))
        else:
            msg = "Incorrect OTP"
    return render_template('Account_ForgotPassOTP.html', form=check_user_form, msg=msg)


# Resent Email OTP (For Forgot Password)
@app.route('/acctresentemailotp', methods=['GET', 'POST'])
def acctresentemail_otp():
    session.pop('OTP', None)
    session['OTP'] = generate_otp('email', session['EmailOTP'], 'forgot')

    curtime = datetime.datetime.now()
    validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
    session['otpvalidtime'] = validtill       # Block Attempts Till This Time

    return redirect(url_for('mementer_otp'))


# Enter SMS OTP: (For Forgot Account)
@app.route('/acctforgotacctotp', methods=['GET', 'POST'])
def forgotacctenter_otp():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['enterotpattempt'] >= 3:
            try:
                session['enterotpblktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['enterotpblktime'] = blktill       # Block Attempts Till This Time
            session['enterotpblktime'] = session['enterotpblktime'].replace(tzinfo=None)
            timeremain = str(session['enterotpblktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('enterotpblktime', None)
                msg = ''
                session['enterotpattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called enterotpattempt
        session['enterotpattempt'] = 0

    session['otpvalidtime'] = session['otpvalidtime'].replace(tzinfo=None)
    timeremain = str(session['otpvalidtime'] - datetime.datetime.now())       # Calculate Time Remaining
    timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
    if timeremain == ' day,':       # If Block Time Is Up
        session['OTP'] = 'Invalid'  # Set OTP to invalid

    check_user_form = EnterOTP(request.form)
    msg = ''
    if request.method == 'POST' and check_user_form.validate() and session['enterotpattempt'] < 3:
        if session['OTP'] == 'Invalid':
            msg = 'OTP Timeout, Please request for a new otp'
        elif int(check_user_form.OTP.data) == int(session['OTP']):
            session.pop('OTP', None)
            session.pop('enterotpattempt', None)
            session.pop('otpvalidtime', None)  # Remove otpvalidtime From Session
            return redirect(url_for('forgotacctshow'))
        else:
            session['enterotpattempt'] += session['enterotpattempt'] + 1
            msg = "Incorrect OTP"
    return render_template('Account_ForgotAccountOTP.html', form=check_user_form, msg=msg)


# Resent Phone OTP (For Forgot Account)
@app.route('/acctresentsmsotp', methods=['GET', 'POST'])
def acctresentsms_otp():
    session.pop('OTP', None)
    session['OTP'] = generate_otp('phone', str('+65' + session['acctrecoverphone']), 'forgot')

    curtime = datetime.datetime.now()
    validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
    session['otpvalidtime'] = validtill       # Block Attempts Till This Time
    return redirect(url_for('forgotacctenter_otp'))


# Show Email Address
@app.route('/acctforgotacctshow', methods=['GET', 'POST'])
def forgotacctshow():
    email = session['acctrecoveremail']
    session.pop('acctrecover', None)       # Remove User's Email From The Session acctrecover
    session.pop('acctrecoverphone', None)   # Remove User's Phone Number From The Session
    return render_template('Account_ForgotAccountShow.html', youremail=email)


# Mandatory Change Password:
# Update Password
@app.route('/ChangeAcctPassword', methods=['GET', 'POST'])
def Change_Acct_Password():
    msg = ''
    update_user_form = ManChangeAccountPassword(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and update_user_form.validate():
        #Check If Password Has Been Used Before
        cursor.execute('SELECT * FROM password_hist WHERE email = %s', (session['acctrecoveremail'],))
        pwdhist = cursor.fetchall()

        # Password Hashing (New Password Entered)
        # Create a random number (Salt)
        salt = bcrypt.gensalt(rounds=16)
        # A hashed value is created with hashpw() function, which takes the cleartext value and a salt as parameters.
        newhash_password = bcrypt.hashpw(update_user_form.newpassword.data.encode(), salt)

        if pwdhist:
            state = ''
            for a in pwdhist:
                if a['password'] == newhash_password:    # Check Password History
                    msg = ' This Password Has Been Used'
                    state = "used"
                    break
            if state != 'used':
                if len(pwdhist) >= 2:
                    firstocc = pwdhist[0].get('serial_no')
                    cursor.execute('DELETE FROM password_hist WHERE serial_no = %s', [firstocc])
                    mysql.connection.commit()
                curdate = datetime.date.today()   # Get Today's date
                expiry_date = curdate + datetime.timedelta(days=90)
                pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
                cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s, account_status = NULL WHERE email = %s', (newhash_password, pwd_expiry, session['acctrecoveremail'],))   # Update SQL To New Password That User Entered and Unlock User Account If Locked
                # Store Password
                cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (session['acctrecoveremail'], newhash_password))
                mysql.connection.commit()
                session.pop('acctrecoveremail', None)
                return redirect(url_for('acct_updatesuccess'))
        else:
            curdate = datetime.date.today()   # Get Today's date
            expiry_date = curdate + datetime.timedelta(days=90)
            pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
            cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s, account_status = NULL WHERE email = %s', (newhash_password, pwd_expiry, session['acctrecoveremail'],))   # Update SQL To New Password That User Entered and Unlock User Account If Locked
            # Store Password
            cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (session['acctrecoveremail'], newhash_password))
            mysql.connection.commit()
            session.pop('acctrecoveremail', None)
            return redirect(url_for('acct_updatesuccess'))

    return render_template('Account_ChangePassword.html', form=update_user_form, msg=msg)


@app.route('/Acctforgotacctsecqn', methods=['GET', 'POST'])
def acctsecqn():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    msg = ''
    mememail = session['acctrecoveremail']      # Get User's Email From The Phone Number They Entered
    photolist = []            # Add Picture That User Has Choosen When Setting Up Account Recovery
    for a in range(1,5):
        memselectedpic = mememail.replace('@', '') + "_memsecpic" + str(a)    # Get Picture File Name
        photolist.append(memselectedpic)
    random.shuffle(photolist)       # Shuffle Order Of Pictures To Be Shown
    check_user_form = secpic(request.form)
    check_user_form.secpic.choices = [(p, p) for p in photolist]    # Show Pictures In Radio Button Format
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM security_qn WHERE email = %s' , ([session['acctrecoveremail']]))
    acctsecinfo = cursor.fetchone()
    question = acctsecinfo['Security_Question']
    answer = mememail.replace('@', '') + "_memsecpic" + acctsecinfo['answer']
    if session['choosesecpicattempt'] >= 2: # Change Over to SMS OTP
        session['OTP'] = generate_otp('phone', str('+65' + session['acctrecoverphone']), 'forgot')
        curtime = datetime.datetime.now()
        validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
        session['otpvalidtime'] = validtill       # Block Attempts Till This Time
        return redirect(url_for('forgotacctenter_otp'))
    if request.method == 'POST' and check_user_form.validate():
        if check_user_form.secpic.data == answer:       # If Option That User Has Choosen Matches The One In The Account Recovery
             return redirect(url_for('forgotacctshow'))
        else:
            session['choosesecpicattempt'] = session['choosesecpicattempt'] + 1
    return render_template('Account_ForgotAcctsecqn.html', form=check_user_form, question=question, msg=msg)


# Show Their Fav Pic
@app.route('/showAcctsecfavpic', methods=['GET', 'POST'])
def showacctsecfavpic():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute('SELECT * FROM account WHERE staff_id = %s', ([session['staff_id']]))
        staffaccount = cursor.fetchone() # Since Staff and User Email are not stored the same way in session, Have to get email from staff name
        cursor.execute('SELECT * FROM security_qn WHERE email = %s', ([staffaccount['email']]))  # Check if user has previously set up security questions before
        gotaccount = cursor.fetchone()
        if gotaccount:
            filename = str(gotaccount['email']).replace('@', '') + "_memsecpic"
        else:
            return redirect(url_for('acctsecfavpic'))
    except:
        cursor.execute('SELECT * FROM security_qn WHERE email = %s', ([session['email']]))  # Check if user has previously set up security questions before
        gotaccount = cursor.fetchone()
        if gotaccount:
            filename = str(gotaccount['email']).replace('@', '') + "_memsecpic"
        else:
            return redirect(url_for('acctsecfavpic'))
    return render_template('Account_ExistUploadFavPic.html', account=gotaccount, filename=filename)


# Upload Their Fav Pic
@app.route('/Acctsecfavpic', methods=['GET', 'POST'])
def acctsecfavpic():
    upload_form = uploadfavpic(request.form)
    msg = ""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST':
        fileuploaded1 = request.files[upload_form.pic1.name].read()    # Get Image 1 In Pure Data Format
        fileuploaded2 = request.files[upload_form.pic2.name].read()    # Get Image 2 In Pure Data Format
        fileuploaded3 = request.files[upload_form.pic3.name].read()    # Get Image 3 In Pure Data Format
        fileuploaded4 = request.files[upload_form.pic4.name].read()    # Get Image 4 In Pure Data Format
        try:    # Using Staff Page
            cursor.execute('SELECT * FROM account WHERE staff_id = %s', ([session['staff_id']]))
            staffaccount = cursor.fetchone() # Since Staff and User Email are not stored the same way in session, Have to get email from staff name
            filename1 = str(staffaccount['email']).replace('@', '') + "_memsecpic" + '1' + ".jpg"   # Prep File Name
            filename2 = str(staffaccount['email']).replace('@', '') + "_memsecpic" + '2' + ".jpg"   # Prep File Name
            filename3 = str(staffaccount['email']).replace('@', '') + "_memsecpic" + '3' + ".jpg"   # Prep File Name
            filename4 = str(staffaccount['email']).replace('@', '') + "_memsecpic" + '4' + ".jpg"   # Prep File Name
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename1)), 'wb').write(fileuploaded1)    # Save The Picture 1 That Is Uploaded By The User
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename2)), 'wb').write(fileuploaded2)    # Save The Picture 2 That Is Uploaded By The User
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename3)), 'wb').write(fileuploaded3)    # Save The Picture 3 That Is Uploaded By The User
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename4)), 'wb').write(fileuploaded4)    # Save The Picture 4 That Is Uploaded By The User
            cursor.execute('SELECT * FROM security_qn WHERE email = %s', ([staffaccount['email']]))  # Check if user has previously set up security questions before
            gotaccount = cursor.fetchone()
            if gotaccount:
                cursor.execute('UPDATE security_qn SET Security_Question = %s, answer = %s WHERE email = %s', (upload_form.chosensecqn.data, upload_form.picchose.data, staffaccount['email']))   # Update SQL To New Password That User Entered and Unlock User Account If Locked
            else:
                cursor.execute('INSERT INTO security_qn VALUES (%s, %s, %s)', (staffaccount['email'], upload_form.chosensecqn.data, upload_form.picchose.data))    # Add Correct Picture into Database
            mysql.connection.commit()
            return redirect(url_for('staffpage'))
        except:   # Using member Page
            filename1 = str(session['email']).replace('@', '') + "_memsecpic" + '1' + ".jpg"   # Prep File Name
            filename2 = str(session['email']).replace('@', '') + "_memsecpic" + '2' + ".jpg"   # Prep File Name
            filename3 = str(session['email']).replace('@', '') + "_memsecpic" + '3' + ".jpg"   # Prep File Name
            filename4 = str(session['email']).replace('@', '') + "_memsecpic" + '4' + ".jpg"   # Prep File Name
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename1)), 'wb').write(fileuploaded1)    # Save The Picture 1 That Is Uploaded By The User
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename2)), 'wb').write(fileuploaded2)    # Save The Picture 2 That Is Uploaded By The User
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename3)), 'wb').write(fileuploaded3)    # Save The Picture 3 That Is Uploaded By The User
            open(os.path.join(app.config['UPLOAD_FOLDER'], str(filename4)), 'wb').write(fileuploaded4)    # Save The Picture 4 That Is Uploaded By The User
            cursor.execute('SELECT * FROM security_qn WHERE email = %s', ([session['email']]))  # Check if user has previously set up security questions before
            gotaccount = cursor.fetchone()
            if gotaccount:
                cursor.execute('UPDATE security_qn SET Security_Question = %s, answer = %s WHERE email = %s', (upload_form.chosensecqn.data, upload_form.picchose.data, session['email']))   # Update SQL To New Password That User Entered and Unlock User Account If Locked
            else:
                cursor.execute('INSERT INTO security_qn VALUES (%s, %s, %s)', (session['email'], upload_form.chosensecqn.data, upload_form.picchose.data))    # Add Correct Picture into Database
            mysql.connection.commit()
            return redirect(url_for('referral', referral_state=" "))
    return render_template('Account_UploadFavPic.html', form=upload_form, msg=msg)


def generate_otp(method, numemail, reason):     # numemail can be a phone number of email address, depending on the method passed in
    otp = random.randint(100000, 999999)
    if method == 'email' and reason == 'login':
        msg = Message('Piquant: Trying to login?', sender='piquant.nyp@gmail.com', recipients=[numemail])
        msg.body = str('Enter This OTP: {}, to login. OTP is valid for 1 minutes' .format(otp))
        mail.send(msg)
    if method == 'email' and reason == 'forgot':
        msg = Message('Piquant: Forgot Your Password?', sender='piquant.nyp@gmail.com', recipients=[numemail])
        msg.body = str('Enter This OTP: {}, to reset your password. OTP is valid for 1 minutes' .format(otp))
        mail.send(msg)
    if method == 'email' and reason == 'registering':
        msg = Message('Piquant: Registering Your Account?', sender='piquant.nyp@gmail.com', recipients=[numemail])
        msg.body = str('Enter This OTP: {}, to register your account. OTP is valid for 1 minutes' .format(otp))
        mail.send(msg)
    elif method == 'phone':
        message = twilioclient.messages \
        .create(
             body= str('This Is Your OTP {}. OTP is valid for 1 minutes' .format(otp)),
             from_='',
             to = numemail
         )
    return otp

# Verify Account (Choose OTP Method):
@app.route('/AuthenticateAcct', methods=['GET', 'POST'])
def authenticate_account():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    authenticate_option = AuthenticateAccount(request.form)
    if request.method == 'POST' and authenticate_option.validate():
        if authenticate_option.chooseOTP.data == 'Email':
            emailotp = generate_otp('email', session['authemail'], session['authreason'])  # To Generate Email OTP

            curtime = datetime.datetime.now()
            validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
            session['otpvalidtime'] = validtill       # Put OTP Valid Time in Session

            session['authotp'] = emailotp
            return redirect(url_for('authenticate_accountemail'))
        else:
             smsotp = generate_otp('phone', str('+65' + session['authphone']), session['authreason'])  # To Generate SMS OTP

             curtime = datetime.datetime.now()
             validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
             session['otpvalidtime'] = validtill       # Put OTP Valid Time in Session

             session['authotp'] = smsotp
             return redirect(url_for('authenticate_accountphone'))
    return render_template('Account_OTPMethod.html', form=authenticate_option)


@app.route('/AuthenticateAcctEmail', methods=['GET', 'POST'])
def authenticate_accountemail():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    msg = ''
    otpform = EnterOTP(request.form)
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['enterotpattempt'] >= 3:
            try:
                session['enterotpblktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['enterotpblktime'] = blktill       # Block Attempts Till This Time
            session['enterotpblktime'] = session['enterotpblktime'].replace(tzinfo=None)
            timeremain = str(session['enterotpblktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('enterotpblktime', None)
                msg = ''
                session['enterotpattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called enterotpattempt
        session['enterotpattempt'] = 0

    session['otpvalidtime'] = session['otpvalidtime'].replace(tzinfo=None)
    timeremain = str(session['otpvalidtime'] - datetime.datetime.now())       # Calculate Time Remaining
    timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
    if timeremain == ' day,':       # If Block Time Is Up
        session['authotp'] = 'Invalid'  # Set OTP to invalid

    if request.method == 'POST' and otpform.validate() and session['enterotpattempt'] < 3:
        if session['authotp'] == 'Invalid':
            msg = 'OTP Timeout, Please request for a new otp'
        elif int(otpform.OTP.data) == int(session['authotp']):    # Check if user entered OTP matches the one that is generated
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Retrive User Details (This is for Staff Part especially, since staff page uses staff name instead of email)
            cursor.execute('SELECT * FROM account WHERE email = %s', ([session['authemail']]))
            account = cursor.fetchone()
            # For Audit
            now = str(datetime.datetime.now().replace(microsecond=0))
            cursor.execute('UPDATE audit SET login_time = %s, action= %s WHERE email=%s', (now,'Logged in', session['authemail']))
            logger.info('{} is logged in'.format(session['authemail']))
            mysql.connection.commit()
            if account['staff_id'] == None: # For Memeber
                session['email'] = session['authemail'] # Put email in session
                session.pop('authphone', None)  # Remove Authentication Phone From Session
                session.pop('authotp', None)    # Remove Authentication OTP From Session
                session.pop('authemail', None)  # Remove Authentication Email From Session
                session.pop('otpvalidtime', None)  # Remove otpvalidtime From Session
                if session['authreason'] != 'login':    # If Authentication was used to verify account
                    # To Set Account Status To Verfied (NULL)
                    cursor.execute('UPDATE account SET account_status = NULL WHERE email=%s', ([session['email']]))
                    mysql.connection.commit()
                session.pop('authereason', None)   # Remove Authentication reason
                session['loggedin'] = True
                return redirect(url_for('referral', referral_state=" "))
            else:   # For Staff
                session.pop('authphone', None)  # Remove Authentication Phone From Session
                session.pop('authotp', None)    # Remove Authentication OTP From Session
                session.pop('authemail', None)  # Remove Authentication Email From Session
                session.pop('authereason', None)   # Remove Authentication reason
                session.pop('otpvalidtime', None)  # Remove otpvalidtime From Session
                session['stafflogged'] = account['full_name']   # Put staff name In Session
                session['staff_id'] = account['staff_id']   # Put Staff Id in Session
                if account['manager_id'] != None:   # If The Account Used is a manager
                    session['manager_id'] = account['manager_id']   # Put Manager Id in Session
                return redirect(url_for('staffpage'))
        else:
            session['enterotpattempt'] = session['enterotpattempt'] + 1 # Increase OTP attempts
            msg = 'Incorrect OTP'
    return render_template('Account_VerifyEmailOTP.html', form=otpform, msg=msg)


@app.route('/authenticateemailresentotp', methods=['GET', 'POST'])
def authenticatemail_resent_otp():
    emailotp = generate_otp('email', session['authemail'], session['authreason'])

    curtime = datetime.datetime.now()
    validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
    session['otpvalidtime'] = validtill       # Put OTP Valid Time in Session

    session['authotp'] = emailotp

    return redirect(url_for('authenticate_accountemail'))


@app.route('/AuthenticateAcctPhone', methods=['GET', 'POST'])
def authenticate_accountphone():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=1)     # Set Session Time Out
    msg = ''
    otpform = EnterOTP(request.form)
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['enterotpattempt'] >= 3:
            try:
                session['enterotpblktime']
            except:
                curtime = datetime.datetime.now()
                blktill = curtime + datetime.timedelta(minutes=1)    # Block For 1 Minutes
                session['enterotpblktime'] = blktill       # Block Attempts Till This Time
            session['enterotpblktime'] = session['enterotpblktime'].replace(tzinfo=None)
            timeremain = str(session['enterotpblktime'] - datetime.datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('enterotpblktime', None)
                msg = ''
                session['enterotpattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called enterotpattempt
        session['enterotpattempt'] = 0

    session['otpvalidtime'] = session['otpvalidtime'].replace(tzinfo=None)
    timeremain = str(session['otpvalidtime'] - datetime.datetime.now())       # Calculate Time Remaining
    timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
    if timeremain == ' day,':       # If Block Time Is Up
        session['authotp'] = 'Invalid'  # Set OTP to invalid

    if request.method == 'POST' and otpform.validate() and session['enterotpattempt'] < 3:
        if session['authotp'] == 'Invalid':
            msg = 'OTP Timeout, Please request for a new otp'
        elif int(otpform.OTP.data) == int(session['authotp']):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Retrive User Details (This is for Staff Part especially, since staff page uses staff name instead of email)
            cursor.execute('SELECT * FROM account WHERE email = %s', ([session['authemail']]))
            account = cursor.fetchone()
            # For Audit
            now = str(datetime.datetime.now().replace(microsecond=0))
            cursor.execute('UPDATE audit SET login_time = %s, action= %s WHERE email=%s', (now,'Logged in', session['authemail']))
            logger.info('{} is logged in'.format(session['authemail']))
            mysql.connection.commit()

            if account['staff_id'] == None: # For Memeber
                session['email'] = session['authemail'] # Put email in session
                session.pop('authphone', None)  # Remove Authentication Phone From Session
                session.pop('authotp', None)    # Remove Authentication OTP From Session
                session.pop('authemail', None)  # Remove Authentication Email From Session
                session.pop('otpvalidtime', None)  # Remove otpvalidtime From Session
                if session['authreason'] != 'login':    # If Authentication was used to verify account
                    # To Set Account Status To Verfied (NULL)
                    cursor.execute('UPDATE account SET account_status = NULL WHERE email=%s', ([session['email']]))
                    mysql.connection.commit()
                session.pop('authereason', None)   # Remove Authentication reason
                session['loggedin'] = True
                return redirect(url_for('referral', referral_state=" "))
            else:   # For Staff
                session.pop('authphone', None)  # Remove Authentication Phone From Session
                session.pop('authotp', None)    # Remove Authentication OTP From Session
                session.pop('authemail', None)  # Remove Authentication Email From Session
                session.pop('authereason', None)   # Remove Authentication reason
                session.pop('otpvalidtime', None)  # Remove otpvalidtime From Session
                session['stafflogged'] = account['full_name']   # Put Staff Name In Session
                session['stafflogged'] = account['staff_id']   # Put Staff Id In Session
                if account['manager_id'] != None:   # If The Account Used is a manager
                        session['manager_id'] = account['manager_id']   # Put Manager Id in Session
                return redirect(url_for('staffpage'))
        else:
            session['enterotpattempt'] = session['enterotpattempt'] + 1
            msg = 'Incorrect OTP'
    return render_template('Account_VerifyPhoneOTP.html', form=otpform, msg=msg)

@app.route('/authenticatephoneresentotp')
def authenticatephone_resent_otp():
    smsotp = generate_otp('phone', str('+65' + session['authphone']), session['authreason'])
    curtime = datetime.datetime.now()
    validtill = curtime + datetime.timedelta(minutes=1)    # Remove OTP after 3 minutes
    session['otpvalidtime'] = validtill       # Put OTP Valid Time in Session

    session['authotp'] = smsotp
    return redirect(url_for('authenticate_accountphone'))


# Turn on 2FA
@app.route('/account2fa', methods=['GET', 'POST'])
def account_2fa():
    msg = ''
    fa2methodform = Choose2fa(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and fa2methodform.validate():
        try: # If Staff is logged In
            cursor.execute('SELECT * FROM account WHERE staff_id = %s', ([session['staff_id']]))
            staffaccount = cursor.fetchone() # Since Staff and User Email are not stored the same way in session, Have to get email from staff name
            if fa2methodform.fa2methodoption.data == "Yes":
                # To Set Account Status To Verfied (NULL)
                cursor.execute('UPDATE account SET 2fa_status = %s WHERE email=%s', (['Yes', staffaccount['email']]))
                mysql.connection.commit()
                msg = '2 Factor Authentication has been turned on'
            else:
                # To Set Account Status To Verfied (NULL)
                cursor.execute('UPDATE account SET 2fa_status=NULL WHERE email=%s', ([staffaccount['email']]))
                mysql.connection.commit()
                msg = '2 Factor Authentication has been turned off'
        except:
            if fa2methodform.fa2methodoption.data == "Yes":
                # To Set Account Status To Verfied (NULL)
                cursor.execute('UPDATE account SET 2fa_status = %s WHERE email=%s', (['Yes', session['email']]))
                mysql.connection.commit()
                msg = '2 Factor Authentication has been turned on'
            else:
                # To Set Account Status To Verfied (NULL)
                cursor.execute('UPDATE account SET 2fa_status=NULL WHERE email=%s', ([session['email']]))
                mysql.connection.commit()
                msg = '2 Factor Authentication has been turned off'
    # Check 2FA status, then set radio button defaults
    try:
        cursor.execute('SELECT * FROM account WHERE staff_id = %s', ([session['staff_id']]))
        staffaccount = cursor.fetchone() # Since Staff and User Email are not stored the same way in session, Have to get email from staff name
        if staffaccount['2fa_status'] == 'Yes':
            fa2methodform.fa2methodoption.default = 'Yes'   # Set Radio defaults to Yes
        else:
            fa2methodform.fa2methodoption.default = 'No'    # Set Radio defaults to No
    except:
        cursor.execute('SELECT * FROM account WHERE email = %s', ([session['email']]))
        account = cursor.fetchone()     # Since Staff and User Email are not stored the same way in session, Have to get email from staff name
        if account['2fa_status'] == 'Yes':
            fa2methodform.fa2methodoption.default = 'Yes'   # Set Radio defaults to Yes
        else:
            fa2methodform.fa2methodoption.default = 'No'    # Set Radio defaults to No
    fa2methodform.process() # Set Defaults to the form
    return render_template('Account_2FAOption.html', form=fa2methodform, msg=msg)


# Ernest Audit Page
@app.route('/manaud', methods=['GET','POST'])
# @man
def manager_audit():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    # Check if its manager login
    try:
        session['manager_id']
    except:
        cursor.execute('SELECT * FROM audit WHERE staff_id = %s', ([session['staff_id']]))
        staffinfo = cursor.fetchone()
        newsusnum = staffinfo['suspicious'] + 1
        cursor.execute('UPDATE audit SET suspicious = %s WHERE staff_id = %s', ([newsusnum, session['staff_id']]))
        mysql.connection.commit()
        return redirect(url_for('error'))


    cursor.execute('SELECT * FROM audit WHERE staff_id is not null')
    audit = cursor.fetchall()
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Viewed audit', session['staff_id']))
    logger.info("{} viewed audit".format(session['staff_id']))
    mysql.connection.commit()
    with open('audit.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['manager_id','staff_id','usage','email','full_name','login_time','logout_time', 'action', 'failed_login', 'role', 'suspicious'])
        writer.writeheader()
        for i in audit:
            writer.writerow(i)
    f.close()
    return render_template('Staff_audit_manager.html', audit=audit)


@app.route('/staffauditdashboard')
# @man
def staff_audit_dashboard():
    # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    # Check if its manager login
    try:
        session['manager_id']
    except:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM audit WHERE staff_id = %s', ([session['staff_id']]))
        staffinfo = cursor.fetchone()
        newsusnum = staffinfo['suspicious'] + 1
        cursor.execute('UPDATE audit SET suspicious = %s WHERE staff_id = %s', ([newsusnum, session['staff_id']]))
        mysql.connection.commit()
        return redirect(url_for('error'))

    return render_template('Staff_Audit_dashboard.html')

# Error Handling
@app.route('/error')
def error():
    return render_template('error.html')


# Extra, Shutdown Server
@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return redirect(url_for('home'))

def shutdown_server():
    check = request.environ.get('werkzeug.server.shutdown')
    check()



# Zhi Yang Watchdog/Backup
@app.route("/watchdog", methods=["GET"])
def watchdog():
     # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    # Check if its manager login
    try:
        session['manager_id']
    except:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM audit WHERE staff_id = %s', ([session['staff_id']]))
        staffinfo = cursor.fetchone()
        newsusnum = staffinfo['suspicious'] + 1
        cursor.execute('UPDATE audit SET suspicious = %s WHERE staff_id = %s', ([newsusnum, session['staff_id']]))
        mysql.connection.commit()
        return redirect(url_for('error'))

    br.MyDrive().items()
    a_file = open("data.pkl", "rb")
    file_ids = pickle.load(a_file)
    values_list = []
    for i in file_ids:
        values_list.append(i.values())
    return render_template("watchdoglog.html", values_list=values_list)

def flask_logger():
    with open("watch_dog_logs.log") as log_info:
        while True:
            data = log_info.read()
            yield data.encode()
            time.sleep(1)
        # Create empty job.log, old logging will be deleted
        #open("watch_dog_logs.log", 'w').close()


# Clear Log File
@app.route("/clearwatchdog_log", methods=["GET"])
def clearwatchdog_log():
    with open('watch_dog_logs.log', 'w'):
        pass
    msg = 'Log File Cleared'
    return redirect(url_for('watchdog'))


@app.route("/log_stream", methods=["GET"])
def stream():
    return Response(flask_logger(), mimetype="text/plain", content_type="text/event-stream")


@app.route("/backup", methods=['GET', 'POST'])
def backup_file():
     # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    # Check if its manager login
    try:
        session['manager_id']
    except:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM audit WHERE staff_id = %s', ([session['staff_id']]))
        staffinfo = cursor.fetchone()
        newsusnum = staffinfo['suspicious'] + 1
        cursor.execute('UPDATE audit SET suspicious = %s WHERE staff_id = %s', ([newsusnum, session['staff_id']]))
        mysql.connection.commit()
        return redirect(url_for('error'))

    br.upload()
    msg = "Upload done on " + time.asctime(time.localtime(time.time()))
    print("Upload done on " + time.asctime(time.localtime(time.time())))
    print("\n")
    br.MyDrive().items()
    a_file = open("data.pkl", "rb")
    file_ids = pickle.load(a_file)
    values_list = []
    for i in file_ids:
        values_list.append(i.values())

    return render_template("watchdoglog.html", msg=msg, values_list=values_list)


@app.route("/retrive", methods=['GET', 'POST'])
def retrive_file():
     # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    # Check if its manager login
    try:
        session['manager_id']
    except:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM audit WHERE staff_id = %s', ([session['staff_id']]))
        staffinfo = cursor.fetchone()
        newsusnum = staffinfo['suspicious'] + 1
        cursor.execute('UPDATE audit SET suspicious = %s WHERE staff_id = %s', ([newsusnum, session['staff_id']]))
        mysql.connection.commit()
        return redirect(url_for('error'))

    try:
        file_id = request.form['file_id']
        start = br.MyDrive()
        br.Restore(file_id)
        br.unzip()
        msg = "Restoration done on " + time.asctime(time.localtime(time.time()))
        print("Restoration done on " + time.asctime(time.localtime(time.time())))
        print("\n")
        br.MyDrive().items()
        a_file = open("data.pkl", "rb")
        file_ids = pickle.load(a_file)
        values_list = []
        for i in file_ids:
            values_list.append(i.values())
    except HttpError:
        msg = "please try again"

    return render_template("watchdoglog.html", msg=msg, values_list=values_list)


@app.route("/start", methods=["get"])
def watchdogstart():
     # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    # Check if its manager login
    try:
        session['manager_id']
    except:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM audit WHERE staff_id = %s', ([session['staff_id']]))
        staffinfo = cursor.fetchone()
        newsusnum = staffinfo['suspicious'] + 1
        cursor.execute('UPDATE audit SET suspicious = %s WHERE staff_id = %s', ([newsusnum, session['staff_id']]))
        mysql.connection.commit()
        return redirect(url_for('error'))

    PATH = "../Piquant Integrated"
    message = "Watchdog system active"
    global observer
    observer = Observer()
    event_handler = wd.FileEventHandler(ignore_patterns=['.swp', '.swx', '*.swpx'])
    observer.schedule(event_handler, PATH, recursive=True)
    observer.start()
    br.MyDrive().items()
    a_file = open("data.pkl", "rb")
    file_ids = pickle.load(a_file)
    values_list = []
    for i in file_ids:
        values_list.append(i.values())
    return render_template("watchdoglog.html", message=message, values_list=values_list)


@app.route("/stop", methods=["get"])
def watchdog_stop():
     # Check If Staff Is Logged In (This Is To Prevent User From Using The Back Button)
    try:
        session['stafflogged']
    except:
        return redirect(url_for('checkstaff'))

    # Check if its manager login
    try:
        session['manager_id']
    except:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM audit WHERE staff_id = %s', ([session['staff_id']]))
        staffinfo = cursor.fetchone()
        newsusnum = staffinfo['suspicious'] + 1
        cursor.execute('UPDATE audit SET suspicious = %s WHERE staff_id = %s', ([newsusnum, session['staff_id']]))
        mysql.connection.commit()
        return redirect(url_for('error'))

    try:
        message = "Watchdog system deactivated"
        observer.stop()
        observer.on_thread_stop()
        observer.join()
        br.MyDrive().items()
        a_file = open("data.pkl", "rb")
        file_ids = pickle.load(a_file)
        values_list = []
        for i in file_ids:
            values_list.append(i.values())
    except NameError:
        message = "Please click the start button first"
        br.MyDrive().items()
        a_file = open("data.pkl", "rb")
        file_ids = pickle.load(a_file)
        values_list = []
        for i in file_ids:
            values_list.append(i.values())
    return render_template("watchdoglog.html", message=message, values_list=values_list)


if __name__ == '__main__':
    app.run()
