from flask import Flask, render_template, request, redirect, url_for
from forms import *
import Member_Completion, shelve, addorder, tablenumgenerate
from datetime import date
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''   # Enter Your Own SQL Information
app.config['MYSQL_DB'] = 'piquant'  # Load Up piquant schema
mysql = MySQL(app)


#Email To Be Passed into codes to check wether users are login or not
@app.route('/')
def home():
    return render_template('home.html', email=" ")

@app.route('/home2/<email>')    # For Logged in Users, Another Home Page Will Be Loaded
def home2(email):
    return render_template('home.html', email=email)

@app.route('/about/<email>/')
def about(email):
    return render_template('about.html', email=email)

# Customer Pages
@app.route('/Reservation/<email>', methods=['GET','POST'])
def create_user(email):
    create_user_form = ReservationForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE email = %s', [email])       # Look For Account Information
    account = cursor.fetchone()
    if request.method == 'POST' and create_user_form.validate():
        cursor.execute('INSERT INTO reservation VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (create_user_form.full_name.data, create_user_form.email.data, create_user_form.phone_number.data, create_user_form.date.data,create_user_form.time.data,create_user_form.card_name.data,create_user_form.cn.data,str(create_user_form.expire.data + '-01'),create_user_form.cvv.data,create_user_form.Additional_note.data))
        mysql.connection.commit()   #Update SQL Database
        return redirect(url_for('retrieve_users', email=email))
    if account != None:     # Pre Fill Form if user is logged in
        create_user_form.full_name.data = account['full_name']
        create_user_form.email.data = account['email']
        create_user_form.phone_number.data = account['phone_num']
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

    db.close()
    return redirect(url_for('orderpage1', email=email))


@app.route('/cart/<tablenum>/<email>')
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
    return render_template('Menu_Cartpage.html', order_listdict=order_listdict, total=total, tablenum=ptablenum, email=email)


@app.route('/deleteitem/<deleteitem>/<tablenum>/<email>')
def deleteitem(deleteitem, tablenum, email):
    del_order_dict = {}
    db = shelve.open('storage.db', 'w')
    del_order_dict = db['Order']

    gettablenum = del_order_dict.get(tablenum) #Get Order (As A Whole Class) from tablenum provided
    gettablenum.delete_order(deleteitem)
    del_order_dict[tablenum] = gettablenum
    db['Order'] = del_order_dict
    db.close()

    return redirect(url_for('cart', tablenum=tablenum, email=email))

@app.route('/submit/<email>')
def submit(email):
    return render_template('Menu_Submit.html', email=email)


#Akif
# Create User
@app.route('/createMember/<email>', methods=['GET', 'POST'])
def create_Member(email):
    msg = ''
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        signupdate = date.today()   # Get Today's date
        newdate = signupdate.strftime("%Y-%m-%d")   # To Create New Date According To SQL Format
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s', (create_user_form.email.data,))
        account = cursor.fetchone()
        if account:     # Ensure That there will be no duplicates (As Email is A Primary Key In The Database)
            msg = 'This Email Has Been Taken'
        else:
            cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %7s, %s, %s, NULL, NULL, NULL)', (create_user_form.email.data, create_user_form.full_name.data, create_user_form.password.data, 'Member',  create_user_form.phone_number.data , "Regular", "1/5", newdate))
            mysql.connection.commit()
            return redirect(url_for('referral', email=create_user_form.email.data, state=" "))
    return render_template('Member_createUser.html', form=create_user_form, email=email, msg=msg)


# Login
@app.route('/Memberlogin/<email>', methods=['GET', 'POST'])
def member_login(email):
    msg = ''
    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:     # If Account Exist In DataBase
            return redirect(url_for('referral', email=account['email'], state=" "))
        else:
            msg = "Incorrect Username/Password"     # Return Incorrect Username/Password as a message
    return render_template('Member_login.html', form=check_user_form, email=email, msg=msg)


# Referral
@app.route('/referral/<email>/<state>', methods=['GET', 'POST'])
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
                    cursor.execute('UPDATE rewards SET status = %s WHERE reward_code = %s', ('Claimed', a['reward_code']))  # Update Status To Update
                    mysql.connection.commit()

        if check == "used":     #Shows if code has been claimed before
            return redirect(url_for('referral', email=email, state="used"))
        elif check == "claim":
            newreward = Member_Completion.increase_completion(account['member_level'], account['member_completion'])     # Increase Completion Using Function
            cursor.execute('UPDATE account SET member_level = %s, member_completion = %s WHERE email = %s', (newreward[0], newreward[1], email,))
            mysql.connection.commit()
            return redirect(url_for('referral', email=email, state="claim"))
        else:
            return redirect(url_for('referral', email=email, state="unclaimed"))
    return render_template('Member_referral.html', email=email, form=claim_form, user=account, state=state)

