def dec2ter(a):
    if a//3==0 : return [a%3]
    else : return dec2ter(a//3)+[a%3]

def dec2terstr(list):
    res = ''
    for trit in list:
        res = res + str(trit)
    return res

def dec2terXtrit(number, ntrits):
    temp = dec2terstr(dec2ter(number))
    res = ""
    if (len(temp)>ntrits):
        for i in range(ntrits):
            res = res + "2"
    elif (len(temp)>0):
        res = temp
        for j in range (len(temp),ntrits):
            res = "0"+res
    return res
            
