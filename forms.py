from flask_wtf.file import FileRequired, FileAllowed
from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, validators, BooleanField, DateField, \
    RadioField, FileField, widgets, SelectMultipleField
from wtforms.validators import email
from flask_wtf import RecaptchaField

class ReservationForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()])
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    phone_number = StringField('Phone Number', [validators.Length(min=8, max=8), validators.DataRequired()])
    date = DateField('Date(YYYY-MM-DD)', [validators.DataRequired(), validators.Regexp("^[-0-9]+$", message="Date Must Only Contain - and 0-9")], format='%Y-%m-%d')
    time = StringField('Time(HH:MM) 24 Hrs Format', [validators.Length(min=1, max=8), validators.DataRequired(), validators.Regexp("^[:0-9]+$", message="Time Must Only Contain : and 0-9")])
    card_name = StringField('Card Holder name', [validators.Length(min=1, max=50), validators.DataRequired()])
    cn =StringField('Card Number', [validators.Length(min=16, max=16), validators.DataRequired()])
    expire = StringField('Expiry date of card YYYY-MM', [validators.Length(min=7, max=7), validators.DataRequired(), validators.Regexp("^[-0-9]+$", message="Date Must Only Contain - and 0-9")])
    cvv =StringField('CVV', [validators.Length(min=1, max=3), validators.DataRequired()])
    Additional_note = TextAreaField('Additional note', [validators.Optional()])
    selfie = FileField('For Recognition Purposes, Please Upload A Selfie:', validators=[FileRequired(), FileAllowed(['jpg'], "Jpg Files Only")])

class RetriveReservationForm(Form):
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


# Member Account Creation
class CreateUserForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=30), validators.Regexp("^(?!.*[~`!@#$%^&()={}[\]:;,<>+\/?])[a-zA-Z_.-]", message="Invalid username (special cahracters allowed '_ and -')"), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.Length(max=100, message="Email too long"), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    password = PasswordField('New Password',
                             [validators.Length(min=8, max=64, message="Password must be at least 8 characters long."),
                              validators.Regexp("^(?=.*[a-z])", message="Password must have a lowercase character"),
                              validators.Regexp("^(?=.*[A-Z])", message="Password must have an uppercase character"),
                              validators.Regexp("^(?=.*\\d)", message="Password must contain a number"),
                              validators.Regexp(
                                  "(?=.*[@$!%*#?&])", message="Password must contain a special character"
                              ), validators.DataRequired(),
                              validators.EqualTo('confirm', message='Passwords must match')],
                             render_kw={"placeholder": "New Password"})
    confirm = PasswordField('Confirm Password', render_kw={"placeholder": "Confirm Password"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.regexp("^(?!.*[a-zA-Z~`!@#$%^&()_={}[\]:;,.<>+\/?-])(?=.*[0-9])", message="Only numbers are allowed"), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    recaptcha = RecaptchaField()

# Member Login Page
class LoginForm(Form):
    email = StringField('Email', [email(), validators.DataRequired(), validators.regexp("^[a-zA-Z0-9]+@[a-zA-Z0-9.-]+.com$", message="Invalid Characters")],
                 render_kw={"placeholder": "Email"})
    password = PasswordField('Password', [validators.DataRequired(), validators.regexp("[^\s?\*=+~`><-][a-zA-Z0-9]{2,25}", message="Invalid Characters")], render_kw={"placeholder": "Password"})

# Referal Code
class ClaimCode(Form):
    claim_code = StringField('Claim a code', [validators.optional(), validators.Length(min=6, max=20)], render_kw={"placeholder": "eg. 12345A"})

class CreateCode(Form):
    code = StringField('Enter New Loyalty code', [validators.optional(), validators.Length(min=6, max=20)])


# Adding New Menu Items
class addmenu(Form):
    itemcode = StringField('Item Code', [validators.Length(min=4, max=4), validators.DataRequired()])
    itemname = StringField('Item Name', [validators.Length(min=0, max=50), validators.DataRequired()])
    itemdesc = StringField('Item Description', [validators.Length(min=0, max=300), validators.DataRequired()])
    itemprice = StringField('Item Price (x.xx)', [validators.Length(min=3, max=5), validators.DataRequired()])



# Account Management
class ChangePasswordForm(Form):
    oldpassword = PasswordField('Old Password', [validators.DataRequired()], render_kw={"placeholder": "Old Password"})
    newpassword = PasswordField('New Password', [validators.Length(min=8, max=64, message="Password must be at least 8 characters long."),
                              validators.Regexp("^(?=.*[a-z])", message="Password must have a lowercase character"),
                              validators.Regexp("^(?=.*[A-Z])", message="Password must have an uppercase character"),
                              validators.Regexp("^(?=.*\\d)", message="Password must contain a number"),
                              validators.Regexp(
                                  "(?=.*[@$!%*#?&])", message="Password must contain a special character"
                              ), validators.DataRequired(),
                              validators.EqualTo('cfmnewpassword', message='Passwords must match')],
                              render_kw={"placeholder": "New Password"})
    cfmnewpassword = PasswordField('Confirm New Password', [validators.DataRequired()], render_kw={"placeholder": "Confirm New Password"})

class ManChangeAccountPassword(Form):
    newpassword = PasswordField('Password', [validators.Length(min=8, max=64, message="Password must be at least 8 characters long."),
                              validators.Regexp("^(?=.*[a-z])", message="Password must have a lowercase character"),
                              validators.Regexp("^(?=.*[A-Z])", message="Password must have an uppercase character"),
                              validators.Regexp("^(?=.*\\d)", message="Password must contain a number"),
                              validators.Regexp(
                                  "(?=.*[@$!%*#?&])", message="Password must contain a special character"
                              ), validators.DataRequired(),
                              validators.EqualTo('cfmnewpassword', message='Passwords must match')],  render_kw={"placeholder": "New Password"})
    cfmnewpassword = PasswordField('Reenter Password', [validators.DataRequired()], render_kw={"placeholder": "Reenter Password"})

class Acctforgotpassword(Form):
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "Email"})
    recaptcha = RecaptchaField()

