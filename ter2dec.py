def ter2dec(a):
    res = 0
    for k in range(len(a)):
        res += a[-k]*3**(len(a)-k-1)
    return res
