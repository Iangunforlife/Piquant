from flask import Flask, render_template, request, redirect, url_for, session
from forms import *
import Member_Completion, GenerateOrderNum, random, logging
from datetime import date, datetime, timedelta
from flask_mysqldb import MySQL
import MySQLdb.cursors
from datetime import date
import datetime
from handler import error
from functools import wraps # don't need to pip install
import splunklib.client as client # pip install splunk-sdk
import socket
from flask_mail import Mail, Message
import os
from twilio.rest import Client
from werkzeug.exceptions import RequestEntityTooLarge

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
    password=''
)
'''

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

# Email To Be Passed into codes to check wether users are login or not
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

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
    if request.method == 'POST' and create_user_form.validate():
        # add in update user action here
        useremail = create_user_form.email.data.lower()
        cursor.execute('INSERT INTO reservation VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (create_user_form.full_name.data, useremail, create_user_form.phone_number.data, create_user_form.date.data,create_user_form.time.data,create_user_form.card_name.data,create_user_form.cn.data,str(create_user_form.expire.data + '-01'),create_user_form.cvv.data,create_user_form.Additional_note.data))
        mysql.connection.commit()   #Update SQL Database
        logger.info('{} has made a reservation'.format(create_user_form.full_name.data))
        return redirect(url_for('retrieve_users', email=email))
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


#Akif
# Create User
@app.route('/createMember', methods=['GET', 'POST'])
def create_Member():
    msg = ''
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        signupdate = date.today()   # Get Today's date
        newdate = signupdate.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
        login_time = datetime.datetime.now().replace(microsecond=0)
        date_time = datetime.datetime(2021, 12, 31)
        exp_date = date_time.strftime("%Y-%m-%d")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        useremail = create_user_form.email.data.lower()
        cursor.execute('SELECT * FROM account WHERE email = %s', (useremail,))
        account = cursor.fetchone()
        if account:     # Ensure That there will be no duplicates (As Email is A Primary Key In The Database)
            msg = 'This Email Has Been Taken'
        else:
            cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %7s, %s, %s, NULL, NULL, NULL)', (useremail, create_user_form.full_name.data, create_user_form.password.data, 'Member',  create_user_form.phone_number.data , "Regular", "1/5", newdate))
            cursor.execute('UPDATE account SET login_time = %s pwd_expiry= %s WHERE email = %s', (login_time,exp_date,create_user_form.email.data,))
            cursor.execute('UPDATE audit SET action = %s WHERE email = %s', ('Signed up as member', create_user_form.email.data,))
            logger.info('{} signed up as member'.format(create_user_form.full_name.data))
            session['login'] = True
            session['email'] = useremail
            mysql.connection.commit()
            return redirect(url_for('referral', state=" "))
    return render_template('Member_createUser.html', form=create_user_form, msg=msg)


# Login
@app.route('/Memberlogin', methods=['GET', 'POST'])
def member_login():
    # New
    msg = ''
    try:    # Check If There's A Login Attempt Session In Place
        # At 5 Attempt
        if session['loginattempt'] == 5:
            try:
                session['blktime']
            except:
                curtime = datetime.now()
                blktill = curtime + timedelta(minutes=1)    # Block For 1 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            timeremain = str(session['blktime'] - datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = session['loginattempt'] + 1   # To Unblock User
            else:
                msg = 'You account has been locked. You can try again after ' + timeremain + 'Minutes'
        # At 10 Attempt ( Have To Put 11 As Session Will +1 To Unblock User Earlier On)
        elif session['loginattempt'] == 11:
            try:
                session['blktime']
            except:
                curtime = datetime.now()
                blktill = curtime + timedelta(minutes=10)    # Block For 10 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            timeremain = str(session['blktime'] - datetime.now())   # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = session['loginattempt'] + 1   # To Unblock User
            else:
                msg = 'You account has been locked. Please reset your password to unlocked your account'
    except:     # Create A New Session called loginattempt
        session['loginattempt'] = 0

    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate() and session['loginattempt'] != 5 and session['loginattempt'] != 11:
        useremail = check_user_form.email.data.lower()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (useremail,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:     # If Account Exist In DataBase
            if account['account_status'] == "Blocked":
                msg = 'This Account Has Been Locked, Please Reset Your Password To Unlock Your Account'
            elif check_user_form.password.data == account['password']:      # Check If Password Entered By User Is The Same As The One In The Database
                session.pop('loginattempt', None)
                # To Force User To Change Password
                if account['pwd_expiry'] <= datetime.datetime.today().date():       # Compare Password Expiry Date To Current Date
                    session['acctrecoveremail'] = account['email']
                    return redirect(url_for('Change_Acct_Password'))   # Redirect to Password Change Page
                else:
                    session['loggedin'] = True
                    session['email'] = account['email']
                    now = str(datetime.datetime.now().replace(microsecond=0))
                    cursor.execute('UPDATE audit SET login_time = %s, action= %s WHERE email=%s', (now,'Logged in', session['email']))
                    logger.info('{} is logged in'.format(session['email']))
                    return redirect(url_for('referral', state=" "))
            else:
                msg = "Incorrect Username/Password"     # Return Incorrect Username/Password as a message
        else:
            msg = "Incorrect Username/Password"     # Return Incorrect Username/Password as a message
        session['loginattempt'] = session['loginattempt'] + 1   # Increase Login Attempt By One
        if session['loginattempt'] == 11:    # If Login Attempt Reached 10, Account Will Be Locked [Needs to be equal to 11 as the system will add 1 attempt to allow user to try after the initial 3 failed attempt]
            cursor.execute('UPDATE account SET account_status = %s WHERE email = %s', ("Blocked", useremail,))     # Set Account Status To Blocked In SQL
            mysql.connection.commit()
    return render_template('Member_login.html', form=check_user_form, msg=msg)


# Referral
@app.route('/referral/<state>', methods=['GET', 'POST'])
def referral(state):
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
            return redirect(url_for('referral', email=email, state="used"))
        elif check == "claim":
            newreward = Member_Completion.increase_completion(account['member_level'], account['member_completion'])     # Increase Completion Using Function
            cursor.execute('UPDATE account SET member_level = %s, member_completion = %s WHERE email = %s', (newreward[0], newreward[1], session['email'],))
            cursor.execute('UPDATE audit SET action = %s WHERE email=%s', ('Claimed referral code', email,))
            logger.info('{} claimed referral code {}'.format(email, claim_form.claim_code.data))
            mysql.connection.commit()
            return redirect(url_for('referral', state="claim"))
        else:
            return redirect(url_for('referral', state="unclaimed"))

    return render_template('Member_referral.html', form=claim_form, user=account, state=state)

@app.route('/acctsuccess')
def acct_updatesuccess():
    logout()
    return render_template('Member_Selfupdatesuccess.html')

@app.route('/logout')   # Universal Logout Function
def logout():
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('stafflogged', None)
    session.pop('staff_id', None)
    session.pop('manager_id', None)
    return redirect(url_for('home'))

@app.route('/membersucess')
def member_updatesucess():
    return render_template('Member_Selfupdatesuccess.html')


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
            return redirect(url_for('acct_updatesuccess'))
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
        if update_user_form.oldpassword.data == account['password']:   # Check If Old Password Entered Is The Same One Entered By The User
            cursor.execute('SELECT * FROM password_hist WHERE email = %s', (session['email'],))
            pwdhist = cursor.fetchall()
            if pwdhist:
                state = ''
                if pwdhist[0].get('password') == update_user_form.newpassword.data:
                    msg = ' This Password Has Been Used'
                    state = "used"
                if state != 'used':
                    if len(pwdhist) >= 2:
                        firstocc = pwdhist[0].get('serial_no')
                        cursor.execute('DELETE FROM password_hist WHERE serial_no = %s', [firstocc])
                        mysql.connection.commit()
                    curdate = date.today()   # Get Today's date
                    expiry_date = curdate + timedelta(days=90)
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
                curdate = date.today()   # Get Today's date
                expiry_date = curdate + timedelta(days=90)
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


#Staff Pages
@app.route('/Stafflogin', methods=['GET','POST'])
def checkstaff():
    check_user_form = LoginForm(request.form)
    msg = ' '
    try:    # Check If There's A Login Attempt Session In Place
        # At 5 Attempt
        if session['loginattempt'] == 5:
            try:
                session['blktime']
            except:
                curtime = datetime.now()
                blktill = curtime + timedelta(minutes=5)    # Block For 5 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            timeremain = str(session['blktime'] - datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = session['loginattempt'] + 1   # To Unblock User
            else:
                msg = 'You Have Been Blocked, Please Wait For ' + timeremain
        # At 10 Attempt ( Have To Put 11 As Session Will +1 To Unblock User Earlier On)
        elif session['loginattempt'] == 11:
            try:
                session['blktime']
            except:
                curtime = datetime.now()
                blktill = curtime + timedelta(minutes=10)    # Block For 10 Minutes
                session['blktime'] = blktill       # Block Attempts Till This Time
            timeremain = str(session['blktime'] - datetime.now())   # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('blktime', None)
                msg = ''
                session['loginattempt'] = session['loginattempt'] + 1   # To Unblock User
            else:
                msg = 'You Have Been Blocked, Please Wait For ' + timeremain
    except:     # Create A New Session called loginattempt
        session['loginattempt'] = 0

    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate() and session['loginattempt'] != 5 and session['loginattempt'] != 11:
        useremail = check_user_form.email.data.lower()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:
            if account['account_status'] == "Blocked":
                msg = 'This Account Has Been Locked, Please Reset Your Password To Unlock Your Account'
            elif account['password'] == check_user_form.password.data:
                if account['staff_id'] != None:     # Only allow access if staff_id field in the account has information in it (If An Account is a member, The Staff_id field would not be filled up)
                    # To Force User To Change Password
                    if account['pwd_expiry'] <= datetime.datetime.today().date():       # Compare Password Expiry Date To Current Date
                        session['acctrecoveremail'] = account['email']
                        return redirect(url_for('Change_Acct_Password'))   # Redirect to Password Change Page
                    else:
                        logintime = str(datetime.datetime.now().replace(microsecond=0))
                        session.pop('loginattempt', None)
                        session['stafflogged'] = account['full_name']   # Put Staff Name In Session
                        session['staff_id'] = account['staff_id']   # Put Staff Id in Session
                        logger.info("{} is logged in".format(account['staff_id']))
                        cursor.execute('UPDATE audit SET action = %s, login_time = %s WHERE email = %s ', ('Logged in', logintime, account['email'],))
                        mysql.connection.commit()
                        if account['manager_id'] != None:
                            session['manager_id'] = account['manager_id']   # Put Manager Id in Session
                        return redirect(url_for('staffpage'))
                else:
                    msg = "Incorrect Username/Password"
            else:
                msg = "Incorrect Username/Password"
        else:
            msg = "Incorrect Username/Password"
        session['loginattempt'] = session['loginattempt'] + 1   # Increase Login Attempt By One
        if session['loginattempt'] == 11:    # If Login Attempt Reached 10, Account Will Be Locked [Needs to be equal to 11 as the system will add 1 attempt to allow user to try after the initial 3 failed attempt]
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

@app.route('/Managerpage/')

def manpage():
    # Check If Manager is Logged In
    try:
        session['manager_id']
    except:
        return redirect(url_for('checkstaff'))
    return render_template('Manager_Page.html')

# Reservation Form
@app.route('/retrieveReservation')


def retrieve():
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
    update_user_form = ReservationForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation WHERE reservation_id = %s', [id])       # Get Entire Row That Contains The Reservation ID
    account = cursor.fetchone()
    if request.method == 'POST' and update_user_form.validate():
        useremail = update_user_form.email.data.lower()
        cursor.execute('UPDATE reservation SET full_name= %s, email = %s, phone_num= %s, reservation_date= %s, reservation_time= %s, card_name= %s, card_number= %s, expiry_date= %s, cvv= %s, additional_note= %s WHERE reservation_id = %s', (update_user_form.full_name.data, useremail, update_user_form.phone_number.data, update_user_form.date.data, update_user_form.time.data, update_user_form.card_name.data, update_user_form.cn.data,str(update_user_form.expire.data + '-01'), update_user_form.cvv.data, update_user_form.Additional_note.data, id))
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Updated reservation', session['staff_id'],))
        logger.info("{} updated reservation".format(session['staff_id']))
        mysql.connection.commit()
        return redirect(url_for('retrieve'))
    else:   # Pre Fill Form
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
        update_user_form.date.data = account['reservation_date']
        update_user_form.time.data = account['reservation_time']
        update_user_form.card_name.data = account['card_name']
        update_user_form.cn.data = account['card_number']
        update_user_form.expire.data = str(account['expiry_date'])[0:7]     # Only Display Year and Month
        update_user_form.cvv.data = account['cvv']
        update_user_form.Additional_note.data = account['additional_note']
    return render_template('Reservation_updateUser.html', form=update_user_form)


@app.route('/deleteUser/<id>', methods=['POST'])
def delete_user(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM reservation WHERE reservation_id = %s ', [id])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Deleted reservation', session['staff_id'],))
    logger.info("{} deleted reservation".format(session['staff_id']))
    mysql.connection.commit()
    return redirect(url_for('retrieve'))


#Menu Page (Ian)
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


#Akif
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
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Retrieved members', session['stafflogged'],))
    logger.info("{} retrieved members".format(session['stafflogged']))
    mysql.connection.commit()
    return render_template('Member_retrieveUsers.html', count=len(users_list), users_list=users_list)


# Update Member for Staff
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
            return redirect(url_for('retrieve_Members'))
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


#Referal Codes
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

#Delete Referal Codes
@app.route('/deleteReferal/<codenum>', methods=['GET', 'POST'])
def delete_code(codenum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM rewards WHERE reward_code = %s ', [codenum])
    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted referral code', session['staff_id'],))
    logger.info("{} deleted referral code".format(session['staff_id']))
    mysql.connection.commit()
    return redirect(url_for('referal_codes'))


#Create Staff User (Only Manager)
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
        hire_date = date.today()    # Get Today's Date
        newdate = hire_date.strftime("%Y-%m-%d")    # To Format Date Into SQL Readable Format (YYYY-MM-DD)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        useremail = create_user_form.email.data.lower()
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
                curdate = date.today()   # Get Today's date
                expiry_date = curdate + timedelta(days=90)
                pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
                cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %s, NULL, NULL, NULL, %s, %s, %s, %s)', (useremail, create_user_form.full_name.data, create_user_form.password.data, pwd_expiry, 'Staff',  create_user_form.phone_number.data , create_user_form.staff_id.data, create_user_form.manager_id.data, newdate, create_user_form.job_title.data))
                cursor.execute('INSERT INTO audit VALUES (%s, %s, %s, NULL, NULL, NULL, NULL, NULL, NULL, NULL)', (create_user_form.email.data, create_user_form.full_name, create_user_form.staff_id))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Created new staff', session['staff_id'],))
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
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, staff_id=%s, manager_id=%s,  hire_date= %s, job_title= %s WHERE email = %s', (useremail, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.staff_id.data, update_user_form.manager_id.data, update_user_form.hire_date.data, update_user_form.job_title.data, staff['email'],))
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self profile', session['staff_id'],))
            logger.info("{} updated self profile".format(session['staff_id']))
            mysql.connection.commit()
            return redirect(url_for('staffretrieve'))
    else:
        cursor.execute('SELECT * FROM account WHERE email = %s', (staff['email'],))     # Get Account Information
        account = cursor.fetchone()
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
        update_user_form.staff_id.data = account['staff_id']
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
    cursor.execute('SELECT * FROM account WHERE full_name = %s and staff_id is not NULL', (session['stafflogged'],))
    staff = cursor.fetchone()
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     cursor.execute('SELECT * FROM account WHERE email = %s', (staff['email'],))
     account = cursor.fetchone()
     if update_user_form.oldpassword.data == account['password']:   # Ensure Old Password Matches The Password That The User Entered
         cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, staff['email'],))
         cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self password', session['staff_id'],))
         logger.info("{} updated self password".format(session['staff_id']))
         mysql.connection.commit()
         return redirect(url_for('acct_updatesuccess'))
     else:
        msg = 'Incorrect Password'
    return render_template('Staff_updateselfpass.html', form=update_user_form, msg=msg)


# New Features (Account Manage) -- Ian
# Forgot Password
@app.route('/Acctforgotpass', methods=['GET', 'POST'])
def acct_forgotpass():
    msg = ''
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['acctrecoveryattempt'] >= 3:
            try:
                session['acctrecblktime']
            except:
                curtime = datetime.now()
                blktill = curtime + timedelta(minutes=1)    # Block For 1 Minutes
                session['acctrecblktime'] = blktill       # Block Attempts Till This Time
            timeremain = str(session['acctrecblktime'] - datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('acctrecblktime', None)
                msg = ''
                session['acctrecoveryattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called loginattempt
        session['acctrecoveryattempt'] = 0

    check_user_form = Memforgotpassword(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and check_user_form.validate() and session['acctrecoveryattempt'] != 3:
        useremail = check_user_form.email.data.lower()
        cursor.execute('SELECT * FROM account WHERE email = %s', (useremail ,))
        account = cursor.fetchone()
        if account:
            session['OTP'] = generate_otp('email', account['email'])
            session['acctrecoveremail'] = account['email']
            session.pop('acctrecoveryattempt', None)
            return redirect(url_for('acctenter_otp', email=email))
        else:
            print("Account Not Found")
            session['acctrecoveryattempt'] = session['acctrecoveryattempt'] + 1
            return redirect(url_for('acct_forgotpass'))
    return render_template('Account_ForgotPassword.html', form=check_user_form, msg=msg)


# Forgot Account
@app.route('/acctforgotacct', methods=['GET', 'POST'])
def acct_forgotacct():
    msg = ''
    try:    # Check If There's A Login Attempt Session In Place
        # At 3 Attempt
        if session['acctrecoveryattempt'] >= 3:
            try:
                session['acctrecblktime']
            except:
                curtime = datetime.now()
                blktill = curtime + timedelta(minutes=1)    # Block For 1 Minutes
                session['acctrecblktime'] = blktill       # Block Attempts Till This Time
            timeremain = str(session['acctrecblktime'] - datetime.now())       # Calculate Time Remaining
            timeremain = timeremain[2:7]    # Only Retrieve Minute and seconds
            if timeremain == ' day,':       # If Block Time Is Up
                session.pop('acctrecblktime', None)
                msg = ''
                session['acctrecoveryattempt'] = 0   # To Unblock User
            else:
                msg = 'Looks like you are trying too much, try again in ' + timeremain
    except:     # Create A New Session called loginattempt
        session['acctrecoveryattempt'] = 0

    check_user_form = Memforgotaccount(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and check_user_form.validate() and session['acctrecoveryattempt'] != 3:
        cursor.execute('SELECT * FROM account WHERE phone_num = %s', (check_user_form.phone_number.data,))
        account = cursor.fetchone()
        if account:
            session['acctrecoveremail'] = account['email']       # Put Email In A Session For Use Later
            session['acctrecoverphone'] = check_user_form.phone_number.data
            cursor.execute('SELECT * FROM security_qn WHERE email = %s', ([account['email']],))
            checkgotpic = cursor.fetchone()
            if checkgotpic is None:
                session['OTP'] = generate_otp('phone', str('+65' + session['acctrecoverphone']))
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
    check_user_form = EnterOTP(request.form)
    msg = ''
    if request.method == 'POST' and check_user_form.validate():
        if int(check_user_form.OTP.data) == int(session['OTP']):
            session.pop('OTP', None)
            return redirect(url_for('Change_Acct_Password'))
        else:
            msg = "Incorrect OTP"
    return render_template('Account_ForgotPassOTP.html', form=check_user_form, msg=msg)

# Resent Email OTP (For Forgot Password)
@app.route('/acctresentemailotp', methods=['GET', 'POST'])
def acctresentemail_otp():
    session.pop('OTP', None)
    session['OTP'] = generate_otp('email', session['EmailOTP'])
    return redirect(url_for('mementer_otp'))


# Enter SMS OTP: (For Forgot Account)
@app.route('/acctforgotacctotp', methods=['GET', 'POST'])
def forgotacctenter_otp():
    check_user_form = EnterOTP(request.form)
    msg = ''
    if request.method == 'POST' and check_user_form.validate():
        if int(check_user_form.OTP.data) == int(session['OTP']):
            session.pop('OTP', None)
            return redirect(url_for('forgotacctshow'))
        else:
            msg = "Incorrect OTP"
    return render_template('Account_ForgotAccountOTP.html', form=check_user_form, msg=msg)


# Resent Phone OTP (For Forgot Account)
@app.route('/acctresentsmsotp', methods=['GET', 'POST'])
def acctresentsms_otp():
    session.pop('OTP', None)
    session['OTP'] = generate_otp('phone', str('+65' + session['acctrecoverphone']))
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
    update_user_form = ChangeMemberPassword(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST' and update_user_form.validate():
        #Check If Password Has Been Used Before
        cursor.execute('SELECT * FROM password_hist WHERE email = %s', (session['acctrecoveremail'],))
        pwdhist = cursor.fetchall()
        if pwdhist:
            state = ''
            for a in pwdhist:
                if a['password'] == update_user_form.newpassword.data:
                    msg = ' This Password Has Been Used'
                    state = "used"
                    break
            if state != 'used':
                if len(pwdhist) >= 2:
                    firstocc = pwdhist[0].get('serial_no')
                    cursor.execute('DELETE FROM password_hist WHERE serial_no = %s', [firstocc])
                    mysql.connection.commit()
                curdate = date.today()   # Get Today's date
                expiry_date = curdate + timedelta(days=90)
                pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
                cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s, account_status = NULL WHERE email = %s', (update_user_form.newpassword.data, pwd_expiry, session['acctrecoveremail'],))   # Update SQL To New Password That User Entered and Unlock User Account If Locked
                # Store Password
                cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (session['acctrecoveremail'], update_user_form.newpassword.data))
                mysql.connection.commit()
                session.pop('acctrecoveremail', None)
                return redirect(url_for('acct_updatesuccess'))
        else:
            curdate = date.today()   # Get Today's date
            expiry_date = curdate + timedelta(days=90)
            pwd_expiry = expiry_date.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
            cursor.execute('UPDATE account SET password = %s, pwd_expiry = %s, account_status = NULL WHERE email = %s', (update_user_form.newpassword.data, pwd_expiry, session['acctrecoveremail'],))   # Update SQL To New Password That User Entered and Unlock User Account If Locked
            # Store Password
            cursor.execute('INSERT INTO password_hist VALUES (NULL, %s, %s)', (session['acctrecoveremail'], update_user_form.newpassword.data))
            mysql.connection.commit()
            session.pop('acctrecoveremail', None)
            return redirect(url_for('acct_updatesuccess'))

    return render_template('Account_ChangePassword.html', form=update_user_form, msg=msg)


@app.route('/Acctforgotacctsecqn', methods=['GET', 'POST'])
def acctsecqn():
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
        session['OTP'] = generate_otp('phone', str('+65' + session['acctrecoverphone']))
        return redirect(url_for('forgotacctenter_otp'))
    if request.method == 'POST' and check_user_form.validate():
        if check_user_form.secpic.data == answer:       # If Option That User Has Choosen Matches The One In The Account Recovery
             return redirect(url_for('forgotacctshow'))
        else:
            session['choosesecpicattempt'] = session['choosesecpicattempt'] + 1
    return render_template('Account_ForgotAcctsecqn.html', form=check_user_form, question=question, msg=msg)


# Upload Their Fav Pic
@app.route('/Acctsecfavpic', methods=['GET', 'POST'])
def acctsecfavpic():
    upload_form = uploadfavpic(request.form)
    msg = ""
    if request.method == 'POST':
        fileuploaded1 = request.files[upload_form.pic1.name].read()    # Get Image 1 In Pure Data Format
        fileuploaded2 = request.files[upload_form.pic2.name].read()    # Get Image 2 In Pure Data Format
        fileuploaded3 = request.files[upload_form.pic3.name].read()    # Get Image 3 In Pure Data Format
        fileuploaded4 = request.files[upload_form.pic4.name].read()    # Get Image 4 In Pure Data Format
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if session['stafflogged'] is None:  # Using member Page
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
            return redirect(url_for('referral', state = " "))
        else:   # Using Staff Page
            cursor.execute('SELECT * FROM account WHERE full_name = %s', ([session['stafflogged']]))
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
    return render_template('Account_UploadFavPic.html', form=upload_form, msg=msg)

# Exception Handling For Uploading Files
@app.errorhandler(413)
@app.errorhandler(RequestEntityTooLarge)
def app_handle_413(e):
    return redirect(url_for('acctsecfavpic'))


def generate_otp(method, numemail):
    otp = random.randint(100000, 999999)
    if method == 'email':
        msg = Message('OTP Forgot Password', sender='piquant.nyp@gmail.com', recipients=[numemail])
        msg.body = str('This Is Your OTP {}' .format(otp))
        mail.send(msg)
    elif method == 'phone':
        message = twilioclient.messages \
        .create(
             body= str('This Is Your OTP {}' .format(otp)),
             from_='',
             to = numemail
         )
    return otp


# Extra, Shutdown Server
@app.route('/shutdown', methods=['GET'])
def shutdown():
    shutdown_server()
    return redirect(url_for('home'))

def shutdown_server():
    check = request.environ.get('werkzeug.server.shutdown')
    check()

if __name__ == '__main__':
    app.run(debug=True)
