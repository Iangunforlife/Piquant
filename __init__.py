from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from forms import *
import shelve, addorder, tablenumgenerate, logging, Member_Completion
from datetime import date
import datetime, csv
from handler import error
from functools import wraps # don't need to pip install
import splunklib.client as client # pip install splunk-sdk

app = Flask(__name__)
# for sql
app.register_blueprint(error)
app.secret_key = 'lol'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Iaminmumbai22'
app.config['MYSQL_DB'] = 'piquant'
mysql = MySQL(app)

logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s:%(pathname)s:%(name)s:%(message)s')
file_handler = logging.FileHandler('piquant.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

#for splunk
service = client.connect(
    host='localhost',
    port=8089,
    username='admin',
    password='Iaminmumbai21!'
)

# Role-Based Access Control
# only manager can update and delete user
# staff could only retrieve reservation and update their own profile


def man(manager):
    @wraps(manager)
    def wrap(staff_name, *args, **kwargs):
        i = 0
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if 'loggedIn' in session:
            cursor.execute('SELECT * FROM account WHERE manager_id IS NOT NULL')
            account = cursor.fetchone()
            if account:
                session['loggedIn'] = True
                session['manager_id'] = account['manager_id']
                if account['manager_id']:
                    return manager(staff_name, *args, **kwargs)
        else:
            i += 1
            cursor.execute('UPDATE suspicious SET suspicious = %s', (i, ))
            mysql.connection.commit()
            return render_template('error.html')

    return wrap

def role(staff):
    @wraps(staff)
    def wrap(staff_name, *args, **kwargs):
        i = 0
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if 'loggedIn' in session:
            cursor.execute('SELECT * FROM account WHERE staff_id IS NOT NULL')
            account = cursor.fetchone()
            if account:
                session['loggedIn'] = True
                session['staff_id'] = account['staff_id']

                if account['staff_id']:
                    return staff(staff_name, *args, **kwargs)
        else:
            i += 1
            cursor.execute('UPDATE suspicious SET suspicious = %s', (i, ))
            mysql.connection.commit()
            return render_template('error.html')
    return wrap

def mem(member):
    @wraps(member)
    def wrap(email, *args, **kwargs):
        i = 0
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if 'loggedIn' in session:
            cursor.execute('SELECT * FROM account WHERE email IS NOT NULL')
            account = cursor.fetchone()
            if account:
                session['loggedIn'] = True
                session['email'] = account['email']
                session['full_name'] = account['full_name']
                if account['email']:
                    return member(email, *args, **kwargs)
        else:
            i += 1
            cursor.execute('UPDATE suspicious SET suspicious = %s', (i, ))
            mysql.connection.commit()
            return render_template('error.html')
    return wrap


#Email To Be Passed into codes to check wether users are login or not
@app.route('/')
def home():
    return render_template('home.html', email=' ')

@app.route('/memhome/<email>')
@mem
def mem_home(email):
    if 'loggedIn' in session:
        return render_template('home.html', email=session['email'])
    return redirect(url_for('member_login', email=' '))

@app.route('/about/')
def about():
    return render_template('about.html', email=' ')

@app.route('/about/<email>')
@mem
def mem_about(email):
    if 'loggedIn' in session:
        return render_template('about.html', email=email)
    return render_template('about.html', email=' ')

# Customer Pages
@app.route('/Reservation/<email>', methods=['GET','POST'])
def create_user(email):
    create_user_form = ReservationForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE email = %s', [email])       # Look For Account Information
    account = cursor.fetchone()
    if request.method == 'POST' and create_user_form.validate():
        cursor.execute('INSERT INTO reservation VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (create_user_form.full_name.data, create_user_form.email.data, create_user_form.phone_number.data, create_user_form.date.data,create_user_form.time.data,create_user_form.card_name.data,create_user_form.cn.data,str(create_user_form.expire.data + '-01'),create_user_form.cvv.data,create_user_form.Additional_note.data))
        # add in update user action here
        mysql.connection.commit()   #Update SQL Database
        logger.info('{} has made a reservation'.format(create_user_form.full_name.data))
        return redirect(url_for('retrieve_users', email=email))
    if 'loggedIn' in session:     # Pre Fill Form if user is logged in
        create_user_form.full_name.data = account['full_name']
        create_user_form.email.data = account['email']
        create_user_form.phone_number.data = account['phone_num']
        if request.method == 'POST' and create_user_form.validate():
            # add in update user action here
            # put mysql.connection.commit here
            logger.info('{} has made a reservation'.format(session['full_name']))
            return redirect(url_for('retrieve_users', email=session['email']))
    return render_template('Reservation.html', form=create_user_form, email=email)


@app.route('/Confirmation/<email>/')
def retrieve_users(email):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation')
    users_list = cursor.fetchall()  # Get everything in reservation
    getuser = users_list[-1]    # Get Most Recent Record Only
    return render_template('Reservation_Confirmation.html', count=len(users_list), get_user=getuser, email=email)


@app.route('/thanks/<email>')
def number(email):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation')
    users_list = cursor.fetchall()
    reservationid = users_list[-1].get('reservation_id')
    return render_template('Reservation_thanks.html', email=email, reservationid=reservationid)


# Ian
@app.route('/onlineorder/<email>')
@mem
def orderpage1(email):
    table_dict = {}
    db = shelve.open('storage.db', 'c')
    try:
        table_dict = db['Tablenum']
    except:
        print("Error In Storage.db")

    if len(table_dict) == 0:
        table = tablenumgenerate.tablenumgen() #Create Class
        table_dict["1"] = table  #STORE CLASS IN DICT
        db['Tablenum'] = table_dict #STORE DICT IN SHELVE
        tablenum = table_dict.get("1").get_tablenum()  #GET TABLE NUM FROM DICT THEN GET TABLENUM FROM SHELVE
    else:
        tablenum = table_dict.get("1").get_tablenum()  #GET TABLE NUM FROM DICT THEN GET TABLENUM FROM SHELVE

    return render_template('Menu_OrderPage.html', tablenum=tablenum, email=email)

@app.route('/addingorder/<orderitem>/<tablenum>/<email>')
@mem
def addingorder(orderitem, tablenum, email):
    order_dict = {}
    db = shelve.open('storage.db', 'c')
    try:
        order_dict = db['Order']
        print("hi")
    except:
        print("Wrong")

    try:
        order_dict.get(tablenum)
        item = order_dict[tablenum]
        item.add_order(orderitem)
        order_dict[tablenum] = item
        db['Order'] = order_dict
        print(item.get_order(), "was stored in storage.db successfully with tablenum =", item.get_tablenum())
    except:
        table = addorder.addorder(tablenum)
        table.add_order(orderitem)
        order_dict[table.get_tablenum()] = table
        db['Order'] = order_dict
        print(table.get_order(), "was stored in storage.db successfully with tablenum =", table.get_tablenum())

    # add in update user action here
    # put mysql.connection.commit here
    logger.info('{} added {} to cart'.format(session['full_name'], orderitem))
    db.close()
    return redirect(url_for('orderpage1', email=email))


@app.route('/cart/<tablenum>/<email>')
@mem
def cart(tablenum, email):
    get_order_dict = {}
    db = shelve.open('storage.db', 'r')
    get_order_dict = db['Order']
    db.close()

    order_listdict = [] #Order From THAT Tables
    total = 0

    order = get_order_dict.get(tablenum)
    order_listdict.append(order)   #Order From All The Tables
    for tableorderitem in order_listdict:  #Individual Table Order Item (Stored Whole Class into Shelve)
        total = tableorderitem.get_price()

    ptablenum = tablenum #SO THAT TABLENUM CAN TO RENDER TEMPLATE
    print(ptablenum)
    db.close()
    # add in update user action here
    # put mysql.connection.commit here
    logger.info('{} viewed cart items'.format(session['full_name']))
    return render_template('Menu_Cartpage.html', order_listdict=order_listdict, total=total, tablenum=ptablenum, email=email)


@app.route('/deleteitem/<deleteitem>/<tablenum>/<email>')
@mem
def deleteitem(deleteitem, tablenum, email):
    del_order_dict = {}
    db = shelve.open('storage.db', 'w')
    del_order_dict = db['Order']

    gettablenum = del_order_dict.get(tablenum) #Get Order (As A Whole Class) from tablenum provided
    gettablenum.delete_order(deleteitem)
    del_order_dict[tablenum] = gettablenum
    db['Order'] = del_order_dict
    db.close()
    # add in update user action here
    # put mysql.connection.commit here
    logger.info('{} deleted order item'.format(session['full_name']))

    return redirect(url_for('cart', tablenum=tablenum, email=email))

@app.route('/submit/<email>')
@mem
def submit(email):
    return render_template('Menu_Submit.html', email=email)

#Akif
# Create User
@app.route('/createMember/<email>', methods=['GET', 'POST'])
@mem
def create_Member(email):
    msg = ''
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        signupdate = date.today()   # Get Today's date
        newdate = signupdate.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
        login_time = datetime.datetime.now().replace(microsecond=0)
        date_time = datetime.datetime(2021, 12, 31)
        exp_date = date_time.strftime("%Y-%m-%d")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s and full_name = %s', (create_user_form.email.data, create_user_form.full_name.data,))
        account = cursor.fetchone()

        if account:     # Ensure That there will be no duplicates (As Email is A Primary Key In The Database)
            msg = 'This Email Has Been Taken'

        else:
            cursor.execute('INSERT INTO account VALUES (%s, %s,NULL,NULL, %s, NULL, %s ,%s, %s, %s, %s, %s, NULL, NULL, NULL, NULL)', (create_user_form.email.data, create_user_form.full_name.data, create_user_form.password.data,'Valid', 'Member',  create_user_form.phone_number.data , "Regular", "1/5", newdate,))
            cursor.execute('SELECT * FROM account WHERE email = %s and full_name = %s', (create_user_form.email.data, create_user_form.full_name.data,))
            cursor.execute('UPDATE account SET sign_up_date= %s WHERE email = %s and full_name = %s', (newdate,create_user_form.email.data, create_user_form.full_name.data,))
            logger.info('{} signed up as member'.format(create_user_form.full_name.data))
            mysql.connection.commit()
            session['loggedIn'] = True
            session['email'] = create_user_form.email.data
            return redirect(url_for('mem_home'))

    return render_template('Member_createUser.html', form=create_user_form, email=email, msg=msg)


# Login
@app.route('/Memberlogin/', methods=['GET', 'POST'])
def member_login():
    msg = ''
    i = 0
    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s', (check_user_form.email.data,))
        account = cursor.fetchone()
        if account:     # If Account Exist In DataBase
            session['loggedIn'] = True
            session['email'] = account['email']
            session['full_name'] = account['full_name']
            now = str(datetime.datetime.now().replace(microsecond=0))
            logger.info('{} is logged in'.format(session['full_name']))
            mysql.connection.commit()
            return redirect(url_for('mem_home', email=session['email']))
        else:
            i += 1
            cursor.execute('UPDATE audit SET failed_login = %s WHERE email = %s', (i, check_user_form.email.data,))
            mysql.connection.commit()
            msg = "Incorrect Username/Password"

    # Return Incorrect Username/Password as a message
    return render_template('Member_login.html', form=check_user_form, msg=msg, email='')


# Referral

@app.route('/referral/<email>/<state>', methods=['GET', 'POST'])
@mem
def referral(email, state):
    claim_form = ClaimCode(request.form)
    # For Show Completion Part
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE email = %s', (email,))        # From Pratical wk 4 line 101, To Change To Session
    account = cursor.fetchone()

    #For Claiming Codes
    if request.method == 'POST' and claim_form.validate():
        check = ''
        cursor.execute('SELECT * FROM rewards ')
        code_list = cursor.fetchall()       # Get all Codes From Database
        for a in code_list:
            if a['reward_code'] == claim_form.claim_code.data:
                if a['status'] == "Claimed":       # Check Status
                     check = "used"     # Return Variable To Let Webapge Know That The Code is Used
                else:
                    check = "claim"
                    cursor.execute('UPDATE rewards SET status = %s WHERE reward_code = %s', ('Claimed', a['reward_code'],))  # Update Status To Update
                    mysql.connection.commit()

        if check == "used":     #Shows if code has been claimed before
            cursor.execute('UPDATE audit SET action = %s', ('Used referral code',))
            logger.info('{} used referral code {}'.format(email, claim_form.claim_code.data))
            mysql.connection.commit()
            return redirect(url_for('referral', email=email, state="used"))
        elif check == "claim":
            newreward = Member_Completion.increase_completion(account['member_level'], account['member_completion'])     # Increase Completion Using Function
            cursor.execute('UPDATE account SET member_level = %s, member_completion = %s WHERE email = %s', (newreward[0], newreward[1], email,))
            logger.info('{} claimed referral code {}'.format(email, claim_form.claim_code.data))
            mysql.connection.commit()
            return redirect(url_for('referral', email=email, state="claim"))
        else:
            return redirect(url_for('referral', email=email, state=" "))
    return render_template('Member_referral.html', email=email, form=claim_form, user=account, state=state)


@app.route('/membersucess/<email>')
@mem
def member_updatesucess(email):
    return render_template('Member_Selfupdatesuccess.html', email=email)


#Update Member (For Customers)
@app.route('/updateMember/<email>/', methods=['GET', 'POST'])
@mem
def update_member(email):
    update_user_form = UpdatememberdetailForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        cursor.execute('SELECT * FROM account WHERE email = %s', (update_user_form.email.data,))
        account = cursor.fetchone()     # Fetch Only 1 SQL Record (Since Email Is A Primary Key, There Should Be Only 1 Record)
        if email != account['email']:   # Check Wether Database has this email or not
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, email,))
            logger.info('{} updated self profile'.format(email))
            mysql.connection.commit()
            return redirect(url_for('member_updatesucess', email=email))
    else:   # Pre Fill Information in the form
        cursor.execute('SELECT * FROM account WHERE email = %s', (email,))
        account = cursor.fetchone()
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
        logger.info('{} updated self profile'.format(email))
        mysql.connection.commit()
    return render_template('Member_updateself.html', form=update_user_form, email=email, msg=msg)

