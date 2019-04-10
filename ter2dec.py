def ter2dec(a):
    res = 0
    for k in range(len(a)-1,-1,-1):
        print("k={}".format(k))
        res += a[k]*3^k
    return res

print(ter2dec([0]))
print(ter2dec([1]))
print(ter2dec([2]))
print(ter2dec([1,0]))
print(ter2dec([1,1]))
print(ter2dec([1,2]))