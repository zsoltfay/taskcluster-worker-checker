from matplotlib import pyplot as plt
from matplotlib import style
import csv


style.use("seaborn")
x = []
y = []

x2 = []
y2 = []

x3 = []
y3 = []


def generate_graph():
    with open("logs/linux.log", "r") as csvfile:
        # if len(csvfile.readlines()) == 0:
        #     pass
        # else:
        plots = csv.reader(csvfile, delimiter="-")
        for row in plots:
            x.append(str(row[0]))
            y.append(int(row[1]))

    with open("logs/windows.log", "r") as csvfile:

        plots = csv.reader(csvfile, delimiter="-")
        for row in plots:
            x2.append(str(row[0]))
            y2.append(int(row[1]))

    with open("logs/macosx.log", "r") as csvfile:

        plots = csv.reader(csvfile, delimiter="-")
        for row in plots:
            x3.append(str(row[0]))
            y3.append(int(row[1]))
    fig = plt.figure()
    plt.subplots_adjust(bottom=0.25)
    plt.plot(x, y, label="Linux")
    plt.plot(x2, y2, label="Windows")
    plt.plot(x3, y3, label="MacOSX")
    plt.xlabel("Date and Time")
    plt.ylabel("Number of Broken Machines")
    fig.canvas.set_window_title("Evolution of RelEng Broken Hardware")

    plt.legend()

    plt.show()

