from flask import Flask, render_template, request, redirect, url_for, session
from forms import *
import Member_Completion, GenerateOrderNum
from datetime import date, datetime
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'Secret'
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
    try:
        session['tablealloc']
    except:
         session['tablenum'] = 1
    try:
        session['onlineorder']
    except:
        session['onlineorder'] = True
        session['tablealloc'] = True
        now = datetime.now()
        curtime = now.strftime("%H_%M_%S")
        session['ordersess'] = str(session['tablenum']) + '_' + curtime
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM menu')
    allitem = cursor.fetchall()
    return render_template('Menu_OrderPage.html', email=email, allitem=allitem)


@app.route('/addingorder/<orderitem>/<email>')
def addingorder(orderitem, email):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    newordernum = session['ordersess'] + '_' + str(GenerateOrderNum.generateordernum()) # Generate A Random Order Number To Store
    cursor.execute('INSERT INTO cart VALUES (%s, %s, %s, %s, %s)', [newordernum, str(session['tablenum']), email, orderitem, 'Pending'])
    mysql.connection.commit()
    return redirect(url_for('orderpage1', email=email))


@app.route('/cart/<email>')
def cart(email):
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
    return render_template('Menu_Cartpage.html', order_list=order_list, oldorder_list=oldorder_list, iteminfo=iteminfo, total=total, email=email)


@app.route('/deleteitem/<ordernum>/<email>')
def deleteitem(ordernum, email):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM cart WHERE order_num = %s', [ordernum])
    mysql.connection.commit()
    return redirect(url_for('cart', email=email))

@app.route('/submit/<email>')
def submit(email):
    session.pop('onlineorder', None)
    session.pop('ordersess', None)
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

@app.route('/membersuccess/<email>')
def member_updatesuccess(email):
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
            return redirect(url_for('member_updatesuccess', email=email))
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
             return redirect(url_for('member_updatesuccess', email=email))
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
    cursor.execute('SELECT * FROM reservation WHERE reservation_id = %s', [id])       # Get Entire Row That Contains The Reservation ID
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
    if state == "T":    # Increase Table Number By 1
        session['tablenum'] = session['tablenum'] + 1
    elif state == "F":  # Decrease Table Number By 1
        if session['tablenum'] > 1:
            session['tablenum'] = session['tablenum'] - 1
    return redirect(url_for('orderpage1', email=' '))


@app.route('/orderpage_staff/<staff_name>')
def orderpagestaff(staff_name):
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
    return render_template('Menu_Stafforderpage.html', allorders=allorders, counttable=counttable, iteminfo=iteminfo, staff_name=staff_name)