@app.route('/membersucess/<email>')
def member_updatesucess(email):
    return render_template('Member_Selfupdatesuccess.html', email=email)


#Update Member (For Customers)
@app.route('/updateMember/<email>/', methods=['GET', 'POST'])
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
            mysql.connection.commit()
            return redirect(url_for('member_updatesucess', email=email))
    else:   # Pre Fill Information in the form
        cursor.execute('SELECT * FROM account WHERE email = %s', (email,))
        account = cursor.fetchone()
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
    return render_template('Member_updateself.html', form=update_user_form, email=email, msg=msg)


@app.route('/updateMemberpass/<email>/', methods=['GET', 'POST'])
def update_memberpass(email):
     update_user_form = ChangePasswordForm(request.form)
     msg = ''
     if request.method == 'POST' and update_user_form.validate():
         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
         cursor.execute('SELECT * FROM account WHERE email = %s', (email,))
         account = cursor.fetchone()
         if update_user_form.oldpassword.data == account['password']:   # Check If Old Password Entered Is The Same One Entered By The User
             cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, email,))   # Update SQL To New Password That User Entered
             mysql.connection.commit()
             return redirect(url_for('member_updatesucess', email=email))
         else:
             msg = 'Incorrect Password'
     return render_template('Member_updateselfpass.html', form=update_user_form, email=email, msg=msg)


#Staff Pages
@app.route('/Stafflogin/<email>', methods=['GET','POST'])
def checkstaff(email):
    check_user_form = LoginForm(request.form)
    msg = ' '
    if request.method == 'POST' and check_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:
            if account['staff_id'] != None:     # Only allow access if staff_id field in the account has information in it (If An Account is a member, The Staff_id field would not be filled up)
                return redirect(url_for('staffpage', staff_name=account['full_name']))
        msg = "Incorrect Username/Password"

    return render_template('Staff_login.html', form=check_user_form, msg=msg, email=email)

@app.route('/Staffpage/<staff_name>')
def staffpage(staff_name):
    return render_template('Staff_Page.html', staff_name=staff_name)


