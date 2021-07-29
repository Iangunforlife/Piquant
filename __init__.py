from flask import Flask, render_template, request, redirect, url_for
from forms import ReservationForm, CreateUserForm,  UpdatememberdetailForm, ChangePasswordForm, LoginForm, ClaimCode, CreateCode, CreateStaff, UpdateStaff
import User, shelve, addorder, tablenumgenerate, referalcode
from datetime import date
from flask_mysqldb import MySQL
import MySQLdb.cursors


import bcrypt
from tkinter import *
from tkinter import messagebox
import tkinter
import time
import os
import random
import smtplib


app = Flask(__name__)

app.config['RECAPTCHA_PUBLIC_KEY'] = '6Ld8DSsbAAAAAKwzOf-7wqEtMrn4s-wzWGId70tk'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Ld8DSsbAAAAAGaCbG6u8jdfT1BIHCm3HHN_X2vV'
app.config['TESTING'] = False

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Thegodofwind2'
app.config['MYSQL_DB'] = 'piquant'
mysql = MySQL(app)


#Email To Be Passed into codes to check wether users are login or not
@app.route('/')
def home():
    return render_template('home.html', email=" ")

@app.route('/home2/<email>') #For Logged in Users
def home2(email):
    return render_template('home.html', email=email)

@app.route('/about/<email>/')
def about(email):
    return render_template('about.html', email=email)

# Customer Pages
@app.route('/Reservation/<email>', methods=['GET','POST'])
def create_user(email):
    create_user_form = ReservationForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        users_dict = {}
        db = shelve.open('storage.db', 'c')

        try:
            users_dict = db['RUsers']
        except:
            print("Error in retrieving Users from storage.db.")

        user = User.ReserveUser(create_user_form.first_name.data, create_user_form.last_name.data,
                         create_user_form.salutation.data, create_user_form.email.data,
                         create_user_form.Additional_note.data,create_user_form.phone_number.data,
                         create_user_form.date.data,create_user_form.time.data,
                         create_user_form.full_name.data,create_user_form.cn.data,
                         create_user_form.expire.data,create_user_form.cvv.data,)
        users_dict[user.get_user_id()] = user
        db['RUsers'] = users_dict
        db.close()

        return redirect(url_for('retrieve_users', email=email))

    return render_template('Reservation.html', form=create_user_form, email=email)


@app.route('/Confirmation/<email>')
def retrieve_users(email):
    users_dict = {}
    db = shelve.open('storage.db', 'r')
    users_dict = db['RUsers']
    db.close()

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        users_list.append(user)

    getuser = users_list[-1]

    return render_template('Reservation_Confirmation.html', count=len(users_list), get_user=getuser, email=email)


@app.route('/thanks/<email>')
def number(email):
    return render_template('Reservation_thanks.html', email=email)


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
        signupdate = date.today()
        newdate = signupdate.strftime("%Y-%m-%d") # Check, To Create New Date
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s', (create_user_form.email.data,))
        account = cursor.fetchone()
        if account:
            msg = 'This Email Has Been Taken'
        else:

            OTP = random.randint(100000, 999999)
            OTP = str(OTP)

            otp = OTP + " is your OTP"
            message = otp
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.starttls()
            s.login("qwhzjop@gmail.com", "117lol117")

            s.sendmail('qwhzjop@gmail.com', create_user_form.email.data, message)

            out_Window = Tk()
            out_Window.geometry("500x200")  # Size of Window Pop Up
            out_Window.title("Verification Screen")
            create_Member.out_count = 3
            create_Member.otp = "false"

            def verify():
                Window = out_Window
                end = time.time()
                t = format(end - start)
                print(float(t))
                if float(t) >= 60:
                    messagebox.showinfo("Time out", "Session Expired ...Time out Please regenerate OTP")
                    Window.destroy()
                else:
                    cmd1 = str(a.get())
                    if cmd1 == OTP:
                        Window.destroy()
                        # Password Hashing
                        # Create a random number (Salt)
                        salt = bcrypt.gensalt(rounds=16)
                        # A hashed value is created with hashpw() function, which takes the cleartext value and a salt as parameters.
                        hash_password = bcrypt.hashpw(create_user_form.password.data.encode(), salt)

                        cursor.execute('INSERT INTO account VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL)'
                                       , (create_user_form.email.data, create_user_form.full_name.data
                                          , hash_password, 'Member',
                                          create_user_form.phone_number.data, "Regular", "1/5", newdate))
                        mysql.connection.commit()

                        print(hash_password)

                        create_Member.otp = "true"
                        return True

                    cmd = 'python app.py ' + cmd1
                    os.system(cmd)
                    create_Member.out_count -= 1
                    count = create_Member.out_count
                    ok = 'Invalid OTP: ' + str((count)) + ' attempts remaining'
                    if count >= 1:
                        tkinter.messagebox.askretrycancel("Error", ok)
                    elif count == 0:
                        messagebox.showinfo("Your 3 attempts were over. Please regenerate the OTP")
                        Window.destroy()

            start = time.time()
            label1 = Label(out_Window, text="Verification Screen", relief="solid", font=("times", 15), fg='green').pack(
                fill=BOTH)  # Verification Screen [Header]

            a = StringVar()

            Re = Label(out_Window, text="Enter the OTP", font=("arial", 15, "bold"), fg='blue').place(x=0,
                                                                                                      y=125)  # Enter the OTP text
            # white space for user to enter into
            w1 = Entry(out_Window, width=20, fg='blue', textvariable=a)

            w1.place(x=180, y=130)  # Position of the OTP Input Field
            Re1 = Label(out_Window, text="Please enter the OTP within 1 minute", font=("times", 15), fg='blue').place(
                x=0,
                y=50)  # Please enter the OTP within 1 minutes [Sub-Header]
            ver = Button(out_Window, text="Verify", relief="raised", bg='cyan', font=("arial", 15), fg='green',
                         command=verify).place(x=350, y=125)
            out_Window.mainloop()

            if create_Member.otp == "true":
                return redirect(url_for('referral', email=create_user_form.email.data, state=" "))

    return render_template('Member_createUser.html', form=create_user_form, email=email, msg=msg)


