import argparse 
import re
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


def main(args):
    f = open(args.log)
    lines = f.readlines() 
    nvar = len(args.variable)
    raw_datas = [[] for v in range(nvar)]
    cnt = 0
    index = [[] for v in range(nvar)]
    data_len = [0 for v in range(nvar)]
    for line in lines:
        for v in range(nvar):
            if line.startswith(args.variable[v]+":"):
                tmp = [float(a) for a in re.findall(r'-?\d+\.?\d*e?[-+]?\d*', line)]
                # print(tmp)
                if data_len[v]==0:
                    data_len[v] = len(tmp)
                if data_len[v]!=0 and len(tmp) == data_len[v]:
                    raw_datas[v].append(tmp)
                    index[v].append(cnt)
        cnt += 1
    print(data_len)
    # print(raw_datas)
    datas = [[[] for i in range(len(raw_datas[v][0]))] for v in range(nvar)]
    for v in range(nvar):
        for i in range(len(raw_datas[v])):
            for j in range(len(raw_datas[v][0])):
                # print(i,j,raw_datas[i][j])
                datas[v][j].append(raw_datas[v][i][j])
    # print(datas)
    
    for i in range(len(datas[0])):
        plt.figure(i)
        plt.xlim(-361, 361)
        plt.ylim(-203, 203)
        plt.plot(datas[v][0], datas[v][1], linewidth=3)
        # for v in range(nvar):
        #     plt.plot(datas[v][0], datas[v][1], linewidth=3)
            # if i < len(datas[v]):
            #     plt.plot(index[v], datas[v][i], label="{}[{}]".format(args.variable[v], i))
            # else:
            #     plt.plot(index[v], datas[v][0], label="{}[{}]".format(args.variable[v], 0))
        plt.legend()

    # for i in range(len(datas[0])):
    #     plt.figure(i)
        
        # for v in range(nvar):
        #     plt.plot(datas[v][0], datas[v][1], label="{}[{}]".format(args.variable[v], 1))
            # plt.plot(index[v], datas[v][2], label="{}[{}]".format(args.variable[v], 2))
            # if i < len(datas[v]):
            #     plt.plot(index[v], datas[v][i], label="{}[{}]".format(args.variable[v], i))
            # else:
            #     plt.plot(index[v], datas[v][0], label="{}[{}]".format(args.variable[v], 0))
        # plt.legend()
    # plt.figure()
    # plt.xlim(-361, 361)
    # plt.ylim(-203, 203)
    # plt.plot(datas[v][0], datas[v][1], label="{}[{}]".format(args.variable[v], 1))
    # plt.plot(datas[v + 1][0], datas[v + 1][1], label="{}[{}]".format(args.variable[v + 1], 1))
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('log', help='log file path')
    parser.add_argument('variable', nargs='+', help='variable to plot')
    args = parser.parse_args()
    print(args)
    main(args)