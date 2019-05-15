def dec2ter(a):
    if a//3==0 : return [a%3]
    else : return dec2ter(a//3)+[a%3]

def dec2terstr(list):
    res = ''
    for trit in list:
        res = res + str(trit)
    return res