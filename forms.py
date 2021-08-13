from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, validators, BooleanField
from wtforms.validators import email
from flask_wtf import RecaptchaField



class ReservationForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    salutation = SelectField('Salutation', [validators.DataRequired()], choices=[('', 'Select'), ('Dr', 'Dr'), ('Mr', 'Mr'), ('Mrs', 'Mrs'), ('Mdm', 'Mdm')], default='')
    email = StringField('Email', [validators.DataRequired(), validators.Email()])
    Additional_note = TextAreaField('Additional note', [validators.Optional()])
    phone_number = StringField('Phone Number', [validators.Length(min=1, max=150), validators.DataRequired()])
    date = StringField('Date(00/00/00)', [validators.Length(min=1, max=6), validators.DataRequired()])
    time = StringField('Time(0000)', [validators.Length(min=1, max=4), validators.DataRequired()])
    full_name = StringField('Full name', [validators.Length(min=1, max=150), validators.DataRequired()])
    cn =StringField('Card Number', [validators.Length(min=16, max=16), validators.DataRequired()])
    expire = StringField('Expiry date of card', [validators.Length(min=1, max=4), validators.DataRequired()])
    cvv =StringField('CVV', [validators.Length(min=1, max=3), validators.DataRequired()])


class CreateUserForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=30), validators.Regexp("^(?!.*[~`!@#$%^&()={}[\]:;,<>+\/?])[a-zA-Z_.-]", message="Invalid username (special cahracters allowed '_ and -')"), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})

    email = StringField('Email', [email(), validators.Length(max=40, message="Email too long"), validators.DataRequired()],
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


class UpdatememberdetailForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    phone_number = StringField('Phone_Number', [validators.Length(min=1, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})

class ChangePasswordForm(Form):
    oldpassword = PasswordField('Old Password', [validators.DataRequired()], render_kw={"placeholder": "Old Password"})
    newpassword = PasswordField('New Password', [validators.DataRequired(), validators.EqualTo('cfmnewpassword', message='Passwords must match')], render_kw={"placeholder": "New Password"})
    cfmnewpassword = PasswordField('Confirm New Password', [validators.DataRequired()], render_kw={"placeholder": "Confirm New Password"})

class LoginForm(Form):
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "Email"})
    password = PasswordField('Password', [validators.DataRequired()], render_kw={"placeholder": "Password"})


class ClaimCode(Form):
    claim_code = StringField('Claim a code', [validators.optional(), validators.Length(min=6, max=20)], render_kw={"placeholder": "eg. 12345A"})

class CreateCode(Form):
    code = StringField('Enter New Loyalty code', [validators.optional(), validators.Length(min=6, max=20)])

class CreateStaff(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    password = PasswordField('New Password', [validators.DataRequired()], render_kw={"placeholder": "New Password"})
    phone_number = StringField('Phone_Number', [validators.Length(min=1, max=8), validators.DataRequired()],
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
    phone_number = StringField('Phone_Number', [validators.Length(min=1, max=8), validators.DataRequired()],
                               render_kw={"placeholder": "Phone Number"})
    staff_id = StringField('Staff ID', [validators.Length(min=1, max=7), validators.DataRequired()],
                               render_kw={"placeholder": "Staff ID"})
    job_title = StringField('Job Title', [validators.Length(min=1, max=60), validators.DataRequired()],
                               render_kw={"placeholder": "Job Title"})
