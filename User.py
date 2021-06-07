class ReserveUser:
    count_id = 0

    def __init__(self, first_name, last_name, salutation, email, additional_note, phone_number, date, time, full_name, cn, expire, cvv):
        ReserveUser.count_id += 1
        self.__user_id = ReserveUser.count_id
        self.__first_name = first_name
        self.__last_name = last_name
        self.__salutation = salutation
        self.__email = email
        self.__additional_note = additional_note
        self.__phone_number = phone_number
        self.__date = date
        self.__time = time
        self.__full_name = full_name
        self.__cn = cn
        self.__expire = expire
        self.__cvv =  cvv

    def get_user_id(self):
        return self.__user_id

    def get_first_name(self):
        return self.__first_name

    def get_last_name(self):
        return self.__last_name

    def get_salutation(self):
        return self.__salutation

    def get_email(self):
        return self.__email

    def get_additional_note(self):
        return self.__additional_note

    def get_phone_number(self):
        return self.__phone_number

    def get_date(self):
        return self.__date

    def get_time(self):
        return self.__time

    def get_full_name(self):
        return self.__full_name

    def get_cn(self):
        return self.__cn

    def get_expire(self):
        return self.__expire

    def get_cvv(self):
        return self.__cvv

    def set_user_id(self, user_id):
        self.__user_id = user_id

    def set_first_name(self, first_name):
        self.__first_name = first_name

    def set_last_name(self, last_name):
        self.__last_name = last_name

    def set_salutation(self, salutation):
        self.__salutation = salutation

    def set_email(self, email):
        self.__email = email

    def set_additional_note(self, additional_note):
        self.__additional_note = additional_note

    def set_phone_number(self,phone_number):
        self.__phone_number = phone_number

    def set_date(self,date):
        self.__date = date

    def set_time(self,time):
        self.__time = time

    def set_full_name(self,full_name):
        self.__full_name = full_name

    def set_cn(self,cn):
        self.__cn = cn

    def set_expire(self,expire):
        self.__expire = expire

    def set_cvv(self,cvv):
        self.__cvv = cvv


class stafflogin:
    def __init__(self, staff_id, password):
        self.__staff_id = staff_id
        self.__password = password

    def get_staff_id(self):
        return self.__staff_id

    def get_password(self):
        return self.__password

class Member:
    def __init__(self, full_name, email, password, sign_up_date, level, completion):
        self.__full_name = full_name
        self.__email = email
        self.__password = password
        self.__sign_up_date = sign_up_date
        self.__level = level  # regular, bronze
        self.__completion = completion  # 1/5 2/5 6/10 1/15

    def get_full_name(self):
        return self.__full_name

    def get_email(self):
        return self.__email

    def get_password(self):
        return self.__password

    def get_sign_up_date(self):
        return self.__sign_up_date

    def get_level(self):
        return self.__level

    def get_completion(self):
        return self.__completion

    def set_full_name(self, full_name):
        self.__full_name = full_name

    def set_email(self, email):
        self.__email = email

    def set_password(self, password):
        self.__password = password

    def set_sign_up_date(self, sign_up_date):
        self.__sign_up_date = sign_up_date

    def set_level(self, level):
        self.__level = level

    def set_completion(self, completion):
        self.__completion = completion


    def increase_completion(self):  # 1/5 --> 2/5
        value = self.__completion

        if self.__level == 'Regular': #If Completion Reaches Regular Final Stage
            if int(value[0]) == 5:
                add_value = int(value[2]) + 5
                new_value = "1/" + str(add_value)
                self.__completion = new_value
                self.__level = "Bronze"
            else:   #Only For Regular as these have 1 digit for their max completion
                add_value = int(value[0])
                add_value += 1
                add_value = str(add_value)
                new_value = add_value + "/" + value[2]
                self.__completion = new_value

        if value[1] ==  "/":  #Only For Bronze and Above as these have 2 digit for their max completion
            add_value = int(value[0])
            add_value += 1
            add_value = str(add_value)
            new_value = add_value + "/" + value[2:4]
            self.__completion = new_value


        elif self.__level == 'Bronze' and value[0:2] == "10": #If Completion Reaches Bronze Final Stage
            add_value = int(value[3:5]) + 5
            new_value = "1/" + str(add_value)
            self.__completion = new_value
            self.__level = "Silver"

        elif self.__level == 'Silver' and int(value[0:2]) == 15: #If Completion Reaches Silver Final Stage
            add_value = int(value[3:5]) + 5
            new_value = "1/" + str(add_value)
            self.__completion = new_value
            self.__level = "Gold"

        elif self.__level == 'Gold' and int(value[0:2]) == 20: #If Completion Reaches Silver Final Stage
            add_value = int(value[3:5]) + 5
            new_value = "1/" + str(add_value)
            self.__completion = new_value
            self.__level = "Platinum"

        elif int(value[0:2]) >= 10: #10 and above
            add_value = int(value[0:2])
            add_value += 1
            add_value = str(add_value)
            new_value = add_value + "/" + value[3:5]
            self.__completion = new_value
