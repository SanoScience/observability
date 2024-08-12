from typing import Iterable
import time
import glob
import os
import psutil
import sys
import re
import subprocess
from subprocess import PIPE
import argparse

from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.metrics import (
    CallbackOptions,
    Observation,
    get_meter_provider,
    set_meter_provider,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

parser = argparse.ArgumentParser(description='Script for monitoring SLURM jobs.')
parser.add_argument('--collector', required=True, help="Opentelemetry collector endpoint e.g. http://example.com:4318")
parser.add_argument('--case-number', required=True, help="{{ case_number }} parameter. Unique identifier of MEE patient")
parser.add_argument('--pipeline-identifier', required=True, help="{{ pipeline_identifier }} parameter. \"#{case_number}_#{pipeline_id}\"")
parser.add_argument('--pipeline-name', required=True, help="{{ pipeline_name }} parameter. Readable pipeline name")
parser.add_argument('--step-name', required=True, help="{{ step_name }} parameter. Computation step name")
parser.add_argument('--custom-labels', required=False, help="Custom labels for this run of the script. Fortmat: --custom-labels label1:value1 label2:value2 ...", nargs='*')

args=parser.parse_args(sys.argv[1:])
print(args)

MAX_JOB_WAIT_RETRIES = 50
JOB_ID = os.environ.get('SLURM_JOB_ID')

pipeline_id = re.search("\d+$", args.pipeline_identifier)
if pipeline_id is not None:
    pipeline_id = pipeline_id.group()

resource = Resource(attributes={
    SERVICE_NAME: "Local"
})
exporter = OTLPMetricExporter(endpoint=args.collector, insecure=True)
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(metric_readers=[reader], resource=resource)
set_meter_provider(provider)
meter = get_meter_provider().get_meter("sano", "0.1.0")

def get_own_uid():
    """
    Fetch uid of the user who started the program.
    """
    get_uid = ['id', '-u']
    return subprocess.check_output(get_uid).strip().decode()

def get_username(uid):
    """
    Convert a numerical uid to a username
    """
    get_username = ['/usr/bin/id', '--name', '--user', '{}'.format(uid)]
    return subprocess.check_output(get_username).strip().decode()

def cgroup_processes(uid, job):
    """
    Find all the current PIDs for a cgroup of a user+job. Later on new processes might be started.
    """
    procs = []
    if job != JOB_ID:
        return procs
    step_g = '/sys/fs/cgroup/memory/slurm/uid_{}/job_{}/step_*'
    for step in glob.glob(step_g.format(uid, job)):
       for process_file in glob.glob(step + '/task_*'):
            with open(process_file + '/cgroup.procs', 'r') as stats:
                for proc in stats.readlines():
                    # check if process is not running as root
                    # a long sleep running as root can be found in step_extern
                    try:
                        ps = psutil.Process(int(proc))
                        if ps.username() != 'root':
                            procs.append(int(proc))
                    except psutil.NoSuchProcess:
                        pass
    return procs

def wait_for_job_start(uid, job):
    retries = MAX_JOB_WAIT_RETRIES
    procs = cgroup_processes(uid, job)
    while len(procs) == 0:
        if retries <= 0:
            print("Unable to fetch procs for this job. Exiting.")
            sys.exit(-1)
        print("Retry {} of fetching procs. Sleeping.".format(MAX_JOB_WAIT_RETRIES - retries))
        time.sleep(1)
        procs = cgroup_processes(uid, job)
        retries -= 1
    print("Scrapping job: {} for user: {} with uid: {}".format(job, user, uid))

job = JOB_ID
uid = get_own_uid()
user = get_username(uid)
wait_for_job_start(uid, job)
mem_path = '/sys/fs/cgroup/memory/slurm/uid_{}/job_{}/'.format(uid, job)
cpu_usage_file_path = '/sys/fs/cgroup/cpu/slurm/uid_{}/job_{}/cpuacct.usage'.format(uid, job)
simulation_id = None

base_metric_labels = {
    "case_number": args.case_number, "pipeline_id": pipeline_id,
    "pipeline_name": args.pipeline_name, "step_name": args.step_name,
    "slurm_job_id": job, "user": user, "simulation_id": simulation_id
}

custom_metric_labels = {
    label_with_value.split(':')[0]: label_with_value.split(':')[1] for label_with_value in args.custom_labels
} if args.custom_labels else {}

metric_labels = {**base_metric_labels, **custom_metric_labels}


def read_cpu_act_usage() -> int:
    with open(cpu_usage_file_path, 'r') as file:
        try:
            return int(file.read())
        except:
            return 0

start_time = int(time.time() * 1e9)
start_cpu_time = read_cpu_act_usage()


def read_cpu_percentage_usage() -> float:
    global start_time, start_cpu_time

    end_time = int(time.time() * 1e9)
    end_cpu_time = read_cpu_act_usage()

    cpu_usage = (end_cpu_time - start_cpu_time) / (end_time - start_time) * 100

    start_time = end_time
    start_cpu_time = end_cpu_time

    return cpu_usage

def read_single_memory_stat(file_name: str) -> int:
    with open(mem_path + file_name, 'r') as file:
        try:
            return int(file.read())
        except:
            return 0

def extract_memory_stat_metric(metric_name: str) -> int:
    metric_value = 0
    with open(mem_path + 'memory.stat', 'r') as f_stats:
        for line in f_stats.readlines():
            data = line.split()
            if len(data) == 2 and data[0] == metric_name:
                try:
                    metric_value = int(data[1])
                except:
                    pass
    return metric_value

def observable_gauge_usage_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(read_single_memory_stat('memory.usage_in_bytes'), metric_labels)

gauge_usage = meter.create_observable_gauge("slurm_job_memory_usage", [observable_gauge_usage_func])

def observable_gauge_max_usage_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(read_single_memory_stat('memory.max_usage_in_bytes'), metric_labels)

gauge_usage_max = meter.create_observable_gauge("slurm_job_memory_max", [observable_gauge_max_usage_func])

def observable_gauge_mem_limit_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(read_single_memory_stat('memory.limit_in_bytes'), metric_labels)

gauge_usage_mem_limit = meter.create_observable_gauge("slurm_job_memory_limit", [observable_gauge_mem_limit_func])

def observable_gauge_mem_cache_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_cache'), metric_labels)

gauge_usage_mem_cache = meter.create_observable_gauge("slurm_job_memory_total_cache", [observable_gauge_mem_cache_func])

def observable_gauge_mem_swap_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_swap'), metric_labels)

gauge_usage_mem_swap = meter.create_observable_gauge("slurm_job_memory_total_swap", [observable_gauge_mem_swap_func])

def observable_gauge_mem_total_rss_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_rss'), metric_labels)

gauge_usage_mem_total_rss = meter.create_observable_gauge("slurm_job_memory_total_rss", [observable_gauge_mem_total_rss_func])

def observable_gauge_mem_total_rss_huge_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_rss_huge'), metric_labels)

gauge_usage_mem_total_rss_huge = meter.create_observable_gauge("slurm_job_memory_total_rss_huge", [observable_gauge_mem_total_rss_huge_func])

def observable_gauge_mem_total_mapped_file_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_mapped_file'), metric_labels)

gauge_usage_mem_total_mapped_file = meter.create_observable_gauge("slurm_job_memory_total_mapped_file", [observable_gauge_mem_total_mapped_file_func])

def observable_gauge_mem_total_active_file_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_active_file'), metric_labels)

gauge_usage_mem_total_active_file = meter.create_observable_gauge("slurm_job_memory_total_active_file", [observable_gauge_mem_total_active_file_func])

def observable_gauge_mem_total_inactive_file_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_inactive_file'), metric_labels)

gauge_usage_mem_total_inactive_file = meter.create_observable_gauge("slurm_job_memory_total_inactive_file", [observable_gauge_mem_total_inactive_file_func])

def observable_gauge_mem_total_inactive_file_func(options: CallbackOptions) -> Iterable[Observation]:
    yield Observation(extract_memory_stat_metric('total_unevictable'), metric_labels)
    
gauge_usage_mem_total_unevictable = meter.create_observable_gauge("slurm_job_memory_total_unevictable", [observable_gauge_mem_total_inactive_file_func])

# CPU Guage

def observable_gauge_cpu_percentage_func(options: CallbackOptions) -> Iterable[Observation]:
    cpu_percentage_usage = read_cpu_percentage_usage()
    yield Observation(cpu_percentage_usage, metric_labels)
    
gauge_usage_cpu_percentage = meter.create_observable_gauge("slurm_job_cpu_percentage_usage", [observable_gauge_cpu_percentage_func])



# Async Gauge

def check_parent(pid, parent_pid):
    try:
        parent = psutil.Process(pid).parent()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # process may have exited or we may not have permission to access it
        return False
    if parent == None:
        return False
    if parent.pid != parent_pid:
        return check_parent(parent.pid, parent_pid)
    elif parent.pid == parent_pid:
        return True
    else:
        return True

def get_pids_from_parent_shell():
    parent_shell_pid = psutil.Process(os.getpid()).parent().parent().pid
    processes = psutil.process_iter()

    return ",".join([str(p.pid) for p in processes if check_parent(p.pid, parent_shell_pid)])


def observable_gauge_cpu_usage_percent_func(options: CallbackOptions) -> Iterable[Observation]:
    filtered_pids = get_pids_from_parent_shell()

    cpu_percentages = {}
    command = ["ps", "-p", filtered_pids, "-o", "pid,%cpu", "--no-headers"]
    result = subprocess.check_output(command).strip().decode()
    if result:
        for process_result in result.split('\n'):
            pid, usage = [number for number in process_result.split(' ') if len(number) > 0]
            cpu_percentages[pid] = float(usage)

    total_cpu_usage = sum(cpu_percentages.values())

    yield Observation(total_cpu_usage, metric_labels)

gauge_cpu_usage = meter.create_observable_gauge("slurm_job_cpu_percent", [observable_gauge_cpu_usage_percent_func])

def observable_gauge_mem_usage_percent_func(options: CallbackOptions) -> Iterable[Observation]:
    filtered_pids = get_pids_from_parent_shell()

    mem_percentages = {}
    command = ["ps", "-p", filtered_pids, "-o", "pid,%mem", "--no-headers"]
    result = subprocess.check_output(command).strip().decode()
    if result:
        for process_result in result.split('\n'):
            pid, usage = [number for number in process_result.split(' ') if len(number) > 0]
            mem_percentages[pid] = float(usage)

    total_mem_usage = sum(mem_percentages.values())

    yield Observation(total_mem_usage, metric_labels)

gauge_mem_usage = meter.create_observable_gauge("slurm_job_mem_percent", [observable_gauge_mem_usage_percent_func])

def get_list_of_disk_usages(process_pid):
    lsof_result = subprocess.Popen(["lsof", "-p", str(process_pid), "-Fs"], stdout=PIPE, stderr=PIPE)
    grep_result = subprocess.Popen(["grep", "^s"], stdin=lsof_result.stdout, stdout=PIPE, stderr=PIPE)
    cut_result = subprocess.run(["cut", "-c2-"], stdin=grep_result.stdout, stdout=PIPE, stderr=PIPE)
    return [int(x) for x in cut_result.stdout.strip().split(b'\n') if len(x) > 0]

def observable_gauge_disk_usage_func(options: CallbackOptions) -> Iterable[Observation]:
    filtered_pids = get_pids_from_parent_shell()

    total_disk_usage = sum(get_list_of_disk_usages(filtered_pids))

    yield Observation(total_disk_usage, metric_labels)

def observable_gauge_open_files(options: CallbackOptions) -> Iterable[Observation]:
    filtered_pids = get_pids_from_parent_shell()

    total_open_files = len(get_list_of_disk_usages(filtered_pids))

    yield Observation(total_open_files, metric_labels)

disk_usage = meter.create_observable_gauge("slurm_job_disk_usage", [observable_gauge_disk_usage_func])
open_files = meter.create_observable_gauge("slurm_job_open_files", [observable_gauge_open_files])

while True:
    provider.force_flush()
    except Exception as e:
        print(f"Exception occurred during force_flush: {e}")
    time.sleep(3)