# Change State To Served
@app.route('/stateorderpage_staff/<ordernum>/<staff_name>')
def stateorderpagestaff(ordernum, staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Retrieve Carts From All Table
    cursor.execute('UPDATE cart SET status= %s WHERE order_num= %s', ['Served', ordernum])
    mysql.connection.commit()
    return redirect(url_for('orderpagestaff', staff_name=staff_name))


# Delete Order Items
@app.route('/delorderpage_staff/<ordernum>/<staff_name>')
def delorderpagestaff(ordernum, staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Retrieve Carts From All Table
    cursor.execute('DELETE FROM cart WHERE order_num = %s', [ordernum])
    mysql.connection.commit()
    return redirect(url_for('orderpagestaff', staff_name=staff_name))


# Add Item To Menu:
@app.route('/staffadditem/<staff_name>', methods=['GET', 'POST'])
def staffadditem(staff_name):
    msg = ''
    add_item_form = addmenu(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM menu')
    allmenu = cursor.fetchall()
    if request.method == 'POST' and add_item_form.validate():
        add_item_form.itemcode.data = add_item_form.itemcode.data.upper()
        cursor.execute('SELECT * FROM menu WHERE item_code = %s', [add_item_form.itemcode.data])
        item = cursor.fetchone()
        print(add_item_form.itemcode.data)
        if add_item_form.itemcode.data[0] not in ['S', 'M', 'D', 'E', 'W']:
            msg = 'Invalid Item Code'
        elif item:
            msg = 'This Item Code Exist In The Database'
        else:
            cursor.execute('INSERT INTO menu VALUES (%s, %s, %s, %s)', (add_item_form.itemcode.data, add_item_form.itemname.data, add_item_form.itemdesc.data, add_item_form.itemprice.data ))
            mysql.connection.commit()
            return redirect(url_for('staffadditem', staff_name=staff_name))
    return render_template('Menu_Additem.html', form=add_item_form, staff_name=staff_name, msg=msg, allmenu=allmenu)


# Edit Item On Menu:
@app.route('/staffedititem/<itemcode>/<staff_name>', methods=['GET', 'POST'])
def staffedititem(itemcode, staff_name):
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
            except:
                if edit_item_form.itemcode.data[0] not in ['S', 'M','D', 'E', 'W']:
                    msg = 'Invalid Item Code'
                else:
                    cursor.execute('UPDATE menu SET item_code= %s, item_name = %s, item_desc= %s, item_price= %s WHERE item_code = %s', (edit_item_form.itemcode.data, edit_item_form.itemname.data, edit_item_form.itemdesc.data, edit_item_form.itemprice.data, itemcode,))
                    mysql.connection.commit()
                    return redirect(url_for('staffadditem', staff_name=staff_name))
    else:
        cursor.execute('SELECT * FROM menu WHERE item_code = %s', (itemcode,))  # Get Item Info based on the item code choosen
        item = cursor.fetchone()
        edit_item_form.itemcode.data = item['item_code']
        edit_item_form.itemname.data = item['item_name']
        edit_item_form.itemdesc.data = item['item_desc']
        edit_item_form.itemprice.data = item['item_price']

    return render_template('Menu_Edititem.html', form=edit_item_form, staff_name=staff_name, msg=msg)


# Remove Menu Item
@app.route('/staffdelitem/<itemcode>/<staff_name>', methods=['GET', 'POST'])
def staffdelitem(itemcode, staff_name):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM menu WHERE item_code = %s ', [itemcode])
    mysql.connection.commit()
    return redirect(url_for('staffadditem', staff_name=staff_name))


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
    msg = ''
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

    return render_template('Member_StaffReferalCodes.html', form=createcode, count=len(code_list), code_list=code_list, staff_name=staff_name, msg=msg)

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
    msg = ''
    create_user_form = CreateStaff(request.form)
    if request.method == 'POST' and create_user_form.validate():
        hire_date = date.today()    # Get Today's Date
        newdate = hire_date.strftime("%Y-%m-%d")    # To Format Date Into SQL Readable Format (YYYY-MM-DD)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Check If Email Exist In Database
        cursor.execute('SELECT * FROM account WHERE email = %s', (create_user_form.email.data,))
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
                cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, NULL, NULL, NULL, %s, %s, %s)', (create_user_form.email.data, create_user_form.full_name.data, create_user_form.password.data, 'Member',  create_user_form.phone_number.data , create_user_form.staff_id.data , newdate, create_user_form.job_title.data))
                mysql.connection.commit()
                return redirect(url_for('confirmstaff', staff_name=staff_name, newuser=create_user_form.email.data))
    return render_template('Staff_Create.html', form=create_user_form, staff_name=staff_name, msg=msg)


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
    cursor.execute('SELECT * FROM account WHERE full_name = %s and staff_id is not NULL', (toupdate,))  # Get Staff Email based on the staff name entered
    staff = cursor.fetchone()
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        cursor.execute('SELECT * FROM account WHERE email = %s', (update_user_form.email.data,))
        account = cursor.fetchone()
        if staff['email'] != account['email']:
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, staff_id= %s, hire_date= %s, job_title= %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.staff_id.data, update_user_form.hire_date.data, update_user_form.job_title.data, staff['email'],))
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
        update_user_form.hire_date.data = account['hire_date']
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
             return redirect(url_for('member_updatesuccess', email=' '))
         else:
             msg = 'Incorrect Password'
     return render_template('Staff_updateselfpass.html', form=update_user_form, staff_name=staff_name, msg=msg)


if __name__ == '__main__':
    app.run()
