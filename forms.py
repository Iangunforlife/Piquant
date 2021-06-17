from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, validators, BooleanField, DateField
from wtforms.validators import email
from flask_wtf import RecaptchaField

class ReservationForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()])
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    phone_number = StringField('Phone Number', [validators.Length(min=8, max=8), validators.DataRequired()])
    date = DateField('Date(YYYY-MM-DD)', [validators.DataRequired()], format='%Y-%m-%d')
    time = StringField('Time(00:00:00)', [validators.Length(min=1, max=8), validators.DataRequired()])
    card_name = StringField('Card Holder name', [validators.Length(min=1, max=50), validators.DataRequired()])
    cn =StringField('Card Number', [validators.Length(min=16, max=16), validators.DataRequired()])
    expire = StringField('Expiry date of card YYYY-MM', [validators.Length(min=7, max=7), validators.DataRequired()])
    cvv =StringField('CVV', [validators.Length(min=1, max=3), validators.DataRequired()])
    Additional_note = TextAreaField('Additional note', [validators.Optional()])

# Akif
class CreateUserForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    password = PasswordField('New Password', [validators.DataRequired()], render_kw={"placeholder": "New Password"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})

class UpdatememberdetailForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})

class UpdatememberdetailstaffForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    signup_date = DateField('Sign Up Date(YYYY-MM-DD)', [validators.DataRequired()])

class ChangePasswordForm(Form):
    oldpassword = PasswordField('Old Password', [validators.DataRequired()], render_kw={"placeholder": "Old Password"})
    newpassword = PasswordField('New Password', [validators.DataRequired(), validators.EqualTo('cfmnewpassword', message='Passwords must match')], render_kw={"placeholder": "New Password"})
    cfmnewpassword = PasswordField('Confirm New Password', [validators.DataRequired()], render_kw={"placeholder": "Confirm New Password"})

class LoginForm(Form):
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "Email"})
    password = PasswordField('Password', [validators.DataRequired()], render_kw={"placeholder": "Password"})

# Referal Code
class ClaimCode(Form):
    claim_code = StringField('Claim a code', [validators.optional(), validators.Length(min=6, max=20)], render_kw={"placeholder": "eg. 12345A"})

class CreateCode(Form):
    code = StringField('Enter New Loyalty code', [validators.optional(), validators.Length(min=6, max=20)])

# Staff
class CreateStaff(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    password = PasswordField('New Password', [validators.DataRequired()], render_kw={"placeholder": "New Password"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    staff_id = StringField('Staff ID', [validators.Length(min=1, max=7), validators.DataRequired()],
                               render_kw={"placeholder": "Staff ID"})
    job_title = StringField('Job Title', [validators.Length(min=1, max=60), validators.DataRequired()],
                               render_kw={"placeholder": "Job Title"})

class UpdateStaff(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    staff_id = StringField('Staff ID', [validators.Length(min=1, max=7), validators.DataRequired()],
                               render_kw={"placeholder": "Staff ID"})
    hire_date = DateField('Hire Date(YYYY-MM-DD)', [validators.DataRequired()])
    job_title = StringField('Job Title', [validators.Length(min=1, max=60), validators.DataRequired()],
                               render_kw={"placeholder": "Job Title"})

# Adding New Menu Items
class addmenu(Form):
    itemcode = StringField('Item Code', [validators.Length(min=4, max=4), validators.DataRequired()])
    itemname = StringField('Item Name', [validators.Length(min=0, max=50), validators.DataRequired()])
    itemdesc = StringField('Item Description', [validators.Length(min=0, max=300), validators.DataRequired()])
    itemprice = StringField('Item Price (x.xx)', [validators.Length(min=3, max=5), validators.DataRequired()])

class Memforgotpassword(Form):
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "Email"})
    recaptcha = RecaptchaField()

class Memforgotaccount(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    recaptcha = RecaptchaField()

class EnterOTP(Form):
    OTP = StringField('OTP', [validators.Length(min=6, max=6), validators.DataRequired()],
                      render_kw={"placeholder": "OTP"})

class SecQn(Form):
    SecAns1 = StringField('', [validators.Length(min=1, max=50), validators.DataRequired()],
                      render_kw={"placeholder": "Answer"})
    SecAns2 = StringField('', [validators.Length(min=1, max=50), validators.DataRequired()],
                      render_kw={"placeholder": "Answer"})

class ChangeMemberPassword(Form):
    newpassword = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('cfmpassword', message='Passwords must match')],  render_kw={"placeholder": "New Password"})
    cfmpassword = PasswordField('Reenter Password', [validators.DataRequired()], render_kw={"placeholder": "Reenter Password"})