class Acctforgotaccount(Form):
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    recaptcha = RecaptchaField()

class EnterOTP(Form):
    OTP = StringField('OTP', [validators.Length(min=6, max=6), validators.DataRequired()],
                      render_kw={"placeholder": "OTP"})

class SecQn(Form):
    SecAns1 = StringField('', [validators.Length(min=1, max=50), validators.DataRequired()],
                      render_kw={"placeholder": "Answer"})
    SecAns2 = StringField('', [validators.Length(min=1, max=50), validators.DataRequired()],
                      render_kw={"placeholder": "Answer"})

class secpic(Form):
    secpic = RadioField('pic')

class uploadfavpic(Form):
    chosensecqn = StringField('Question:', [validators.Length(min=0, max=150), validators.DataRequired()])
    pic1 = FileField('Pic 1', validators=[FileRequired(), FileAllowed(['jpg'], "Jpg Files Only")])
    pic2 = FileField('Pic 2', validators=[FileRequired(), FileAllowed(['jpg'], "Jpg Files Only")])
    pic3 = FileField('Pic 3', validators=[FileRequired(), FileAllowed(['jpg'], "Jpg Files Only")])
    pic4 = FileField('Pic 4', validators=[FileRequired(), FileAllowed(['jpg'], "Jpg Files Only")])
    picchose = RadioField('Correct Picture', choices=[(1, 'Pic 1'), (2, 'Pic 2'), (3, 'Pic 3'), (4, 'Pic 4')])


# Member Account Management
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


# Staff Account Management
class CreateStaff(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    password = PasswordField('New Password',
                             [validators.Length(min=8, max=64, message="Password must be at least 8 characters long."),
                              validators.Regexp("^(?=.*[a-z])", message="Password must have a lowercase character"),
                              validators.Regexp("^(?=.*[A-Z])", message="Password must have an uppercase character"),
                              validators.Regexp("^(?=.*\\d)", message="Password must contain a number"),
                              validators.Regexp(
                                  "(?=.*[@$!%*#?&])", message="Password must contain a special character"
                              ), validators.DataRequired(),
                              validators.EqualTo('confirm', message='Passwords must match')],
                             render_kw={"placeholder": "New Password"})
    confirm = PasswordField('Confirm Password', render_kw={"placeholder": "Confirm Password"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    staff_id = StringField('Staff ID', [validators.Length(min=1, max=30), validators.DataRequired()],
                               render_kw={"placeholder": "Staff ID"})
    manager_id = StringField('Manager ID', [validators.Length(min=0, max=30)],
                               render_kw={"placeholder": "Manager ID (Optional)"})
    job_title = StringField('Job Title', [validators.Length(min=1, max=60), validators.DataRequired()],
                               render_kw={"placeholder": "Job Title"})

class UpdateStaff(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    phone_number = StringField('Phone_Number', [validators.Length(min=8, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    staff_id = StringField('Staff ID', [validators.Length(min=1, max=30), validators.DataRequired()],
                               render_kw={"placeholder": "Staff ID"})
    manager_id = StringField('Manager ID', [validators.Length(min=0, max=30)],
                               render_kw={"placeholder": "Manager ID (Optional)"})
    hire_date = DateField('Hire Date(YYYY-MM-DD)', [validators.DataRequired()])
    job_title = StringField('Job Title', [validators.Length(min=1, max=60), validators.DataRequired()],
                               render_kw={"placeholder": "Job Title"})

class AuthenticateAccount(Form):
    chooseOTP = RadioField('Choose 2FA Method', choices=[('Email', 'Email'), ("SMS", 'SMS')])

class Choose2fa(Form):
    fa2methodoption = RadioField('2FA status', choices=[('Yes', 'Yes'), ("No", 'No')])
