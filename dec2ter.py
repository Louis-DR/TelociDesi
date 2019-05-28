def dec2ter(a,ntrits):
    if a>=0 :
        return dec2terAbs(a)
    else :
        a = int(((3**ntrits)-1)/2 - a)
        return dec2terAbs(a)

def dec2terAbs(a) :
    if a//3==0 : return [a%3]
    else : return dec2terAbs(a//3)+[a%3]

def dec2terstr(list):
    res = ''
    for trit in list:
        res = res + str(trit)
    return res

def dec2terXtrit(number, ntrits):
    temp = dec2terstr(dec2ter(number,ntrits))
    res = ""
    if (len(temp)>0):
        res = temp
        for j in range (len(temp),ntrits):
            res = "0"+res
    return res
            
