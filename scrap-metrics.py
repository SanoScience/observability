from typing import Iterable
import time
import glob
import os
import psutil
import sys
from functools import lru_cache
import subprocess
from subprocess import PIPE

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

resource = Resource(attributes={
    SERVICE_NAME: "Local"
})
exporter = OTLPMetricExporter(endpoint="%%opentelemetry_collector_endpoint%%", insecure=True)
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(metric_readers=[reader], resource=resource)
set_meter_provider(provider)

JOB_ID = os.environ.get('SLURM_JOB_ID')
job = JOB_ID
meter = get_meter_provider().get_meter("sano", "0.1.0")
def get_username(uid):
    command = ['/usr/bin/id', '--name', '--user', '{}'.format(uid)]
    return subprocess.check_output(command).strip().decode()

def cgroup_processes(uid, job):
    procs = []
    if job != JOB_ID:
        return procs
    step_g = '/sys/fs/cgroup/memory/slurm/uid_{}/job_{}/step_*'
    for step in glob.glob(step_g.format(uid, job)):
        for process_file in glob.glob(step):
            with open(process_file + '/cgroup.procs', 'r') as stats:
                for proc in stats.readlines():
                    try:
                        ps = psutil.Process(int(proc))
                        if ps.username() != 'root':
                            procs.append(int(proc))
                    except psutil.NoSuchProcess:
                        pass
    return procs

for uid_dir in glob.glob("/sys/fs/cgroup/memory/slurm/uid_*"):

    uid = uid_dir.split('/')[-1].split('_')[1]
    job_path = "/sys/fs/cgroup/memory/slurm/uid_{}/job_*".format(uid)

    for job_dir in glob.glob(job_path):
        job = JOB_ID

        procs = cgroup_processes(uid, job)

        if len(procs) == 0:
            continue

        mem_path = '/sys/fs/cgroup/memory/slurm/uid_{}/job_{}/'.format(uid, job)
        user = get_username(uid)
        gpu_set = set()
        account = "error"

        def observable_gauge_usage_func(options: CallbackOptions) -> Iterable[Observation]:
            usage = 0
            with open(mem_path + 'memory.usage_in_bytes', 'r') as f_usage:
                usage = int(f_usage.read())
            yield Observation(usage, {"slurmjobid": job, "user": user})

        gauge_usage = meter.create_observable_gauge("slurm_job_memory_usage", [observable_gauge_usage_func])

        def observable_gauge_max_usage_func(options: CallbackOptions) -> Iterable[Observation]:
            usage_max = 0
            with open(mem_path + 'memory.max_usage_in_bytes', 'r') as f_max:
                usage_max = int(f_max.read())
            yield Observation(usage_max, {"slurmjobid": job, "user": user})

        gauge_usage_max = meter.create_observable_gauge("slurm_job_memory_max", [observable_gauge_max_usage_func])

        def observable_gauge_mem_limit_func(options: CallbackOptions) -> Iterable[Observation]:
            usage_limit = 0
            with open(mem_path + 'memory.limit_in_bytes', 'r') as f_limit:
                usage_limit = int(f_limit.read())
            yield Observation(usage_limit, {"slurmjobid": job, "user": user})

        gauge_usage_mem_limit = meter.create_observable_gauge("slurm_job_memory_limit", [observable_gauge_mem_limit_func])

        def observable_gauge_mem_cache_func(options: CallbackOptions) -> Iterable[Observation]:
            total_cache = 0
            with open(mem_path + 'memory.stat', 'r') as f_stats:
                for line in f_stats.readlines():
                    data = line.split()
                    if data[0] == 'total_cache':
                        total_cache = int(data[1])
            yield Observation(total_cache, {"slurmjobid": job, "user": user})
        gauge_usage_mem_cache = meter.create_observable_gauge("slurm_job_memory_total_cache", [observable_gauge_mem_cache_func])

        def observable_gauge_mem_total_rss_func(options: CallbackOptions) -> Iterable[Observation]:
            total_rss = 0
            with open(mem_path + 'memory.stat', 'r') as f_stats:
                for line in f_stats.readlines():
                    data = line.split()
                    if data[0] == 'total_rss':
                        total_rss = int(data[1])
            yield Observation(total_rss, {"slurmjobid": job, "user": user})
        gauge_usage_mem_total_rss = meter.create_observable_gauge("slurm_job_memory_total_rss", [observable_gauge_mem_total_rss_func])

        def observable_gauge_mem_total_rss_huge_func(options: CallbackOptions) -> Iterable[Observation]:
            total_rss_huge = 0
            with open(mem_path + 'memory.stat', 'r') as f_stats:
                for line in f_stats.readlines():
                    data = line.split()
                    if data[0] == 'total_rss_huge':
                        total_rss_huge = int(data[1])
            yield Observation(total_rss_huge, {"slurmjobid": job, "user": user})
        gauge_usage_mem_total_rss_huge = meter.create_observable_gauge("slurm_job_memory_total_rss_huge", [observable_gauge_mem_total_rss_huge_func])
        def observable_gauge_mem_total_mapped_file_func(options: CallbackOptions) -> Iterable[Observation]:
            total_mapped_file = 0
            with open(mem_path + 'memory.stat', 'r') as f_stats:
                for line in f_stats.readlines():
                    data = line.split()
                    if data[0] == 'total_mapped_file':
                        total_mapped_file = int(data[1])
            yield Observation(total_mapped_file, {"slurmjobid": job, "user": user})
        gauge_usage_mem_total_mapped_file = meter.create_observable_gauge("slurm_job_memory_total_mapped_file", [observable_gauge_mem_total_mapped_file_func])

        def observable_gauge_mem_total_active_file_func(options: CallbackOptions) -> Iterable[Observation]:
            total_active_file = 0
            with open(mem_path + 'memory.stat', 'r') as f_stats:
                for line in f_stats.readlines():
                    data = line.split()
                    if data[0] == 'total_active_file':
                        total_active_file = int(data[1])
            yield Observation(total_active_file, {"slurmjobid": job, "user": user})
        gauge_usage_mem_total_active_file = meter.create_observable_gauge("slurm_job_memory_total_active_file", [observable_gauge_mem_total_active_file_func])

        def observable_gauge_mem_total_inactive_file_func(options: CallbackOptions) -> Iterable[Observation]:
            total_inactive_file = 0
            with open(mem_path + 'memory.stat', 'r') as f_stats:
                for line in f_stats.readlines():
                    data = line.split()
                    if data[0] == 'total_inactive_file':
                        total_inactive_file = int(data[1])
            yield Observation(total_inactive_file, {"slurmjobid": job, "user": user})
        gauge_usage_mem_total_inactive_file = meter.create_observable_gauge("slurm_job_memory_total_inactive_file", [observable_gauge_mem_total_inactive_file_func])

        def observable_gauge_mem_total_inactive_file_func(options: CallbackOptions) -> Iterable[Observation]:
            total_unevictable = 0
            with open(mem_path + 'memory.stat', 'r') as f_stats:
                for line in f_stats.readlines():
                    data = line.split()
                    if data[0] == 'total_unevictable':
                        total_unevictable = int(data[1])
            yield Observation(total_unevictable, {"slurmjobid": job, "user": user})
        gauge_usage_mem_total_unevictable = meter.create_observable_gauge("slurm_job_memory_total_unevictable", [observable_gauge_mem_total_inactive_file_func])


