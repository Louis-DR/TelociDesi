def ter2dec(a):
    res = 0
    for k in range(len(a)):
        res += a[-k]*3**(len(a)-k-1)
    return res

print(ter2dec([2,2,0,2,0,0]))
print(ter2dec([2,1,2,2,1,2]))
print(ter2dec([1,1,2,1,1,1]))
print(ter2dec([2,0,0,1,1,1]))
print(ter2dec([1,1,1,1,1,1]))
print(ter2dec([1,1,2,2,0,0]))