@app.route('/updateMemberpass/<email>/', methods=['GET', 'POST'])
@mem
def update_memberpass(email):
     update_user_form = ChangePasswordForm(request.form)
     msg = ''
     if request.method == 'POST' and update_user_form.validate():
         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
         cursor.execute('SELECT * FROM account WHERE email = %s', (email,))
         account = cursor.fetchone()
         if update_user_form.oldpassword.data == account['password']:   # Check If Old Password Entered Is The Same One Entered By The User
             cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, email,))   # Update SQL To New Password That User Entered
             logger.info("{} updated password".format(email))
             mysql.connection.commit()
             return redirect(url_for('member_updatesucess', email=email))
         else:
             msg = 'Incorrect Password'
     return render_template('Member_updateselfpass.html', form=update_user_form, email=email, msg=msg)

#Staff Pages
@app.route('/Stafflogin/', methods=['GET','POST'])
def checkstaff():
    check_user_form = LoginForm(request.form)
    msg = ''
    i = 0
    if request.method == 'POST' and check_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:
            login = str(datetime.datetime.now().replace(microsecond=0))
            # Only allow access if staff_id field in the account has information in it (If An Account is a member, The Staff_id field would not be filled up)

            if account['manager_id'] == account['staff_id']:
                session['loggedIn'] = True
                session['manager_id'] = account['manager_id']
                session['email'] = account['email']
                logger.info("{} is logged in".format(account['manager_id']))
                cursor.execute('UPDATE audit SET action = %s, login_time = %s WHERE manager_id = %s', ('Logged in', login, account['manager_id'],))
                mysql.connection.commit()
                return redirect(url_for('manpage', staff_name=account['manager_id']))
            else:
                session['loggedIn'] = True
                session['staff_id'] = account['staff_id']
                session['email'] = account['email']
                logger.info("{} is logged in".format(account['staff_id']))

                cursor.execute('UPDATE audit SET action = %s, login_time = %s WHERE email = %s ', ('Logged in', login, account['email'],))
                mysql.connection.commit()
                return redirect(url_for('staffpage', staff_name=account['staff_id']))
        else:
            i += 1
            cursor.execute('UPDATE audit SET failed_login = %s WHERE email = %s', (i, check_user_form.email.data,))
            mysql.connection.commit()
            msg = "Incorrect Username/Password"
    return render_template('Staff_login.html', form=check_user_form, msg=msg)