def observable_gauge_cpu_usage_percent_func(options: CallbackOptions) -> Iterable[Observation]:
    parent_pid = psutil.Process(os.getpid()).parent().parent().pid

    # get a list of all running processes
    processes = psutil.process_iter()

    def check_parent(pid):
        try:
            parent = psutil.Process(pid).parent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        if parent == None:
            return False
        if parent.pid != parent_pid:
            return check_parent(parent.pid)
        elif parent.pid == parent_pid:
            return True
        else:
            return True

    filtered_processes = [p for p in processes if check_parent(p.pid)]

    cpu_percentages = {}
    for process in filtered_processes:
        try:
            command = ["ps", "-p", str(process.pid), "-o", "%cpu", "--no-headers"]
            result = subprocess.run(command, stdout=PIPE, stderr=PIPE)
            trimmed_output = result.stdout.strip()
            cpu_percentages[process.pid] = float(trimmed_output)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            print('Not found process')

    total_cpu_usage = sum(cpu_percentages.values())

    yield Observation(total_cpu_usage, {"slurmjobid": job, "user": user})

gauge_cpu_usage = meter.create_observable_gauge("slurm_job_cpu_percent", [observable_gauge_cpu_usage_percent_func])

def observable_gauge_mem_usage_percent_func(options: CallbackOptions) -> Iterable[Observation]:
    parent_pid = psutil.Process(os.getpid()).parent().parent().pid

    processes = psutil.process_iter()

    def check_parent(pid):
        try:
            parent = psutil.Process(pid).parent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
        if parent == None:
            return False
        if parent.pid != parent_pid:
            return check_parent(parent.pid)
        elif parent.pid == parent_pid:
            return True
        else:
            return True

    filtered_processes = [p for p in processes if check_parent(p.pid)]

    mem_percentages = {}
    for process in filtered_processes:
        try:
            command = ["ps", "-p", str(process.pid), "-o", "%mem", "--no-headers"]
            result = subprocess.run(command, stdout=PIPE, stderr=PIPE)
            trimmed_output = result.stdout.strip()
            mem_percentages[process.pid] = float(trimmed_output)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # process may have exited or we may not have permission to access it
            print('False')

    total_mem_usage = sum(mem_percentages.values())

    yield Observation(total_mem_usage, {"slurmjobid": job, "user": user})

gauge_mem_usage = meter.create_observable_gauge("slurm_job_mem_percent", [observable_gauge_mem_usage_percent_func])


while True:
    provider.force_flush()
    time.sleep(5)