# Login
@app.route('/Memberlogin/<email>/<state>', methods=['GET', 'POST'])
def member_login(email, state):
    msg = ''
    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:
            return redirect(url_for('referral', email=account['email'], state=" "))
        else:
            msg = "Incorrect Username/Password"
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
        code_list = cursor.fetchall()
        for a in code_list:
            if a['reward_code'] == claim_form.claim_code.data:
                if a['status'] == "Claimed":
                     check = "used"
                else:
                    check = "claim"
                    cursor.execute('UPDATE rewards SET status = %s WHERE reward_code = %s', ('Claimed', a['reward_code']))
                    mysql.connection.commit()

        if check == "used": #Shows if code has been claimed before
            return redirect(url_for('referral', email=email, state="used"))
        elif check == "claim":
            newreward = User.increase_completion(account['member_level'], account['member_completion'])
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
        account = cursor.fetchone()
        if email != account['email']:
            msg = "This Email Has Been Used"
        else:
            cursor.execute('UPDATE account SET email= %s, full_name = %s, phone_num= %s WHERE email = %s', (update_user_form.email.data, update_user_form.full_name.data, update_user_form.phone_number.data, email,))
            mysql.connection.commit()
            return redirect(url_for('member_updatesucess', email=email))
    else:
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
         if update_user_form.oldpassword.data == account['password']:
             cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, email,))
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
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account WHERE email = %s AND password = %s', (check_user_form.email.data,check_user_form.password.data,))
        account = cursor.fetchone()
        if account:
            if account['staff_id'] != None:
                return redirect(url_for('staffpage', staff_name=account['full_name']))
        msg = "Incorrect Username/Password"

    return render_template('Staff_login.html', form=check_user_form, msg=msg, email=email)

@app.route('/Staffpage/<staff_name>')
def staffpage(staff_name):
    return render_template('Staff_Page.html', staff_name=staff_name)


#Reservation Form (Joel And Ernest)
@app.route('/retrieveReservation/<staff_name>')
def retrieve(staff_name):
    users_dict = {}
    db = shelve.open('storage.db', 'r')
    users_dict = db['RUsers']
    db.close()

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        users_list.append(user)

    return render_template('Reservation_retrieveUser.html', count=len(users_list), users_list=users_list, staff_name=staff_name)


