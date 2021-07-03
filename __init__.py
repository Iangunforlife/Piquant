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
        cursor.execute('INSERT INTO reservation VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (create_user_form.full_name.data, create_user_form.email.data, create_user_form.phone_number.data, create_user_form.date.data,create_user_form.time.data,create_user_form.card_name.data,create_user_form.cn.data,str(create_user_form.expire.data + '-01'),create_user_form.cvv.data,create_user_form.Additional_note.data))
        mysql.connection.commit()   #Update SQL Database
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


# Ian
@app.route('/onlineorder')
def orderpage1():
    try:
        session['tablealloc']   # Check If Table Allocation Exist
    except:
         session['tablealloc'] = True   # Turn On Table Allocation
         session['tablenum'] = 1    # If Session Does Not Exist, Put as Default Table
    try:
        session['onlineorder']  # Check If There's Ordering Session For The Table
    except:
        session['onlineorder'] = True   # Turn On Online Order
        now = datetime.now()
        curtime = now.strftime("%H_%M_%S")
        session['ordersess'] = str(session['tablenum']) + '_' + curtime     # Create An Order Session Using tablenum and Current Time
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM menu')
    allitem = cursor.fetchall()
    return render_template('Menu_OrderPage.html', allitem=allitem)


@app.route('/addingorder/<orderitem>/')
def addingorder(orderitem):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    newordernum = session['ordersess'] + '_' + str(GenerateOrderNum.generateordernum()) # Generate A Random Order Number To Store
    cursor.execute('INSERT INTO cart VALUES (%s, %s, %s, %s, %s)', [newordernum, str(session['tablenum']), session['email'], orderitem, 'Pending'])
    mysql.connection.commit()
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
    return render_template('Menu_Cartpage.html', order_list=order_list, oldorder_list=oldorder_list, iteminfo=iteminfo, total=total)


@app.route('/deleteitem/<ordernum>')
def deleteitem(ordernum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM cart WHERE order_num = %s', [ordernum])
    mysql.connection.commit()
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
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s', (create_user_form.email.data,))
        account = cursor.fetchone()
        if account:     # Ensure That there will be no duplicates (As Email is A Primary Key In The Database)
            msg = 'This Email Has Been Taken'
        else:
            cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %7s, %s, %s, NULL, NULL, NULL)', (create_user_form.email.data, create_user_form.full_name.data, create_user_form.password.data, 'Member',  create_user_form.phone_number.data , "Regular", "1/5", newdate))
            mysql.connection.commit()
            session['login'] = True
            session['email'] = create_user_form.email.data
            return redirect(url_for('referral', state=" "))
    return render_template('Member_createUser.html', form=create_user_form, msg=msg)


# Login
@app.route('/Memberlogin', methods=['GET', 'POST'])
def member_login():
    msg = ''
    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:     # If Account Exist In DataBase
            session['login'] = True
            session['email'] = account['email']
            return redirect(url_for('referral', state=" "))
        else:
            msg = "Incorrect Username/Password"     # Return Incorrect Username/Password as a message
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
                     check = "used"     # Return Variable To Let Webapge Know That The Code is Used
                else:
                    check = "claim"
                    cursor.execute('UPDATE rewards SET status = %s WHERE reward_code = %s', ('Claimed', a['reward_code']))  # Update Status To Update
                    mysql.connection.commit()

        if check == "used":     #Shows if code has been claimed before
            return redirect(url_for('referral', state="used"))
        elif check == "claim":
            newreward = Member_Completion.increase_completion(account['member_level'], account['member_completion'])     # Increase Completion Using Function
            cursor.execute('UPDATE account SET member_level = %s, member_completion = %s WHERE email = %s', (newreward[0], newreward[1], session['email'],))
            mysql.connection.commit()
            return redirect(url_for('referral', state="claim"))
        else:
            return redirect(url_for('referral', state="unclaimed"))

    return render_template('Member_referral.html', form=claim_form, user=account, state=state)

@app.route('/logout')
def logout():
    session.pop('login', None)
    session.pop('email', None)
    try:
        session.pop('stafflogged', None)
    except:
        pass
    return redirect(url_for('member_login'))

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
        cursor.execute('SELECT * FROM account WHERE email = %s', (update_user_form.email.data,))
        account = cursor.fetchone()     # Fetch Only 1 SQL Record (Since Email Is A Primary Key, There Should Be Only 1 Record)
        if session['email'] != account['email']:   # Check Wether Database has this email or not
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, session['email'],))
            mysql.connection.commit()
            return redirect(url_for('member_updatesucess'))
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
             cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, session['email'],))   # Update SQL To New Password That User Entered
             mysql.connection.commit()
             session.pop('login', None)
             session.pop('email', None)
             return redirect(url_for('member_updatesucess'))
         else:
             msg = 'Incorrect Password'
     return render_template('Member_updateselfpass.html', form=update_user_form, msg=msg)


#Staff Pages
@app.route('/Stafflogin', methods=['GET','POST'])
def checkstaff():
    check_user_form = LoginForm(request.form)
    msg = ' '
    if request.method == 'POST' and check_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:
            if account['staff_id'] != None:     # Only allow access if staff_id field in the account has information in it (If An Account is a member, The Staff_id field would not be filled up)
                try:
                    session['login']
                    session.pop('login', None)
                    session.pop('email', None)
                except:
                    pass
                session['login'] = True
                session['email'] = account['email']    # Allow Staff To Access Normal Webapge
                session['stafflogged'] = account['full_name']   # To Use Staff Page Items
                return redirect(url_for('staffpage'))
        msg = "Incorrect Username/Password"

    return render_template('Staff_login.html', form=check_user_form, msg=msg)

