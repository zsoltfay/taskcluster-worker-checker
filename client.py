"""
This script will check for missing moonshots in TaskCluster.
github repo: https://github.com/Akhliskun/taskcluster-worker-checker
"""
try:
    from argparse import ArgumentParser
    import urllib.request, json
    import logging
    from configs.known_machines import *
    from gui.gui_logic import *
    from modules.git_logic import *
except ImportError:
    from setup import setup

    setup()

workersList = []
LINUX = "gecko-t-linux-talos"
WINDOWS = "gecko-t-win10-64-hw"
MACOSX = "gecko-t-osx-1010"

# Configure Logger
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="logs/runtime.log",
                    level=logging.DEBUG,
                    format=LOG_FORMAT
                    )

consoleHandler = logging.StreamHandler()
run_logger = logging.getLogger()
run_logger.addHandler(consoleHandler)

run_formatter = logging.Formatter('%(levelname)s: %(asctime)s - %(message)s')
machine_formatter = logging.Formatter('%(asctime)s - %(message)s', '%Y.%m.%d %H:%M')


def machine_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as we need"""
    handler = logging.FileHandler(log_file)
    handler.setFormatter(machine_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


lin_logger = machine_logger('lin_logger', 'logs/linux.log')
win_logger = machine_logger('win_logger', 'logs/windows.log')
osx_logger = machine_logger('osx_logger', 'logs/macosx.log')


def get_all_keys(*args):
    """Given a list of dictionaries, return a list of dictionary keys"""
    all_keys = []
    for d in args:
        all_keys.extend(list(d.keys()))
    return all_keys


def parse_taskcluster_json(workertype):
    '''
    We need this incase Auth fails.
    :param workertype: gecko-t-linux-talos, gecko-t-win10-64-hw, gecko-t-osx-1010.
    :return: A JSON file containing all workers for a workertype selected at runtime.
    '''

    # Setup API URLs
    if (workertype == LINUX) or (workertype == "linux"):
        apiUrl = "https://queue.taskcluster.net/v1/provisioners/releng-hardware/worker-types/gecko-t-linux-talos/workers"

    elif (workertype == WINDOWS) or (workertype == "win"):
        apiUrl = "https://queue.taskcluster.net/v1/provisioners/releng-hardware/worker-types/gecko-t-win10-64-hw/workers"

    elif (workertype == MACOSX) or (workertype == "osx"):
        apiUrl = "https://queue.taskcluster.net/v1/provisioners/releng-hardware/worker-types/gecko-t-osx-1010/workers"

    else:
        run_logger.error("Unknown worker-type!")
        run_logger.info("Please run the script with the [client.py -h] to see the help docs!")
        exit(0)

    with urllib.request.urlopen(apiUrl, timeout=10) as api:
        try:
            data = json.loads(api.read().decode())

        except:
            run_logger.info("Coundn't precess the JSON file in 10 seconds or less!")
            exit(0)

        try:
            if not data["workers"]:
                # Not sure why but TC kinda fails at responding or I'm doing something wrong
                # Anyways if you keep at it, it will respond with the JSON data :D
                run_logger.info("JSON Response Failed. Retrying...")
                parse_taskcluster_json(workertype)
            else:
                for workers in data['workers']:
                    workersList.append(workers['workerId'])

        except KeyboardInterrupt:
            run_logger.info("Application stopped via Keyboard Shortcut.")
            exit(0)

    return workersList


def generate_machine_lists(workertype):
    global mdc1_range, mdc2_range  # We need them global so we can use them to generate the ssh command.
    if (workertype == LINUX) or (workertype == "linux"):
        mdc1_range = list(range(1, 16)) + list(range(46, 61)) + \
                     list(range(91, 106)) + list(range(136, 151)) + \
                     list(range(181, 196)) + list(range(226, 241)) + \
                     list(range(271, 281))

        mdc2_range = list(range(301, 316)) + list(range(346, 361)) + \
                     list(range(391, 406)) + list(range(436, 451)) + \
                     list(range(481, 496)) + list(range(526, 541)) + \
                     list(range(571, 581))

        range_ms_linux = mdc1_range + mdc2_range
        ms_linux_name = "t-linux64-ms-{}"
        linux_machines = []

        for i in range_ms_linux:
            digit_constructor = str(i).zfill(3)  # Generate numbers in 3 digits form, like: 001, 002, 003
            linux_machines.append(ms_linux_name.format(digit_constructor))

        return linux_machines

    if (workertype == WINDOWS) or (workertype == "win"):
        mdc1_range = list(range(16, 46)) + list(range(61, 91)) + \
                     list(range(106, 136)) + list(range(151, 181)) + \
                     list(range(196, 226)) + list(range(241, 271)) + \
                     list(range(281, 299))
        mdc2_range = list(range(316, 346))

        range_ms_windows = mdc1_range + mdc2_range

        ms_windows_name = "T-W1064-MS-{}"
        windows_machines = []

        for i in range_ms_windows:
            digit_constructor = str(i).zfill(3)  # Generate numbers in 3 digits form, like: 001, 002, 003
            windows_machines.append(ms_windows_name.format(digit_constructor))
        return windows_machines

    if (workertype == MACOSX) or (workertype == "osx"):

        mdc2_range = list(range(21, 237))
        mdc1_range = list(range(237, 473))

        range_ms_osx = mdc2_range + mdc1_range  # No idea why macs MDC2 starts with the lower numbers.
        ms_osx_name = "t-yosemite-r7-{}"
        osx_machines = []

        for i in range_ms_osx:
            digit_constructor = str(i).zfill(3)  # Generate numbers in 3 digits form, like: 001, 002, 003
            osx_machines.append(ms_osx_name.format(digit_constructor))
        return osx_machines

    else:
        print("Invalid Worker-Type!")
        exit(0)


def main():
    # Get/Set Arguments
    parser = ArgumentParser(description="Utility to check missing moonshots form TC.")
    parser.add_argument("-w", "--worker-type",
                        dest="worker_type",
                        help="Available options: win, linux, osx",
                        default=LINUX,
                        required=False)
    parser.add_argument("-u", "--ldap-username",
                        dest="ldap_username",
                        help="Example: -u dlabici -- Don't include @mozilla.com!!",
                        default="root",
                        required=False)

    parser.add_argument("-v", "--verbose",
                        dest="verbose_enabler",
                        help="Example: -v True",
                        default=False,
                        required=False)

    parser.add_argument("-e", "--evolution",
                        dest="evolution_graph",
                        help="Example: -e True",
                        default=False,
                        required=False)

    args = parser.parse_args()
    workertype = args.worker_type
    ldap = args.ldap_username
    verbose = args.verbose_enabler
    evolution = args.evolution_graph

    parse_taskcluster_json(workertype)

    if verbose:
        from prettytable import PrettyTable

    # Remove machines from generated list
    if (workertype == LINUX) or (workertype == "linux"):
        loaners = machines_to_ignore["linux"]["loaner"]
        pxe_issues = machines_to_ignore["linux"]["pxe_issues"]
        hdd_issues = machines_to_ignore["linux"]["hdd_issues"]
        other_issues = machines_to_ignore["linux"]["other_issues"]
        ignore_all = list(get_all_keys(loaners, pxe_issues, hdd_issues, other_issues))

        if verbose:
            print("\nLinux Loaners:")
            if not loaners:
                print("No Linux Loaners")
            else:
                table = PrettyTable()
                table.field_names = ["Machine Name", "BUG ID", "Owner"]
                for machine in sorted(loaners.keys()):
                    table.add_row([machine, loaners[machine]['bug'], loaners[machine]['owner']])
                print(table)

            print("\nPXE Issues:")
            if not pxe_issues:
                print("No PXE Issues")
            else:
                pxe_table = PrettyTable()
                pxe_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for pxe in sorted(pxe_issues.keys()):
                    pxe_table.add_row([pxe, pxe_issues[pxe]['bug'], pxe_issues[pxe]['date'], pxe_issues[pxe]['update']])
                print(pxe_table)

            print("\nHDD Issues:")
            if not hdd_issues:
                print("No Linux with HDD Issues")
            else:
                hdd_table = PrettyTable()
                hdd_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for hdd in sorted(hdd_issues.keys()):
                    hdd_table.add_row([hdd, hdd_issues[hdd]['bug'], hdd_issues[hdd]['date'], hdd_issues[hdd]['update']])
                print(hdd_table)

            print("\nOther Issues:")
            if not other_issues:
                print("No Linux under Other Issues")
            else:
                otherissues_table = PrettyTable()
                otherissues_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for issue in sorted(other_issues.keys()):
                    otherissues_table.add_row(
                        [issue, other_issues[issue]['bug'], other_issues[issue]['date'], other_issues[issue]['update']])
                print(otherissues_table)

        a = set(ignore_all)
        workers = [x for x in generate_machine_lists(workertype) if x not in a]

    if (workertype == WINDOWS) or (workertype == "win"):
        loaners = machines_to_ignore["windows"]["loaner"]
        pxe_issues = machines_to_ignore["windows"]["pxe_issues"]
        hdd_issues = machines_to_ignore["windows"]["hdd_issues"]
        other_issues = machines_to_ignore["windows"]["other_issues"]
        ignore_all = list(get_all_keys(loaners, pxe_issues, hdd_issues, other_issues))

        if verbose:
            print("\nWindows Loaners:")
            if not loaners:
                print("No Windows Loaners")
            else:
                table = PrettyTable()
                table.field_names = ["Machine Name", "BUG ID", "Owner"]
                for machine in sorted(loaners.keys()):
                    table.add_row([machine, loaners[machine]['bug'], loaners[machine]['owner']])
                print(table)

            print("\nPXE Issues:")
            if not pxe_issues:
                print("No PXE Issues")
            else:
                pxe_table = PrettyTable()
                pxe_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for pxe in sorted(pxe_issues.keys()):
                    pxe_table.add_row([pxe, pxe_issues[pxe]['bug'], pxe_issues[pxe]['date'], pxe_issues[pxe]['update']])
                print(pxe_table)

            print("\nHDD Issues:")
            if not hdd_issues:
                print("No Windows with HDD Issues")
            else:
                hdd_table = PrettyTable()
                hdd_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for hdd in sorted(hdd_issues.keys()):
                    hdd_table.add_row([hdd, hdd_issues[hdd]['bug'], hdd_issues[hdd]['date'], hdd_issues[hdd]['update']])
                print(hdd_table)

            print("\nOther Issues:")
            if not other_issues:
                print("No Windows under Other Issues")
            else:
                otherissues_table = PrettyTable()
                otherissues_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for issue in sorted(other_issues.keys()):
                    otherissues_table.add_row(
                        [issue, other_issues[issue]['bug'], other_issues[issue]['date'], other_issues[issue]['update']])
                print(otherissues_table)

        a = set(ignore_all)
        workers = [x for x in generate_machine_lists(workertype) if x not in a]

    if (workertype == MACOSX) or (workertype == "osx"):
        loaners = machines_to_ignore["osx"]["loaner"]
        ssh_stdio = machines_to_ignore["osx"]["ssh_stdio"]
        ssh_unresponsive = machines_to_ignore["osx"]["ssh_unresponsive"]
        other_issues = machines_to_ignore["osx"]["other_issues"]
        ignore_all = list(get_all_keys(loaners, ssh_stdio, ssh_unresponsive, other_issues))

        if verbose:
            print("\nYosemite Loaners:")
            if not loaners:
                print("No Yosemite Loaners")
            else:
                table = PrettyTable()
                table.field_names = ["Machine Name", "BUG ID", "Owner"]
                for machine in sorted(loaners.keys()):
                    table.add_row([machine, loaners[machine]['bug'], loaners[machine]['owner']])
                print(table)

            print("\nSSH-STDIO Issues:")
            if not ssh_stdio:
                print("No SSH-STDIO Issues")
            else:
                stdio_table = PrettyTable()
                stdio_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for stdio in sorted(ssh_stdio.keys()):
                    stdio_table.add_row(
                        [stdio, ssh_stdio[stdio]['bug'], ssh_stdio[stdio]['date'], ssh_stdio[stdio]['update']])
                print(stdio_table)

            print("\nSSH-Unresponsive Issues:")
            if not ssh_unresponsive:
                print("No Yosemite with SSH Issues")
            else:
                unresponsive_table = PrettyTable()
                unresponsive_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for unresponsite in sorted(ssh_unresponsive.keys()):
                    unresponsive_table.add_row(
                        [unresponsite, ssh_unresponsive[unresponsite]['bug'], ssh_unresponsive[unresponsite]['date'],
                         ssh_unresponsive[unresponsite]['update']])
                print(unresponsive_table)

            print("\nOther Issues:")
            if not other_issues:
                print("No yosemite under Other Issues")
            else:
                otherissues_table = PrettyTable()
                otherissues_table.field_names = ["Machine Name", "BUG ID", "Date", "Update"]
                for issue in sorted(other_issues.keys()):
                    otherissues_table.add_row(
                        [issue, other_issues[issue]['bug'], other_issues[issue]['date'], other_issues[issue]['update']])
                print(otherissues_table)

        a = set(ignore_all)
        workers = [x for x in generate_machine_lists(workertype) if x not in a]

    b = set(workersList)
    missing_machines = [x for x in workers if x not in b]
    print("\n")
    print("Servers that WE know  of: {}".format(len(generate_machine_lists(workertype))))
    print("Servers that TC knows of: {}".format(len(workersList)))
    print("Total of missing server : {}".format(len(missing_machines)))

    if verbose:
        if len(workers) > len(generate_machine_lists(workertype)):
            print("!!! We got SCL3 Machines in the JSON body!!!! \n"
                  "!!! Ignoring all SCL3, Only MDC{1-2} machines are shown!!!!")

    # Print each machine on a new line.
    for machine in missing_machines:
        if (workertype == LINUX) or (workertype == "linux"):
            print("{}".format(machine))

        if (workertype == WINDOWS) or (workertype == "win"):
            print("{}".format(machine))

        if (workertype == MACOSX) or (workertype == "osx"):
            if int(machine[-3:]) <= int(mdc2_range[-1]):
                print("ssh {}@{}.test.releng.mdc2.mozilla.com".format(ldap, machine))
            else:
                print("ssh {}@{}.test.releng.mdc1.mozilla.com".format(ldap, machine))

    # Add Windows 10 Warning!
    if (workertype == WINDOWS) or (workertype == "win"):
        print('W1064 WORKERS FROM CHASSIS 8 (316-345) HAVE BEEN ADDED TO PRODUCTION. '
              'RE-IMAGE THESE WITH THE 2ND OPTION: GENERIC WORKER 10.10')

    # Add Logs to files:
    if (workertype == LINUX) or (workertype == "linux"):
        lin_logger.info(len(missing_machines))

    if (workertype == WINDOWS) or (workertype == "win"):
        win_logger.info(len(missing_machines))

    if (workertype == MACOSX) or (workertype == "osx"):
        osx_logger.info(len(missing_machines))

    if evolution:
        generate_graph()


if __name__ == '__main__':
    git_update_repo()
    main()
    git_push()
