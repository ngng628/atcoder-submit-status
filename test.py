from time import sleep

# def del_n(n):
#    for _ in range(n):
#       print('\x1b[1F', end='')
#       print('\x1b[2K', end='')

# data = ["a----b", "c------d", "e----f"]
# data2 = ["a----b", "c----d", "e----f", "g----h"]

# [print(d) for d in data]
# sleep(1)
# del_n(len(data))
# sleep(1)
# [print(d) for d in data2]
# sleep(1)
# del_n(len(data2))
# sleep(1)
# [print(d) for d in data]
# sleep(1)
# del_n(len(data))
# print()
# sleep(1)


print('0123456789', end='', flush=True)
sleep(1)
print('\x1b[3D', end='', flush=True)
sleep(1)
print('0\n', end='', flush=True)
sleep(1)