from flask import Flask, render_template, request, redirect, url_for
from forms import ReservationForm, stafflogin, CreateUserForm, UpdatememberForm, LoginForm, ClaimCode, CreateCode, Memforgotpassword, Memforgotaccount
import User, shelve, addorder, tablenumgenerate, referalcode

app = Flask(__name__)

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
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        users_dict = {}
        db = shelve.open('storage.db', 'c')

        try:
            users_dict = db['Member']
        except:
            print("Error in retrieving Users from storage.db.")

        user = User.Member(create_user_form.full_name.data, create_user_form.email.data, create_user_form.password.data,
                         create_user_form.sign_up_date.data, "Regular", "1/5")
        users_dict[user.get_email()] = user
        db['Member'] = users_dict

        db.close()

        return redirect(url_for('referral', email=create_user_form.email.data, state=" "))
    return render_template('Member_createUser.html', form=create_user_form, email=email)

# Login
@app.route('/Memberlogin/<email>/<state>', methods=['GET', 'POST'])
def member_login(email, state):
    check_user_form = LoginForm(request.form)
    if request.method == 'POST' and check_user_form.validate():
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['Member']
        db.close()

        for a in users_dict:
            member = users_dict.get(a)
            if check_user_form.email.data ==  member.get_email():
                if member.get_password() == check_user_form.password.data:
                    email = member.get_email()
                    state = "T"
        if state == "T":
            return redirect(url_for('referral', email=email, state=" "))
        else:
            state = "F"
            return redirect(url_for('member_login', email=email, state=state))

    return render_template('Member_login.html', form=check_user_form, email=email, state=state)


# Referral
@app.route('/referral/<email>/<state>', methods=['GET', 'POST'])
def referral(email, state):
    claim_form = ClaimCode(request.form)
    member_dict = {}
    # For Show Completion Part
    db = shelve.open('storage.db', 'r')
    member_dict = db['Member']
    member = member_dict.get(email)
    member.get_completion()
    db.close()

    #For Claiming Codes
    if request.method == 'POST' and claim_form.validate():
        db = shelve.open('storage.db', 'w')
        code_dict = {}
        check = ""
        try:
            code_dict = db['ClaimCode']
        except:
            print("Error in retrieving ClaimCode from storage.db.")

        for a in code_dict:
            if a == claim_form.claim_code.data:
                getcode = code_dict[a]
                if getcode.get_status() == "Claimed":
                     check = "used"
                else:
                    getcode.set_status("Claimed")
                    code_dict[getcode.get_codenum()] = getcode
                    db['ClaimCode'] = code_dict
                    check = "claim"

        if check == "used": #Shows if code has been claimed before
            db.close()
            return redirect(url_for('referral', email=email, state="used"))
        elif check == "claim":
            member.increase_completion()
            member_dict[email] = member
            db['Member'] = member_dict
            db.close()
            return redirect(url_for('referral', email=email, state="claim"))
        else:
            db.close()
            return redirect(url_for('referral', email=email, state="unclaimed"))

    return render_template('Member_referral.html', email=email, form=claim_form, user=member, state=state)

@app.route('/membersucess/<email>')
def member_updatesucess(email):
    return render_template('Member_Selfupdatesuccess.html', email=email)

#Update Member (For Customers)
@app.route('/updateMember/<email>/', methods=['GET', 'POST'])
def update_member(email):
    update_user_form = UpdatememberForm(request.form)
    if request.method == 'POST' and update_user_form.validate():
        db = shelve.open('storage.db', 'w')
        users_dict = db['Member']
        temp = users_dict.get(email)
        if temp.get_password() == update_user_form.oldpassword.data:
            users_dict.pop(email)

            replace = User.Member(update_user_form.full_name.data, update_user_form.email.data, update_user_form.newpassword.data, temp.get_sign_up_date(), temp.get_level(), temp.get_completion())
            users_dict[replace.get_email()] = replace
            db['Member'] = users_dict
            db.close()
            print("sucess")
        else:
            print("Unsuccess")

        return redirect(url_for('member_updatesucess', email=email))
    else:
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['Member']
        db.close()

        user = users_dict.get(email)
        update_user_form.full_name.data = user.get_full_name()
        update_user_form.email.data = user.get_email()
        update_user_form.oldpassword.data = user.get_password()

        return render_template('Member_updateself.html', form=update_user_form, email=email)

