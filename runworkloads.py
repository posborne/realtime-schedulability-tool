#!/usr/bin/env python
#
# Run each of the workloads, save the time demand function
# to an image and output the result
#
import glob
import subprocess
import sys

def run_workloads():
    for f in sorted(glob.glob("workload*.yml")):
        cmd = "python analyze_workload.py --savefig %s" % f
        print "\n\n"
        print '-' * 100
        print "$ %s" % cmd
        print '-' * 100
        sys.stdout.flush()
        subprocess.call(cmd, shell=True)

if __name__ == "__main__":
    run_workloads()