@app.route('/Staffpage/<staff_name>')
@role
def staffpage(staff_name):
    if 'loggedIn' in session:
        return render_template('Staff_Page.html', staff_name=staff_name)
    return redirect(url_for('checkstaff'))

@app.route('/Managerpage/<staff_name>/')
@man
def manpage(staff_name):
    if 'loggedIn' in session:
        return render_template('Manager_Page.html', staff_name=staff_name)
    return redirect(url_for('checkstaff'))

#Reservation Form (Joel And Ernest)
@app.route('/retrieveReservation/<staff_name>')
@role
@man
def retrieve(staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM reservation')
        users_list = cursor.fetchall()     # Retrieve All Reservation
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Retrieved reservation', staff_name))
        logger.info("{} retrieved reservation".format(staff_name))
        mysql.connection.commit()
        return render_template('Reservation_retrieveUser.html', count=len(users_list), users_list=users_list, staff_name=staff_name)
    return redirect(url_for('checkstaff'))

@app.route('/updateUser/<staff_name>/', methods=['GET', 'POST'])
@role
@man
def update_user(staff_name):
    if 'loggedIn' in session:
        update_user_form = ReservationForm(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM reservation WHERE reservation_id = %s', id)       # Get Entire Row That Contains The Reservation ID
        account = cursor.fetchone()
        if request.method == 'POST' and update_user_form.validate():
            cursor.execute('UPDATE reservation SET full_name= %s, email = %s, phone_num= %s, reservation_date= %s, reservation_time= %s, card_name= %s, card_number= %s, expiry_date= %s, cvv= %s, additional_note= %s WHERE reservation_id = %s', (update_user_form.full_name.data, update_user_form.email.data, update_user_form.phone_number.data, update_user_form.date.data, update_user_form.time.data, update_user_form.card_name.data, update_user_form.cn.data,str(update_user_form.expire.data + '-01'), update_user_form.cvv.data, update_user_form.Additional_note.data, id))
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Updated reservation', staff_name,))
            logger.info("{} updated reservation".format(staff_name))
            mysql.connection.commit()
            return redirect(url_for('retrieve', staff_name=staff_name))
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
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Created reservation', staff_name,))
            logger.info("{} created reservation".format(staff_name))
            mysql.connection.commit()
        return render_template('Reservation_updateUser.html', form=update_user_form, staff_name=staff_name)
    return redirect(url_for('checkstaff'))

#delete reservation
@app.route('/deleteUser/<staff_name>/', methods=['POST'])
@role
@man
def delete_user(staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM reservation WHERE reservation_id = %s ', [id])
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s', ('Deleted reservation', staff_name,))
        logger.info("{} deleted reservation".format(staff_name))
        mysql.connection.commit()
        return redirect(url_for('retrieve', staff_name=staff_name))
    return redirect(url_for('checkstaff'))

#Menu Page (Ian)
@app.route('/changetable/<state>')
def changetable(state):
    if 'loggedIn' in session:
        table_dict = []
        db = shelve.open('storage.db', 'w')
        table_dict = db['Tablenum']

        currenttable = table_dict.get("1") # Since Tablenumgenrate is stored in dict with key 1
        if state == "T":
            newtablenum = currenttable.get_tablenum() + 1
        elif state == "F":
            if currenttable.get_tablenum() > 1:
                newtablenum = currenttable.get_tablenum() - 1
            else:
                newtablenum = currenttable.get_tablenum()
        currenttable.set_tablenum(newtablenum)
        table_dict["1"] = currenttable
        db['Tablenum'] = table_dict

        db.close()
        return redirect(url_for('orderpage1', email=' '))
    return redirect(url_for('checkstaff'))

@app.route('/orderpage_staff/<staff_name>')
@role
@man
def orderpagestaff(staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Viewed order', staff_name,))
        logger.info("{} viewed order".format(staff_name))
        mysql.connection.commit()
        get_order_dict = {}
        db = shelve.open('storage.db', 'r')
        get_order_dict = db['Order']
        table_dict = db['Tablenum']
        db.close()

        order_listdict = [] #Order From All Tables
        currenttable = table_dict.get("1").get_tablenum()

        for tables in get_order_dict:
            order = get_order_dict.get(tables)
            check = 0
            for a in order.get_order():
                if order.get_order().get(a) > 0:
                    check = 1
                    break
                else:
                    continue
            if check == 1:
                order_listdict.append(order)   #Order From All The Tables

        return render_template('Menu_Stafforderpage.html', order_listdict=order_listdict, currenttable=currenttable, staff_name=staff_name)
    return redirect(url_for('checkstaff'))
# Ian Table
@app.route('/staffdeleteitem/<deleteitem>/<tablenum>/<staff_name>')
@role
@man
def staffdeleteitem(deleteitem, tablenum, staff_name):
   if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        del_order_dict = {}
        db = shelve.open('storage.db', 'w')
        del_order_dict = db['Order']
        gettablenum = del_order_dict.get(tablenum) #Get Order (As A Whole Class) from tablenum provided
        gettablenum.delete_order(deleteitem)
        del_order_dict[tablenum] = gettablenum
        db['Order'] = del_order_dict
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted order item', staff_name,))
        logger.info("{} deleted order item".format(staff_name))
        mysql.connection.commit()
        db.close()

        return redirect(url_for('orderpagestaff', staff_name=staff_name))
   return redirect(url_for('checkstaff'))

#Akif
# Retrieve Member
@app.route('/retrieveMembers/<staff_name>')
@man
def retrieve_Members(staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account where member_level is not null ')     # Get Only Members (Staff has no member Level (AKA NULL value), Therefore, it won't be displayed'
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Retrieved members', staff_name,))
        logger.info("{} retrieved members".format(staff_name))
        mysql.connection.commit()
        users_list = cursor.fetchall()
        return render_template('Member_retrieveUsers.html', count=len(users_list), users_list=users_list , staff_name=staff_name)
    return redirect(url_for('checkstaff'))

# Update Member for Staff
@app.route('/updateMemberstaff/<email>/<staff_name>', methods=['GET', 'POST'])
@man
def update_memberstaff(email, staff_name):
    if 'loggedIn' in session:
        update_user_form = UpdatememberdetailstaffForm(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        msg = ''
        if request.method == 'POST' and update_user_form.validate():
            cursor.execute('SELECT * FROM account WHERE email = %s', (update_user_form.email.data,))
            account = cursor.fetchone()
            if email != account['email']:   # Do Not Allow Change Of Email if The Email Address Entered Is Found In The Database
                msg = "This Email Has Been Used"
            else:
                cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, sign_up_date = %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.signup_date.data, email,))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated member', staff_name,))
                logger.info("{} updated member".format(staff_name))
                mysql.connection.commit()
                return redirect(url_for('retrieve_Members', staff_name=staff_name))
        else:   # Pre Fill Form
            cursor.execute('SELECT * FROM account WHERE email = %s', (email,))
            account = cursor.fetchone()
            update_user_form.full_name.data = account['full_name']
            update_user_form.email.data = account['email']
            update_user_form.phone_number.data = account['phone_num']
            update_user_form.signup_date.data = account['sign_up_date']

        return render_template('Member_updateUser.html', form=update_user_form, staff_name=staff_name, msg=msg)
    return redirect(url_for('checkstaff'))

# Delete Member
@app.route('/deleteMember/<mememail>/<staff_name>', methods=['POST'])
@man
def delete_Member(mememail, staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM account WHERE email = %s ', [mememail])
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted member', staff_name,))
        logger.info("{} deleted member".format(staff_name))
        mysql.connection.commit()
        return redirect(url_for('retrieve_Members', staff_name=staff_name))
    return redirect(url_for('checkstaff'))
#Referal Codes
@app.route('/Referalcodes/<staff_name>', methods=['GET','POST'])
@role
@man
def referal_codes(staff_name):
    if 'loggedIn' in session:
        createcode = CreateCode(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM rewards ')
        code_list = cursor.fetchall()
        if request.method == 'POST' and createcode.validate():
            cursor.execute('SELECT * FROM rewards WHERE reward_code = %s', (createcode.code.data,))
            code = cursor.fetchone()
            if code:    # Do Not Allow Duplicated Codes (By Checking if code number exist in the database)
                msg = 'This Code Exist In Database'
            else:
                cursor.execute('INSERT INTO rewards VALUES (%s, %s)', (createcode.code.data, 'Unclaimed'))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Created referral code', staff_name,))
                logger.info("{} created referral code".format(staff_name))
                mysql.connection.commit()
                return redirect(url_for('referal_codes', staff_name=staff_name))

        return render_template('Member_StaffReferalCodes.html', form=createcode, count=len(code_list), code_list=code_list, staff_name=staff_name)
    return redirect(url_for('checkstaff'))

#Delete Referal Codes
@app.route('/deleteReferal/<codenum>/<staff_name>', methods=['GET', 'POST'])
@role
@man
def delete_code(codenum,staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM rewards WHERE reward_code = %s ', ([codenum]))
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted referral code', staff_name,))
        logger.info("{} deleted referral code".format(staff_name))
        mysql.connection.commit()
        return redirect(url_for('referal_codes', staff_name=staff_name))
    return redirect(url_for('checkstaff'))
#Create Staff User
@app.route('/CreateStaff/<staff_name>/', methods=['GET','POST'])
@man
def create_staff(staff_name):
    if 'loggedIn' in session:
        create_user_form = CreateStaff(request.form)
        if request.method == 'POST' and create_user_form.validate():
            hire_date = date.today()    # Get Today's Date
            newdate = hire_date.strftime("%Y-%m-%d")    # To Format Date Into SQL Readable Format (YYYY-MM-DD)
            login_time = datetime.datetime.now().replace(microsecond=0)
            date_time = datetime.datetime(2021, 12, 31)
            exp_date = date_time.strftime("%Y-%m-%d")
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM account WHERE staff_id = %s AND manager_id = staff_id', (staff_name,))
            account = cursor.fetchone()

            if account:
                msg = 'This Email Has Been Taken'
                return redirect(url_for('create_staff', msg=msg))
            else:
                if account['manager_id'] != None:
                    cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, NULL, NULL, NULL, %s, NULL, %s, %s)', (create_user_form.email.data, create_user_form.full_name.data, create_user_form.password.data, 'Staff',  create_user_form.phone_number.data , create_user_form.staff_id.data, newdate, create_user_form.job_title.data,))
                    cursor.execute('INSERT INTO audit VALUES (%s, %s, NULL, %s, %s, NULL, %s, %s, %s, %s)', (create_user_form.email.data, create_user_form.staff_id, create_user_form.full_name, login_time, create_user_form.password.data, exp_date, 'Valid', 'No action',))
                    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Created new staff', staff_name,))
                    logger.info("{} created new staff".format(staff_name))
                    mysql.connection.commit()
                    return redirect(url_for('confirmstaff', email=email, staff_name=staff_name, newuser=create_user_form.email.data))
        return render_template('Staff_Create.html',form=create_user_form, staff_name=staff_name)
    return redirect(url_for('checkstaff'))

@app.route('/CreateManager/<staff_name>/', methods=['GET','POST'])
@man
def create_manager(staff_name):
    if 'loggedIn' in session:
        create_user_form = CreateManager(request.form)

        if request.method == 'POST' and create_user_form.validate():
            hire_date = date.today()    # Get Today's Date
            newdate = hire_date.strftime("%Y-%m-%d")    # To Format Date Into SQL Readable Format (YYYY-MM-DD)
            login_time = datetime.datetime.now().replace(microsecond=0)
            date_time = datetime.datetime(2021, 12, 31)
            exp_date = date_time.strftime("%Y-%m-%d")
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM account WHERE staff_id = %s AND staff_id = manager_id', (staff_name,))
            account = cursor.fetchone()

            if account:
                msg = 'This Email Has Been Taken'
                return redirect(url_for('create_staff', msg=msg))
            else:
                if account['manager_id'] != None:
                    cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, NULL, NULL, NULL, %s, NULL, %s, %s)', (create_user_form.email.data, create_user_form.full_name.data, create_user_form.password.data, 'Staff',  create_user_form.phone_number.data , create_user_form.staff_id.data, newdate, create_user_form.job_title.data,))
                    cursor.execute('INSERT INTO audit VALUES (%s, %s, %s, %s, %s, NULL, %s, %s, %s, %s)', (create_user_form.email.data, create_user_form.staff_id, create_user_form.manager_id, create_user_form.full_name, login_time, create_user_form.password.data, exp_date, 'Valid', 'No action',))
                    cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Created new manager', staff_name,))
                    logger.info("{} created new manager".format(staff_name))
                    mysql.connection.commit()
                    return redirect(url_for('confirmstaff', email=email, staff_name=staff_name, newuser=create_user_form.email.data))

        return render_template('manager_create.html', form=create_user_form, staff_name=staff_name)
    return redirect(url_for('checkstaff'))

@app.route('/confirmstaff/<staff_name>/<newuser>')
@man
def confirmstaff(staff_name, newuser):
    if 'loggedIn' in session:
        return render_template('Staff_Confirm.html', staff_name=staff_name, newuser=newuser)
    return redirect(url_for('checkstaff'))

@app.route('/staffRetrieve/<staff_name>', methods=['GET', 'POST'])
@man
def staffretrieve(staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account where staff_id is not null ')
        users_list = cursor.fetchall()
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Retrieved staff', staff_name,))
        logger.info("{} retrieved staff".format(staff_name))
        mysql.connection.commit()# Get Staff (Members will not be included as their staff_id is a null value)
        return render_template('Staff_Userslist.html', count=len(users_list), users_list=users_list, staff_name=staff_name)
    return redirect(url_for('checkstaff'))

@app.route('/updateMan/<staff_name>/', methods=['GET', 'POST'])
@man
def update_man(staff_name):     # toupdate Variable Is Used in a case where 1 staff Member is editing another Staff Member's Information). toupdate is the staff memeber's name
    if 'loggedIn' in session:
        update_user_form = UpdateManager(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE staff_id = %s', (staff_name, ))  # Get Staff Email based on the staff name entere
        staff = cursor.fetchone()
        msg = ''
        if request.method == 'POST' and update_user_form.validate():
            cursor.execute('SELECT * FROM account')
            account = cursor.fetchone()
            if staff == account:
                msg = "Please type in your info"
            else:
                cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, staff_id= %s, manager_id = %s, job_title= %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.staff_id.data, update_user_form.manager_id.data, update_user_form.job_title.data, staff['email'],))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self profile', staff_name,))
                logger.info("{} updated self profile".format(staff_name))
                mysql.connection.commit()
                if staff_name:
                    return redirect(url_for('staffpage', staff_name=update_user_form.full_name.data))

        else:
            cursor.execute('SELECT * FROM account WHERE staff_id = %s', (staff['staff_id'],))     # Get Account Information
            account = cursor.fetchone()
            update_user_form.full_name.data = account['full_name']
            update_user_form.email.data = account['email']
            update_user_form.phone_number.data = account['phone_num']
            update_user_form.staff_id.data = account['staff_id']
            update_user_form.manager_id.data = account['manager_id']
            update_user_form.job_title.data = account['job_title']
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self profile', staff_name,))
            logger.info("{} updated self profile".format(staff_name))

            mysql.connection.commit()

        return render_template('Man_updateuser.html', form=update_user_form, staff_name=account['staff_id'])
    return redirect(url_for('checkstaff'))




@app.route('/updateStaff/<staff_name>/', methods=['GET', 'POST'])
@man
def update_staff(staff_name):     # toupdate Variable Is Used in a case where 1 staff Member is editing another Staff Member's Information). toupdate is the staff memeber's name
    if 'loggedIn' in session:
        update_user_form = UpdateStaff(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE staff_id = %s', (staff_name, ))  # Get Staff Email based on the staff name entere
        staff = cursor.fetchone()
        msg = ''
        if request.method == 'POST' and update_user_form.validate():
            cursor.execute('SELECT * FROM account')
            account = cursor.fetchone()
            if staff == account:
                msg = "Please type in your info"
            else:
                cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, staff_id= %s, job_title= %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.staff_id.data, update_user_form.job_title.data, staff['email'],))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self profile', staff_name,))
                logger.info("{} updated self profile".format(staff_name))
                mysql.connection.commit()
                if staff_name:
                    return redirect(url_for('staffpage', staff_name=update_user_form.full_name.data))

        else:
            cursor.execute('SELECT * FROM account WHERE staff_id = %s', (staff['staff_id'],))     # Get Account Information
            account = cursor.fetchone()
            update_user_form.full_name.data = account['full_name']
            update_user_form.email.data = account['email']
            update_user_form.phone_number.data = account['phone_num']
            update_user_form.staff_id.data = account['staff_id']
            update_user_form.job_title.data = account['job_title']
            cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self profile', staff_name,))
            logger.info("{} updated self profile".format(staff_name))
            mysql.connection.commit()

        return render_template('Staff_updateuser.html', form=update_user_form, staff_name=account['staff_id'])
    return redirect(url_for('checkstaff'))

@app.route('/deleteStaff/<delstaffemail>/<staff_name>', methods=['POST'])
@man
def delete_staff(delstaffemail, staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('DELETE FROM account WHERE email = %s ', [delstaffemail])
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Deleted staff', staff_name,))
        logger.info("{} deleted staff {}".format(staff_name, delstaffemail))
        mysql.connection.commit()
        return redirect(url_for('staffretrieve', staff_name=staff_name))
    return redirect(url_for('checkstaff'))

@app.route('/updatemanpass/<staff_name>/', methods=['GET', 'POST'])
@man
def Changepass_man(staff_name):
    if 'loggedIn' in session:
        update_user_form = ChangePasswordForm(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE full_name = %s and staff_id is not NULL and manager_id is not NULL', (staff_name,))
        manager = cursor.fetchone()
        msg = ''
        if request.method == 'POST' and update_user_form.validate():
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM account WHERE email = %s', (manager['email'],))
            account = cursor.fetchone()
            if update_user_form.oldpassword.data == account['password']:   # Ensure Old Password Matches The Password That The User Entered
                cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, manager['email'],))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self password', staff_name,))
                logger.info("{} updated self password".format(staff_name))
                mysql.connection.commit()
                return redirect(url_for('member_updatesucess', email=' '))
            else:
                msg = 'Incorrect Password'
        return render_template('manager_selfupdatepass.html', form=update_user_form, staff_name=staff_name, msg=msg)
    return redirect(url_for('checkstaff'))

@app.route('/updatestaffpass/<staff_name>/', methods=['GET', 'POST'])
@role
def Changepass_staff(staff_name):
    if 'loggedIn' in session:
        update_user_form = ChangePasswordForm(request.form)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE full_name = %s and staff_id is not NULL', (staff_name,))
        staff = cursor.fetchone()
        msg = ''
        if request.method == 'POST' and update_user_form.validate():
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM account WHERE email = %s', (staff['email'],))
            account = cursor.fetchone()
            if update_user_form.oldpassword.data == account['password']:   # Ensure Old Password Matches The Password That The User Entered
                cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, staff['email'],))
                cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Updated self password', staff_name,))
                logger.info("{} updated self password".format(staff_name))
                mysql.connection.commit()
                return redirect(url_for('member_updatesucess', email=' '))
            else:
                msg = 'Incorrect Password'
        return render_template('Staff_updateselfpass.html', form=update_user_form, staff_name=staff_name, msg=msg)
    return redirect(url_for('checkstaff'))
# Error validation & auditing

@app.route('/logout/<staff_name>', methods=['GET'])
@role
@man
def logout(staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE staff_id = %s and staff_id is not null', (staff_name,))
        account = cursor.fetchone()
        print(account)
        if account:
            logout = str(datetime.datetime.now().replace(microsecond=0))
            if account['manager_id'] is not None:
                cursor.execute('UPDATE audit SET logout_time = %s, action= %s WHERE manager_id = %s', (logout,'Logged out', account['manager_id'],))
                logger.info("{} is logged out".format(staff_name))
                mysql.connection.commit()
                session.pop('loggedIn', None)
                session.pop('manager_id', None)

            else:
                cursor.execute('UPDATE audit SET logout_time = %s, action = %s WHERE staff_id = %s', (logout,'Logged out', account['staff_id'],))
                logger.info("{} is logged out".format(staff_name))
                mysql.connection.commit()
                session.pop('loggedIn', None)
                session.pop('staff_id', None)

            return redirect(url_for('home', email=''))
    return redirect(url_for('checkstaff'))


@app.route('/manaud/<staff_name>/', methods=['GET','POST'])
@man
def manager_audit(staff_name):
    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM audit WHERE staff_id is not null')
        audit = cursor.fetchall()
        cursor.execute('UPDATE audit SET action = %s WHERE staff_id = %s',('Viewed audit', staff_name,))
        logger.info("{} viewed audit".format(staff_name))
        mysql.connection.commit()
        with open('audit.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['manager_id','staff_id','usage','email','full_name','login_time','logout_time', 'action', 'failed_login', 'role', 'suspicious'])
            writer.writeheader()
            for i in audit:
                writer.writerow(i)
        f.close()
        return render_template('staff_audit_manager.html', staff_name=staff_name, audit=audit)
    return redirect(url_for('checkstaff'))


@app.route('/dashboard/<staff_name>/')
@man
def manager_dashboard(staff_name):
    return render_template('dashboard.html', staff_name=staff_name)


@app.route('/memlogout/<email>/', methods=['GET'])
@mem
def member_logout(email):

    if 'loggedIn' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s ', (email,))
        account = cursor.fetchone()

        if account:
            logout = str(datetime.datetime.now().replace(microsecond=0))
            cursor.execute('UPDATE audit SET logout_time = %s, action = %s ', (logout, 'Logged out'))
            logger.info("{} is logged out".format(session['full_name']))
            mysql.connection.commit()
            session.pop('loggedIn', None)
            session.pop('email', None)
    return redirect(url_for('member_login', email=' '))

if __name__ == '__main__':
    app.run(debug=True)