# Forgot Password
@app.route('/Memberforgotpass/<email>/<state>', methods=['GET', 'POST'])
def member_forgotpass(email, state):
    check_user_form = Memforgotpassword(request.form)
    if request.method == 'POST' and check_user_form.validate():
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['Member']
        db.close()

        for a in users_dict:
            member = users_dict.get(a)
            if check_user_form.email.data == member.get_email():
                state = "T"
        if state == "T":
            print("Account Found")
            return redirect(url_for('referral', email=email, state=" "))
        else:
            state = "F"
            print("Account Not Found")
            return redirect(url_for('member_login', email=email, state=state))

    return render_template('Member_ForgotPassword.html', form=check_user_form, email=email, state=state)

# Forgot Account
@app.route('/Memberforgotacct/<email>/<state>', methods=['GET', 'POST'])
def member_forgotacct(email, state):
    check_user_form = Memforgotaccount(request.form)
    if request.method == 'POST' and check_user_form.validate():
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['Member']
        db.close()

        for a in users_dict:
            member = users_dict.get(a)
            if check_user_form.full_name.data == member.get_full_name():
                state = "T"
        if state == "T":
            print("Account Found")
            return redirect(url_for('referral', email=email, state=" "))
        else:
            state = "F"
            print("Account Not Found")
            return redirect(url_for('member_login', email=email, state=state))

    return render_template('Member_ForgotAccount.html', form=check_user_form, email=email, state=state)


#Staff Pages
@app.route('/Stafflogin/<state>/<email>', methods=['GET','POST'])
def checkstaff(state, email):
    check_user_form = stafflogin(request.form)
    state = state
    staffid = ""
    if request.method == 'POST' and check_user_form.validate():
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['StaffUsers']
        db.close()

        for a in users_dict:
           staff = users_dict.get(a)
           if check_user_form.staff_id.data == staff.get_staff_id():
               if staff.get_password() == check_user_form.password.data:
                    staffid = staff.get_staff_id()
                    state = "T"
        if state == "T":
            return redirect(url_for('staffpage', staffid=staffid))
        else:
            state = "F"
            return redirect(url_for('checkstaff', state=state, email=email))

    return render_template('Staff_login.html', form=check_user_form, state=state, email=email)

@app.route('/Staffpage/<staffid>')
def staffpage(staffid):
    return render_template('Staff_Page.html', staffid=staffid)


#Reservation Form (Joel And Ernest)
@app.route('/retrieveReservation/<staffid>')
def retrieve(staffid):
    users_dict = {}
    db = shelve.open('storage.db', 'r')
    users_dict = db['RUsers']
    db.close()

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        users_list.append(user)

    return render_template('Reservation_retrieveUser.html', count=len(users_list), users_list=users_list, staffid=staffid)

@app.route('/updateUser/<int:id>/<staffid>/', methods=['GET', 'POST'])
def update_user(id, staffid):
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

        return redirect(url_for('retrieve', staffid=staffid))
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

        return render_template('Reservation_updateUser.html', form=update_user_form, staffid=staffid)


@app.route('/deleteUser/<int:id>/<staffid>/', methods=['POST'])
def delete_user(id, staffid):
    users_dict = {}
    db = shelve.open('storage.db', 'w')
    users_dict = db['RUsers']

    users_dict.pop(id)

    db['RUsers'] = users_dict
    db.close()

    return redirect(url_for('retrieve', staffid=staffid))



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


@app.route('/orderpage_staff/<staffid>')
def orderpagestaff(staffid):
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

    return render_template('Menu_Stafforderpage.html', order_listdict=order_listdict, currenttable=currenttable, staffid=staffid)

# Ian Table
@app.route('/staffdeleteitem/<deleteitem>/<tablenum>/<staffid>')
def staffdeleteitem(deleteitem, tablenum, staffid):
    del_order_dict = {}
    db = shelve.open('storage.db', 'w')
    del_order_dict = db['Order']

    gettablenum = del_order_dict.get(tablenum) #Get Order (As A Whole Class) from tablenum provided
    gettablenum.delete_order(deleteitem)
    del_order_dict[tablenum] = gettablenum
    db['Order'] = del_order_dict
    db.close()

    return redirect(url_for('orderpagestaff', staffid=staffid))


#Akif
# Retrieve Member
@app.route('/retrieveMembers/<staffid>')
def retrieve_Members(staffid):
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

    return render_template('Member_retrieveUsers.html', count=len(users_list), users_list=users_list , staffid=staffid)


# Update Member for Staff
@app.route('/updateMemberstaff/<email>/<staffid>', methods=['GET', 'POST'])
def update_memberstaff(email, staffid):
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

        return redirect(url_for('retrieve_Members', staffid=staffid))
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

        return render_template('Member_updateUser.html', form=update_user_form, staffid=staffid)


