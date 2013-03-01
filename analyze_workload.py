# -*- coding: utf-8 -*-
import numpy
import math
import yaml
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('taskdef',
                    help='yaml file from which to load task definitions')
parser.add_argument('--graph', '-g',
                    default=False,
                    action='store_true',
                    help="Display a graph of time-demand curve")
parser.add_argument('--graph-duration',
                    type=int,
                    default=None,
                    help='for graph, how much time should be graphed')
parser.add_argument("--savefig",
                    default=False,
                    action='store_true',
                    help="Store the figure image as demandcurve-<task_set>.png")
args = parser.parse_args()


######################################################################
# Utility functions
######################################################################
def gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)


def lcmm(*args):
    """Return lcm of args."""
    return reduce(lcm, args)


class Task(object):
    """Represent a single task"""

    def __init__(self, period, execution_time, deadline=None, name=None):
        if deadline is None:
            deadline = period  # default deadline full period
        self.period = period
        self.execution_time = execution_time
        self.deadline = deadline
        self.name = name

    def __repr__(self):
        return ("Task %r (p=%d, e=%d, D=%d)" %
                (self.name, self.period, self.execution_time, self.deadline))


class LockingStrategyDisableInterrupts(object):

    @classmethod
    def get_worst_case_priority_inversion(cls, mutex, task):
        # When disabling interrupts, the worst case priority inversion
        # from this mutex of some task is the longest period of time that
        # any task might hold this mutex (disable interrupts) if the
        # task is lower priority.
        lower_priority = []
        task_priority = mutex.get_priority(task)
        for involved_task in mutex.tasks:
            if mutex.get_priority(involved_task) > task_priority:
                lower_priority.append(involved_task)
        if lower_priority:
            return max(mutex.tasks[t] for t in lower_priority)
        else:
            return 0


class LockingStrategyPriorityInheritance(object):

    @classmethod
    def get_worst_case_priority_inversion(cls, mutex, task):
        # Using priority inheritance, priority inversion can only occur
        # if the task being considered shares a resources with another
        # task related to this mutex.  The worst case priority inversion
        # time in this case is the longest duration of any resource holding
        # the resource with a lower priority than the task being considered.
        if not task in mutex.tasks:
            return 0
        lower_priority = []
        task_priority = mutex.get_priority(task)
        for involved_task in mutex.tasks:
            if mutex.get_priority(involved_task) > task_priority:
                lower_priority.append(involved_task)
        if lower_priority:
            return max(mutex.tasks[t] for t in lower_priority)
        else:
            return 0


class Mutex(object):
    """Model a mutual exclusion mechanism shared between tasks"""

    def __init__(self, task_set, tasks, locking_strategy):
        self.task_set = task_set
        self.tasks = tasks
        self.locking_strategy = locking_strategy

    def get_priority(self, task):
        return self.task_set.tasks.index(task)

    def get_worst_case_priority_inversion(self, task):
        """Get the worst case priority inversion time for the task"""
        return self.locking_strategy.get_worst_case_priority_inversion(self, task)


class DeadlineMonotonicFixedPriorityTaskSet(object):
    """Represent a collection of tasks"""

    @classmethod
    def from_task_list(cls, task_list):
        """Factory method to instantatiate and populate a task set from some tasks"""
        task_set = cls()
        for task in task_list:
            task_set.add_task(task)
        return task_set

    def __init__(self, name="Unnamed Task Set"):
        self.tasks = []  # list of tasks in priority order
        self.mutexes = []
        self.name = name

    def __repr__(self):
        return ("DeadlineMonotonicFixedPriorityTaskSet(\n%s)" %
                "".join("    p%d: %s,\n" % (i + 1, task)
                        for i, task in enumerate(self.tasks)))

    def _build_time_demand_fn_idx(self, idx, with_blocking=True):
        def time_demand_fn(t):
            if idx < 0:  # recursive base case
                return 0
            task = self.tasks[idx]
            # note: build demand_fn of next highest priority and recurse
            wi_t = (
                math.ceil(float(t) / task.period) * task.execution_time +
                self._build_time_demand_fn_idx(idx - 1, False)(t))
            if with_blocking:
                wi_t += self.get_blocking_time(task)
            return wi_t
        return time_demand_fn  # return fn bound to list/idx

    def get_blocking_time(self, task):
        if self.mutexes:
            return max(m.get_worst_case_priority_inversion(task) for m in self.mutexes)
        return 0

    def add_task(self, task):
        """Add a task to the task collection

        The task will be inserted in priority order (deadline monotonic
        prioritization).  The ordering between two tasks with the same
        relative deadline has no guarantee.

        """
        # TODO: this could be optimized, probably not a bottleneck
        self.tasks.append(task)
        self.tasks.sort(key=lambda t: t.deadline)  # deadline monotonic prioritization

    def add_mutex(self, mutex):
        """Add a mutex (shared resource with locking) to the task set"""
        self.mutexes.append(mutex)

    def build_time_demand_fn(self, task):
        """Build a time demand function for provided task"""
        idx = self.tasks.index(task)
        if idx < 0:
            raise ValueError("Task %r not in task set" % task)
        return self._build_time_demand_fn_idx(idx)

    def get_task_by_name(self, name):
        for task in self.tasks:
            if task.name == name:
                return task
        raise KeyError("No task with name %s" % name)


