def dec2bin(a):
    if a//2==0 : return [a%2]
    else : return dec2bin(a//2)+[a%2]

def dec2binstr(list):
    res = ''
    for bit in list:
        res = res + str(bit)
    return res

def dec2binXbit(number, nbits):
    temp = dec2binstr(dec2bin(number))
    res = ""
    if (len(temp)>nbits):
        for i in range(nbits):
            res = res + "2"
    elif (len(temp)>0):
        res = temp
        for j in range (len(temp),nbits):
            res = "0"+res
    return res
            
