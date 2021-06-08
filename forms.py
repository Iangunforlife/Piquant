from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, validators, BooleanField
from wtforms.validators import email

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

class stafflogin(Form):
    staff_id = StringField('Staff ID', [validators.Length(min=1, max=150), validators.DataRequired()])
    password = PasswordField('Password', [validators.Length(min=1, max=150), validators.DataRequired()])

# Akif
class CreateUserForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    password = PasswordField('New Password', [validators.DataRequired()], render_kw={"placeholder": "New Password"})
    sign_up_date = StringField('Sign Up Date', [validators.Length(min=1, max=150), validators.DataRequired()],
                               render_kw={"placeholder": "DD/MM/YYYY"})

class UpdatememberForm(Form):
    full_name = StringField('Full Name', [validators.Length(min=2, max=20), validators.DataRequired()],
                            render_kw={"placeholder": "Full Name"})
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "123@email.com"})
    password = PasswordField('New Password', [validators.DataRequired()], render_kw={"placeholder": "New Password"})

class LoginForm(Form):
    email = StringField('Email', [email(), validators.DataRequired()],
                        render_kw={"placeholder": "Email"})
    password = PasswordField('Password', [validators.DataRequired()], render_kw={"placeholder": "Password"})


class ClaimCode(Form):
    claim_code = StringField('Claim a code', [validators.optional(), validators.Length(min=6, max=20)], render_kw={"placeholder": "eg. 12345A"})

class CreateCode(Form):
    code = StringField('Enter New Loyalty code', [validators.optional(), validators.Length(min=6, max=20)])
