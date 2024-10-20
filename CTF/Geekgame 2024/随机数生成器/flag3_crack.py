from time import time

import gorand as gorand

# import gorand_org as gorand

target_1 = 3851868099 - ord('f')
target_2 = 1616668521 - ord('l')


start = 1610612735


def main():
    start_time = int(time())
    try:
        for seed in range(start, 1 << 31):
            gorand.seed(seed)
            # gorand.setseed(seed)

            rand = gorand.int63() >> 31
            # if seed <= start+20:
            #     print("rand:", rand)
            # else:
            #     break
            if rand == target_1:
                print("seed fake?:", seed)
                rand = gorand.int63() >> 31
                if rand == target_2:
                    print("seed:", seed)
                    break
    except KeyboardInterrupt:
        print("seed now:", seed)

    print("Time:", time()-start_time)


if __name__ == '__main__':
    main()