@app.route('/updateUser/<int:id>/<staff_name>/', methods=['GET', 'POST'])
def update_user(id, staff_name):
    update_user_form = ReservationForm(request.form)
    if request.method == 'POST' and update_user_form.validate():

        db = shelve.open('storage.db', 'w')
        users_dict = db['RUsers']

        user = users_dict.get(id)
        user.set_first_name(update_user_form.first_name.data)
        user.set_last_name(update_user_form.last_name.data)
        user.set_salutation(update_user_form.salutation.data)
        user.set_email(update_user_form.email.data)
        user.set_additional_note(update_user_form.Additional_note.data)
        user.set_phone_number(update_user_form.phone_number.data)
        user.set_date(update_user_form.date.data)
        user.set_time(update_user_form.time.data)
        user.set_full_name(update_user_form.full_name.data)
        user.set_cn(update_user_form.cn.data)
        user.set_expire(update_user_form.expire.data)
        user.set_cvv(update_user_form.cvv.data)


        db['RUsers'] = users_dict
        db.close()

        return redirect(url_for('retrieve', staff_name=staff_name))
    else:
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['RUsers']
        db.close()

        user = users_dict.get(id)
        update_user_form.first_name.data = user.get_first_name()
        update_user_form.last_name.data = user.get_last_name()
        update_user_form.salutation.data = user.get_salutation()
        update_user_form.email.data = user.get_email()
        update_user_form.Additional_note.data = user.get_additional_note()
        update_user_form.phone_number.data = user.get_phone_number()
        update_user_form.date.data = user.get_date()
        update_user_form.time.data = user.get_time()
        update_user_form.full_name.data = user.get_full_name()
        update_user_form.cn.data = user.get_cn()
        update_user_form.expire.data = user.get_expire()
        update_user_form.cvv.data = user.get_cvv()

        return render_template('Reservation_updateUser.html', form=update_user_form, staff_name=staff_name)


@app.route('/deleteUser/<int:id>/<staff_name>/', methods=['POST'])
def delete_user(id, staff_name):
    users_dict = {}
    db = shelve.open('storage.db', 'w')
    users_dict = db['RUsers']

    users_dict.pop(id)

    db['RUsers'] = users_dict
    db.close()

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
    '''
    users_dict = {}
    db = shelve.open('storage.db', 'r')
    try:
        users_dict = db['Member']
    except:
        print("Storage not found")
    db.close()

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        users_list.append(user)
    '''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account where member_level is not null ')
    users_list = cursor.fetchall()
    return render_template('Member_retrieveUsers.html', count=len(users_list), users_list=users_list , staff_name=staff_name)


# Update Member for Staff
@app.route('/updateMemberstaff/<email>/<staff_name>', methods=['GET', 'POST'])
def update_memberstaff(email, staff_name):
    update_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and update_user_form.validate():
        db = shelve.open('storage.db', 'w')
        users_dict = db['Member']

        temp = users_dict.get(email)
        users_dict.pop(email)

        replace = User.Member(update_user_form.full_name.data, update_user_form.email.data, update_user_form.password.data, update_user_form.sign_up_date.data, temp.get_level(), temp.get_completion())
        users_dict[replace.get_email()] = replace
        db['Member'] = users_dict
        db.close()

        return redirect(url_for('retrieve_Members', staff_name=staff_name))
    else:
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['Member']
        db.close()

        user = users_dict.get(email)
        update_user_form.full_name.data = user.get_full_name()
        update_user_form.email.data = user.get_email()
        update_user_form.password.data = user.get_password()
        update_user_form.sign_up_date.data = user.get_sign_up_date()

        return render_template('Member_updateUser.html', form=update_user_form, staff_name=staff_name)


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
        if code:
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
        hire_date = date.today()
        newdate = hire_date.strftime("%Y-%m-%d") # Check, To Create New Date
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
    cursor.execute('SELECT * FROM account where staff_id is not null ')
    users_list = cursor.fetchall()
    return render_template('Staff_Userslist.html', count=len(users_list), users_list=users_list, staff_name=staff_name)


@app.route('/updateStaff/<toupdate>/<staff_name>/', methods=['GET', 'POST'])
def update_staff(toupdate, staff_name):
    update_user_form = UpdateStaff(request.form)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM account WHERE full_name = %s and staff_id is not NULL', (toupdate,))
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
        cursor.execute('SELECT * FROM account WHERE email = %s', (staff['email'],))
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
         if update_user_form.oldpassword.data == account['password']:
             cursor.execute('UPDATE account SET password = %s WHERE email = %s', (update_user_form.newpassword.data, staff['email'],))
             mysql.connection.commit()
             return redirect(url_for('member_updatesucess', email=' '))
         else:
             msg = 'Incorrect Password'
     return render_template('Staff_updateselfpass.html', form=update_user_form, staff_name=staff_name, msg=msg)


if __name__ == '__main__':
    app.run(debug=True)