#Reservation Form (Joel And Ernest)
@app.route('/retrieveReservation/<staff_name>')
def retrieve(staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation')
    users_list = cursor.fetchall()     # Retrieve All Reservatio
    return render_template('Reservation_retrieveUser.html', count=len(users_list), users_list=users_list, staff_name=staff_name)


@app.route('/updateUser/<id>/<staff_name>/', methods=['GET', 'POST'])
def update_user(id, staff_name):
    update_user_form = ReservationForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation WHERE reservation_id = %s', id)       # Get Entire Row That Contains The Reservation ID
    account = cursor.fetchone()
    if request.method == 'POST' and update_user_form.validate():
        cursor.execute('UPDATE reservation SET full_name= %s, email = %s, phone_num= %s, reservation_date= %s, reservation_time= %s, card_name= %s, card_number= %s, expiry_date= %s, cvv= %s, additional_note= %s WHERE reservation_id = %s', (update_user_form.full_name.data, update_user_form.email.data, update_user_form.phone_number.data, update_user_form.date.data, update_user_form.time.data, update_user_form.card_name.data, update_user_form.cn.data,str(update_user_form.expire.data + '-01'), update_user_form.cvv.data, update_user_form.Additional_note.data, id))
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
    return render_template('Reservation_updateUser.html', form=update_user_form, staff_name=staff_name)


@app.route('/deleteUser/<id>/<staff_name>/', methods=['POST'])
def delete_user(id, staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM reservation WHERE reservation_id = %s ', [id])
    mysql.connection.commit()
    return redirect(url_for('retrieve', staff_name=staff_name))


#Menu Page (Ian)
@app.route('/changetable/<state>')
def changetable(state):
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


@app.route('/orderpage_staff/<staff_name>')
def orderpagestaff(staff_name):
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

# Ian Table
@app.route('/staffdeleteitem/<deleteitem>/<tablenum>/<staff_name>')
def staffdeleteitem(deleteitem, tablenum, staff_name):
    del_order_dict = {}
    db = shelve.open('storage.db', 'w')
    del_order_dict = db['Order']

    gettablenum = del_order_dict.get(tablenum) #Get Order (As A Whole Class) from tablenum provided
    gettablenum.delete_order(deleteitem)
    del_order_dict[tablenum] = gettablenum
    db['Order'] = del_order_dict
    db.close()

    return redirect(url_for('orderpagestaff', staff_name=staff_name))


#Akif
# Retrieve Member
@app.route('/retrieveMembers/<staff_name>')
def retrieve_Members(staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account where member_level is not null ')     # Get Only Members (Staff has no member Level (AKA NULL value), Therefore, it won't be displayed'
    users_list = cursor.fetchall()
    return render_template('Member_retrieveUsers.html', count=len(users_list), users_list=users_list , staff_name=staff_name)


# Update Member for Staff
@app.route('/updateMemberstaff/<email>/<staff_name>', methods=['GET', 'POST'])
def update_memberstaff(email, staff_name):
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


# Delete Member
@app.route('/deleteMember/<mememail>/<staff_name>', methods=['POST'])
def delete_Member(mememail, staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM account WHERE email = %s ', [mememail])
    mysql.connection.commit()
    return redirect(url_for('retrieve_Members', staff_name=staff_name))


#Referal Codes
@app.route('/Referalcodes/<staff_name>', methods=['GET','POST'])
def referal_codes(staff_name):
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
            mysql.connection.commit()
            return redirect(url_for('referal_codes', staff_name=staff_name))

    return render_template('Member_StaffReferalCodes.html', form=createcode, count=len(code_list), code_list=code_list, staff_name=staff_name)

#Delete Referal Codes
@app.route('/deleteReferal/<codenum>/<staff_name>', methods=['GET', 'POST'])
def delete_code(codenum,staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM rewards WHERE reward_code = %s ', [codenum])
    mysql.connection.commit()
    return redirect(url_for('referal_codes', staff_name=staff_name))


#Create Staff User
@app.route('/CreateStaff/<staff_name>', methods=['GET','POST'])
def create_staff(staff_name):
    create_user_form = CreateStaff(request.form)
    if request.method == 'POST' and create_user_form.validate():
        hire_date = date.today()    # Get Today's Date
        newdate = hire_date.strftime("%Y-%m-%d")    # To Format Date Into SQL Readable Format (YYYY-MM-DD)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s', (create_user_form.email.data,))
        account = cursor.fetchone()
        if account:
            msg = 'This Email Has Been Taken'
        else:
            cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, NULL, NULL, NULL, %s, %s, %s)', (create_user_form.email.data, create_user_form.full_name.data, create_user_form.password.data, 'Member',  create_user_form.phone_number.data , create_user_form.staff_id.data , newdate, create_user_form.job_title.data))
            mysql.connection.commit()
            return redirect(url_for('confirmstaff', staff_name=staff_name, newuser=create_user_form.email.data))
    return render_template('Staff_Create.html', form=create_user_form, staff_name=staff_name)


@app.route('/confirmstaff/<staff_name>/<newuser>')
def confirmstaff(staff_name, newuser):
    return render_template('Staff_Confirm.html', staff_name=staff_name, newuser=newuser)


@app.route('/staffRetrieve/<staff_name>')
def staffretrieve(staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account where staff_id is not null ')     # Get Staff (Members will not be included as their staff_id is a null value)
    users_list = cursor.fetchall()
    return render_template('Staff_Userslist.html', count=len(users_list), users_list=users_list, staff_name=staff_name)


@app.route('/updateStaff/<toupdate>/<staff_name>/', methods=['GET', 'POST'])
def update_staff(toupdate, staff_name):     # toupdate Variable Is Used in a case where 1 staff Member is editing another Staff Member's Information). toupdate is the staff memeber's name
    update_user_form = UpdateStaff(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE full_name = %s and staff_id is not NULL', (toupdate,))  # Get Staff Email based on the staff name entere
    staff = cursor.fetchone()
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        cursor.execute('SELECT * FROM account WHERE email = %s', (update_user_form.email.data,))
        account = cursor.fetchone()
        if staff['email'] != account['email']:
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, staff_id= %s, job_title= %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.staff_id.data, update_user_form.job_title.data, staff['email'],))
            mysql.connection.commit()
            if staff_name == toupdate:
                return redirect(url_for('staffretrieve', staff_name=update_user_form.full_name.data))
            else:
                return redirect(url_for('staffretrieve', staff_name=staff_name))
    else:
        cursor.execute('SELECT * FROM account WHERE email = %s', (staff['email'],))     # Get Account Information
        account = cursor.fetchone()
        update_user_form.full_name.data = account['full_name']
        update_user_form.email.data = account['email']
        update_user_form.phone_number.data = account['phone_num']
        update_user_form.staff_id.data = account['staff_id']
        update_user_form.job_title.data = account['job_title']

    return render_template('Staff_updateuser.html', form=update_user_form, staff_name=staff_name)


@app.route('/deleteStaff/<delstaffemail>/<staff_name>', methods=['POST'])
def delete_staff(delstaffemail, staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM account WHERE email = %s ', [delstaffemail])
    mysql.connection.commit()
    return redirect(url_for('staffretrieve', staff_name=staff_name))


@app.route('/updatestaffpass/<staff_name>/', methods=['GET', 'POST'])
def Changepass_staff(staff_name):
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
             mysql.connection.commit()
             return redirect(url_for('member_updatesucess', email=' '))
         else:
             msg = 'Incorrect Password'
     return render_template('Staff_updateselfpass.html', form=update_user_form, staff_name=staff_name, msg=msg)


if __name__ == '__main__':
    app.run()
