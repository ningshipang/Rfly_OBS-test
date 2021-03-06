import argparse 
import re
import os.path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d


def main(args):
    tmin = 0
    tmax = 1e10
    if args.time is not None:
        trange = [float(a) for a in re.findall(r'-?\d+\.?\d*e?[-+]?\d*', args.time)]
        tmin = trange[0]
        if len(trange) == 2:
            tmax = trange[1]

    nlog = len(args.log)
    raw_datas = [[] for l in range(nlog)]
    index = [[] for l in range(nlog)]
    begin_time = [0 for l in range(nlog)]

    for l in range(nlog):
        f = open(args.log[l])
        lines = f.readlines()
        time = 0
        for line in lines:
            if line.startswith("time:"):
                tmp = [float(a) for a in re.findall(r'-?\d+\.?\d*e?[-+]?\d*', line)]
                time = tmp[0]
                if begin_time[l] == 0: begin_time[l] = time
            if time < tmin or time > tmax:
                continue
            if line.startswith(args.variable+":"):
                tmp = [float(a) for a in re.findall(r'-?\d+\.?\d*e?[-+]?\d*', line)]
                raw_datas[l].append(tmp)
                if args.align:
                    index[l].append(time - begin_time[l])
                else:
                    index[l].append(time)
    # print(raw_datas)

    datas = [[[] for i in range(len(raw_datas[l][0]))] for l in range(nlog)]
    for l in range(nlog):
        for i in range(len(raw_datas[l])):
            for j in range(len(raw_datas[l][i])):
                # print(i,j,raw_datas[i][j])
                datas[l][j].append(raw_datas[l][i][j])
    # print(datas)

    if args.plotxy:
        fig, ax = plt.subplots()
        if args.grid:
            plt.plot([0,640],[240,240], color='#A5A5A5', linewidth=2)
            plt.plot([320,320],[0,480], color='#A5A5A5', linewidth=2)
        for l in range(nlog):
            if args.label is not None:
                plt.plot(datas[l][0], datas[l][1], label=args.label[l], linewidth=args.linewidth)
            else:
                plt.plot(datas[l][0], datas[l][1], label="{}".format(os.path.basename(args.log[l]).split(".")[0]), linewidth=args.linewidth)
        if args.range is not None:
            arange = [float(a) for a in re.findall(r'-?\d+\.?\d*e?[-+]?\d*', args.range)]
            plt.axis(arange)
        if args.title is not None:
            plt.title(args.title)
        if args.xlabel is not None:
            plt.xlabel(args.xlabel)
        if args.ylabel is not None:
            plt.ylabel(args.ylabel)
        plt.legend()
        if args.grid:
            plt.xticks(np.arange(0,642,80))
            plt.yticks(np.arange(0,481,80))
            plt.grid()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.savefig("err.png", dpi=1200)
        # plt.xlim(0, 721)
        # plt.ylim(0, 406)
        plt.show()

    '''
    plot 3D mapping
    '''
    if args.plotxyz:
        # fig, ax = plt.subplots(projection = '3d')
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        # if args.grid:
        #     plt.plot([0,640],[240,240], color='#A5A5A5', linewidth=2)
        #     plt.plot([320,320],[0,480], color='#A5A5A5', linewidth=2)
        for l in range(nlog):
            if args.label is not None:
                ax.plot(datas[l][0], datas[l][1], datas[l][2], label=args.label[l], linewidth=args.linewidth)
                # ax.set_zlim(0,5)
            else:
                ax.plot(datas[l][0], datas[l][1], datas[l][2], label="{}".format(os.path.basename(args.log[l]).split(".")[0]), linewidth=args.linewidth)
        if args.range is not None:
            arange = [float(a) for a in re.findall(r'-?\d+\.?\d*e?[-+]?\d*', args.range)]
            plt.axis(arange)
        if args.title is not None:
            plt.title(args.title)
        if args.xlabel is not None:
            plt.xlabel(args.xlabel)
        if args.ylabel is not None:
            plt.ylabel(args.ylabel)
        
        plt.legend()
        if args.grid:
            plt.xticks(np.arange(0,642,80))
            plt.yticks(np.arange(0,481,80))
            plt.grid()

        center = [0,7.2,2.5]
        radius = 0.05

        # data
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x = radius * np.outer(np.cos(u), np.sin(v)) + center[0]
        y = radius * np.outer(np.sin(u), np.sin(v)) + center[1]
        z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + center[2]
        ax.plot_surface(x, y, z,  rstride=4, cstride=4, color='b')

        if args.zlabel is not None:
            ax.set_zlabel(args.zlabel)

        ax.set_zlim(0,5)
        plt.xlim(-0.5, 0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        fig.savefig("err.png", dpi=1200)
        
        # plt.ylim(0, 1)
        # plt.zlim(0, 3)
        plt.show()

    if not args.self and not args.plotxy:
        for i in range(len(datas[0])):
            fig = plt.figure(i)
            ax = fig.add_subplot(111)
            for l in range(nlog):
                if args.label is not None:
                    plt.plot(index[l], datas[l][i], label=args.label[l], linewidth=args.linewidth)
                else:
                    plt.plot(index[l], datas[l][i], label="{}".format(os.path.basename(args.log[l]).split(".")[0]), linewidth=args.linewidth)
            if args.range is not None:
                arange = [float(a) for a in re.findall(r'-?\d+\.?\d*e?[-+]?\d*', args.range)]
                plt.axis(arange)
            if args.title is not None:
                plt.title(args.title)
            if args.xlabel is not None:
                plt.xlabel(args.xlabel)
            if args.ylabel is not None:
                plt.ylabel(args.ylabel)
            plt.legend()
            if args.grid:
                plt.grid()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            fig.savefig("{}.png".format(i), dpi=1200)
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('log', nargs='+', help='log file path')
    parser.add_argument('variable', help='variable to plot')
    parser.add_argument('-s', '--self', action='store_true', help='draw the various components of the variable on a figure')
    parser.add_argument('-p', '--plotxy', action='store_true', help='draw a 2-dimensional graph')
    parser.add_argument('-d', '--plotxyz', action='store_true', help='draw a 3-dimensional graph')
    parser.add_argument('-g', '--grid', action='store_true', help='show grid')
    parser.add_argument('-a', '--align', action='store_true', help='align the time axis')
    parser.add_argument('-l', '--linewidth', default=2, type=float, help='line width')
    parser.add_argument('-r', '--range', default=None, help='axises range, work with plotxy. usage: "xmin xmax ymin ymax"')
    parser.add_argument('-t', '--time', default=None, help='time range. usage: "tmin tmax" or tmin')
    parser.add_argument('--label', nargs='+', default=None, help='curve labels')
    parser.add_argument('--title', default=None, help='figure title')
    parser.add_argument('--xlabel', default=None, help='x label')
    parser.add_argument('--ylabel', default=None, help='y label')
    parser.add_argument('--zlabel', default=None, help='z label')
    args = parser.parse_args()
    print(args)
    main(args)