value = "10/20"
level = "Gold"

if level == 'Regular': #If Completion Reaches Regular Final Stage
    if int(value[0]) == 5:
        add_value = int(value[2]) + 5
        new_value = "1/" + str(add_value)
        print(new_value)
        print("Bronze")
    else:   #Only For Regular as these have 1 digit for their max completion
        add_value = int(value[0])
        add_value += 1
        add_value = str(add_value)
        new_value = add_value + "/" + value[2]
        print(new_value)

if value[1] == "/":  #Only For Bronze and Above as these have 2 digit for their max completion
    add_value = int(value[0])
    add_value += 1
    add_value = str(add_value)
    new_value = add_value + "/" + value[2:4]
    print(new_value)


elif level == 'Bronze' and value[0:2] == "10": #If Completion Reaches Bronze Final Stage
    add_value = int(value[3:5]) + 5
    new_value = "1/" + str(add_value)
    print(new_value)
    print("Silver")

elif level == 'Silver' and int(value[0:2]) == 15: #If Completion Reaches Silver Final Stage
    add_value = int(value[3:5]) + 5
    new_value = "1/" + str(add_value)
    print(new_value)
    print("Gold")

elif int(value[0:2]) >= 10: #10 and above
    add_value = int(value[0:2])
    add_value += 1
    add_value = str(add_value)
    new_value = add_value + "/" + value[3:5]
    print(new_value)