# Delete Member
@app.route('/deleteMember/<email>/<staffid>', methods=['POST'])
def delete_Member(email, staffid):
    users_dict = {}
    db = shelve.open('storage.db', 'w')
    users_dict = db['Member']

    users_dict.pop(email)

    db['Member'] = users_dict
    db.close()

    return redirect(url_for('retrieve_Members', staffid=staffid))

#Referal Codes
@app.route('/Referalcodes/<staffid>', methods=['GET','POST'])
def referal_codes(staffid):
    createcode = CreateCode(request.form)
    code_dict = {}
    db = shelve.open('storage.db', 'c')
    try:
        code_dict = db['ClaimCode']
    except:
        print("Storage not found")

    code_list = []
    for key in code_dict:
        code = code_dict.get(key)
        code_list.append(code)

    if request.method == 'POST' and createcode.validate():
        code_dict = {}
        db = shelve.open('storage.db', 'c')
        try:
            code_dict = db['ClaimCode']
        except:
            print("Storage not found")

        code = referalcode.ReferalCode(createcode.code.data, "Unclaimed")
        code_dict[code.get_codenum()] = code
        db['ClaimCode'] = code_dict
        db.close()

        return redirect(url_for('referal_codes', staffid=staffid))

    return render_template('Member_StaffReferalCodes.html', form=createcode, count=len(code_list), code_list=code_list, staffid=staffid)

#Update Referal Codes
@app.route('/deleteReferal/<codenum>/<staffid>', methods=['GET', 'POST'])
def delete_code(codenum,staffid):
    code_dict = {}
    db = shelve.open('storage.db', 'w')
    code_dict = db['ClaimCode']

    code_dict.pop(codenum)

    db['ClaimCode'] = code_dict
    db.close()

    return redirect(url_for('referal_codes', staffid=staffid))


#Create Staff User
@app.route('/CreateStaff/<staffid>', methods=['GET','POST'])
def create_staff(staffid):
    create_user_form = stafflogin(request.form)
    if request.method == 'POST' and create_user_form.validate():
        users_dict = {}
        db = shelve.open('storage.db', 'c')

        try:
            users_dict = db['StaffUsers']
        except:
            print("Error in retrieving Users from storage.db.")

        user = User.stafflogin(create_user_form.staff_id.data, create_user_form.password.data)
        newuser = user.get_staff_id()
        users_dict[newuser] = user
        db['StaffUsers'] = users_dict
        db.close()

        return redirect(url_for('confirmstaff', newuser=newuser,  staffid=staffid))

    return render_template('Staff_Create.html', form=create_user_form, staffid=staffid)

@app.route('/confirmstaff/<staffid>/<newuser>')
def confirmstaff(staffid, newuser):
    return render_template('Staff_Confirm.html', staffid=staffid, newuser=newuser)

@app.route('/staffRetrieve/<staffid>')
def staffretrieve(staffid):
    users_dict = {}
    db = shelve.open('storage.db', 'r')
    users_dict = db['StaffUsers']
    db.close()

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        users_list.append(user)

    return render_template('Staff_Userslist.html', count=len(users_list), users_list=users_list, staffid=staffid)

@app.route('/updateStaff/<ustaffid>/<staffid>/', methods=['GET', 'POST'])
def update_staff(ustaffid, staffid):
    update_user_form = stafflogin(request.form)
    if request.method == 'POST' and update_user_form.validate():

        db = shelve.open('storage.db', 'w')
        users_dict = db['StaffUsers']

        users_dict.pop(ustaffid)
        user = User.stafflogin(update_user_form.staff_id.data, update_user_form.password.data)
        users_dict[user.get_staff_id()] = user
        db['StaffUsers'] = users_dict
        db.close()

        return redirect(url_for('staffretrieve', staffid=staffid))
    else:
        users_dict = {}
        db = shelve.open('storage.db', 'r')
        users_dict = db['StaffUsers']
        db.close()

        user = users_dict.get(staffid)
        update_user_form.staff_id.data = user.get_staff_id()
        update_user_form.password.data = user.get_password()

        return render_template('Staff_updateuser.html', form=update_user_form, staffid=staffid)


@app.route('/deleteStaff/<delstaffid>/<staffid>', methods=['POST'])
def delete_staff(delstaffid, staffid):
    users_dict = {}
    db = shelve.open('storage.db', 'w')
    users_dict = db['StaffUsers']

    users_dict.pop(delstaffid)

    db['StaffUsers'] = users_dict
    db.close()

    return redirect(url_for('staffretrieve', staffid=staffid))


if __name__ == '__main__':
    app.run()
