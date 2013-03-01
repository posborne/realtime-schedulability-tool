Schedulability Analysis Tool
============================

Author: Paul Osborne
Date:   2/28/2013

Introduction
------------
The schedulabilty analysis tool takes as input as a description of a
set of tasks and their execution environment and provides an analysis
of whether the task set can be feasibly scheduled, assuming
preemptive fixed priority scheduling without any context switching
overhead.

The tool also generates a basic uniprocessor time demand curve
visualization of the provided task set (some things like the results
of some blocking are not indicated).

Usage
-----

The usage of the program is as follows

    $ python analyze_workloads.py -h
    usage: analyze_workload.py [-h] [--graph] [--graph-duration GRAPH_DURATION]
                               [--savefig]
                               taskdef
    
    positional arguments:
      taskdef               yaml file from which to load task definitions

    optional arguments:
      -h, --help            show this help message and exit
      --graph, -g           Display a graph of time-demand curve
      --graph-duration GRAPH_DURATION
                            for graph, how much time should be graphed
      --savefig             Store the figure image as demandcurve-<task_set>.png

Input Format
------------
The input format should be mostly self-explanatory by looking at other
instances.  YAML (Yet Another Markup Language) is used to define a
basic data structure.  Here is a brief example of a simple task set:

    name: Homework 2 (task set b)
    tasks:
      t1:
        period: 3
        execution_time: 1
      t2:
        period: 6
        execution_time: 3

For tasks, if no deadline is specified, it is assumed to be equal to
the period.

Example Output
--------------

Here's example output from the application where things could be scheduled.

    ********************************************************************************
    * TASK SET: Homework 2 (task set b)
    ********************************************************************************
    == Task Set Report ==
    Task Set Utilization: 0.83
    Tasks (priority ordered):
     - p01: Task 't1' (p=3, e=1, D=3)
         utilization   - 0.33
         blocking time - 0
     - p02: Task 't2' (p=6, e=3, D=6)
         utilization   - 0.50
         blocking time - 0

    == Schedulability Analysis ==
    All tasks could be feasibly scheduled!


Here's an example where the task set could not be scheduled.

    ********************************************************************************
    * TASK SET: Workload 4
    ********************************************************************************
    == Task Set Report ==
    Task Set Utilization: 0.98
    Tasks (priority ordered):
     - p01: Task 't1' (p=25, e=8, D=9)
         utilization   - 0.32
         blocking time - 2
     - p02: Task 't2' (p=50, e=13, D=50)
         utilization   - 0.26
         blocking time - 2
     - p03: Task 't3' (p=100, e=40, D=100)
         utilization   - 0.40
         blocking time - 0

    == Schedulability Analysis ==
    Not Schedulable!
    The following tasks are at risk of missing deadlines:
     - Task 't1' (p=25, e=8, D=9)