def plot_time_demand(task_set, duration=None):
    from matplotlib import pyplot as plt
    import pylab
    if duration is None:
        duration = lcmm(*[t.period for t in task_set.tasks])
    for i, task in enumerate(task_set.tasks):
        x = numpy.linspace(0, duration, 1000)
        wi = task_set.build_time_demand_fn(task)
        y = [wi(t) for t in x]
        plt.plot(x, y, label='w%d(t): %s' % ((i + 1), task))
    plt.plot(x, x, ':', label='uniprocessor service curve')
    pylab.grid(True)
    pylab.legend(loc='upper left', prop={'size': 'xx-small'})
    plt.title("%s - Time Demand Curve" % task_set.name)
    if args.savefig:
        filename = "demandcurve-%s.png" % task_set.name
        plt.savefig(filename, dpi=300)
        print "[Saved %r]" % filename
    else:
        plt.show()


def check_task_set(task_set):
    # we want to walk through each task in the task set
    # to determine if each one can be feasible scheduled.
    #
    # We use the Lehoczky time-demand analysis method to make
    # this determination.  For each task we must examine a set
    # of values t to verify the the time demand function for
    # the task at t is <= t.  If there is an instance where this
    # inequality is true, then the task can be scheduled.
    not_schedulable = []
    for idx, t_i in enumerate(task_set.tasks):
        time_demand_fn = task_set.build_time_demand_fn(t_i)
        t = t_i.execution_time
        while t <= t_i.deadline:
            wt = time_demand_fn(t)
            if wt <= t:
                break  # feasible
            t = wt
        else:  # no break in previous block
            not_schedulable.append(t_i)

    print ""
    print "== Schedulability Analysis =="
    if not_schedulable:
        print "Not Schedulable!"
        print "The following tasks are at risk of missing deadlines:"
        for task in not_schedulable:
            print " - %s" % task
    else:
        print "All tasks could be feasibly scheduled!"


def generate_report(task_set):
    print "== Task Set Report =="
    u = sum((float(t.execution_time) / t.period) for t in task_set.tasks)
    print "Task Set Utilization: %0.2f" % u
    print "Tasks (priority ordered):"
    for i, task in enumerate(task_set.tasks):
        utilization = float(task.execution_time) / task.period
        print " - p%02d: %r" % (i + 1, task)
        print "     utilization   - %0.2f" % (utilization)
        print "     blocking time - %d" % (task_set.get_blocking_time(task))


def load_tasks_from_yml():
    LOCKING_STRATEGIES = {
        'no_interrupt': LockingStrategyDisableInterrupts,
        'priority_inheritance': LockingStrategyPriorityInheritance,
    }
    with open(args.taskdef, 'r') as f:
        config = yaml.load(f)
    set_name = config.get("name", "%s" % args.taskdef)
    print "*" * 80
    print "* TASK SET: %s" % set_name
    print "*" * 80
    tasks_config = config.get("tasks", {})
    task_set = DeadlineMonotonicFixedPriorityTaskSet(set_name)
    for key, task_def in tasks_config.items():
        deadline = task_def.get("deadline", None)
        period = task_def["period"]
        execution_time = task_def["execution_time"]
        task = Task(period, execution_time, deadline, name=key)
        task_set.add_task(task)
    for mutex_key, mutex_def in config.get("mutexes", {}).items():
        method = mutex_def.get("method")
        tasks = {}
        for task_key, mutex_task_info in mutex_def.get("tasks").items():
            task = task_set.get_task_by_name(task_key)
            tasks[task] = mutex_task_info.get("cs_duration")
        task_set.add_mutex(Mutex(task_set, tasks, LOCKING_STRATEGIES.get(method)))

    if not args.graph:
        plot_time_demand(task_set, args.graph_duration)
    generate_report(task_set)
    check_task_set(task_set)


def main():
    load_tasks_from_yml()

if __name__ == '__main__':
    main()