@app.route('/Staffpage')
def staffpage():
    return render_template('Staff_Page.html')


#Reservation Form (Joel And Ernest)
@app.route('/retrieveReservation')
def retrieve():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation')
    users_list = cursor.fetchall()     # Retrieve All Reservatio
    return render_template('Reservation_retrieveUser.html', count=len(users_list), users_list=users_list)


@app.route('/updateUser/<id>', methods=['GET', 'POST'])
def update_user(id):
    update_user_form = ReservationForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reservation WHERE reservation_id = %s', id)       # Get Entire Row That Contains The Reservation ID
    account = cursor.fetchone()
    if request.method == 'POST' and update_user_form.validate():
        cursor.execute('UPDATE reservation SET full_name= %s, email = %s, phone_num= %s, reservation_date= %s, reservation_time= %s, card_name= %s, card_number= %s, expiry_date= %s, cvv= %s, additional_note= %s WHERE reservation_id = %s', (update_user_form.full_name.data, update_user_form.email.data, update_user_form.phone_number.data, update_user_form.date.data, update_user_form.time.data, update_user_form.card_name.data, update_user_form.cn.data,str(update_user_form.expire.data + '-01'), update_user_form.cvv.data, update_user_form.Additional_note.data, id))
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
    return redirect(url_for('orderpage1'))


@app.route('/orderpage_staff')
def orderpagestaff():
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
    return render_template('Menu_Stafforderpage.html', allorders=allorders, counttable=counttable, iteminfo=iteminfo)

# Change State To Served
@app.route('/stateorderpage_staff/<ordernum>')
def stateorderpagestaff(ordernum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Retrieve Carts From All Table
    cursor.execute('UPDATE cart SET status= %s WHERE order_num= %s', ['Served', ordernum])
    mysql.connection.commit()
    return redirect(url_for('orderpagestaff'))


# Delete Order Items
@app.route('/delorderpage_staff/<ordernum>')
def delorderpagestaff(ordernum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Retrieve Carts From All Table
    cursor.execute('DELETE FROM cart WHERE order_num = %s', [ordernum])
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
        print(add_item_form.itemcode.data)
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
        if checkitem['item_code'] != itemcode:
            msg = 'This Item Code Exist In The Database'
        elif edit_item_form.itemcode.data[0] not in ['S', 'M','D', 'E', 'W']:
            msg = 'Invalid Item Code'
        else:
            cursor.execute('UPDATE menu SET item_code= %s, item_name = %s, item_desc= %s, item_price= %s WHERE item_code = %s', (edit_item_form.itemcode.data, edit_item_form.itemname.data, edit_item_form.itemdesc.data, edit_item_form.itemprice.data, itemcode,))
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
    mysql.connection.commit()
    return redirect(url_for('staffadditem'))


#Akif
# Retrieve Member
@app.route('/retrieveMembers')
def retrieve_Members():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account where member_level is not null ')     # Get Only Members (Staff has no member Level (AKA NULL value), Therefore, it won't be displayed'
    users_list = cursor.fetchall()
    return render_template('Member_retrieveUsers.html', count=len(users_list), users_list=users_list)


# Update Member for Staff
@app.route('/updateMemberstaff/<mememail>', methods=['GET', 'POST'])
def update_memberstaff(mememail):
    update_user_form = UpdatememberdetailstaffForm(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    msg = ''
    if request.method == 'POST' and update_user_form.validate():
        cursor.execute('SELECT * FROM account WHERE email = %s', (update_user_form.email.data,))
        account = cursor.fetchone()
        if mememail != account['email']:   # Do Not Allow Change Of Email if The Email Address Entered Is Found In The Database
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s, sign_up_date = %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, update_user_form.signup_date.data, mememail,))
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
    mysql.connection.commit()
    return redirect(url_for('retrieve_Members'))


#Referal Codes
@app.route('/Referalcodes', methods=['GET','POST'])
def referal_codes():
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
            mysql.connection.commit()
            return redirect(url_for('referal_codes'))

    return render_template('Member_StaffReferalCodes.html', form=createcode, count=len(code_list), code_list=code_list, msg = msg)

#Delete Referal Codes
@app.route('/deleteReferal/<codenum>', methods=['GET', 'POST'])
def delete_code(codenum):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM rewards WHERE reward_code = %s ', [codenum])
    mysql.connection.commit()
    return redirect(url_for('referal_codes'))


#Create Staff User
@app.route('/CreateStaff', methods=['GET','POST'])
def create_staff():
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
                return redirect(url_for('confirmstaff', newuser=create_user_form.email.data))
    return render_template('Staff_Create.html', form=create_user_form, msg=msg)


@app.route('/confirmstaff/<newuser>')
def confirmstaff(newuser):
    return render_template('Staff_Confirm.html', newuser=newuser)


@app.route('/staffRetrieve')
def staffretrieve():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account where staff_id is not null ')     # Get Staff (Members will not be included as their staff_id is a null value)
    users_list = cursor.fetchall()
    return render_template('Staff_Userslist.html', count=len(users_list), users_list=users_list)


@app.route('/updateStaff/<toupdate>', methods=['GET', 'POST'])
def update_staff(toupdate):     # toupdate Variable Is Used in a case where 1 staff Member is editing another Staff Member's Information). toupdate is the staff memeber's name
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
    mysql.connection.commit()
    return redirect(url_for('staffretrieve'))


@app.route('/updatestaffpass', methods=['GET', 'POST'])
def Changepass_staff():
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
             mysql.connection.commit()
             return redirect(url_for('member_updatesucess'))
         else:
             msg = 'Incorrect Password'
     return render_template('Staff_updateselfpass.html', form=update_user_form, msg=msg)


if __name__ == '__main__':
    app.run()
