# Observability:
Observability is project focused on bringing monitoring to scientific applications.
It is designed to work with supercomputer from Cyfronet AGH (Ares) 

# System:
System for collecting, storing and providing access to monitoring data is build from several components. Below diagram ilustrates connections between them:

![monitoring workflow](https://github.com/user-attachments/assets/b62096c2-37a3-48fe-9ed5-61463f4ddb08)

# Deployment:


All the necessary files for deploying the monitoring system are included in this repository. The system is designed to run as multiple Docker containers.
To enable telemetry data collection, you must specify the HTTP endpoint for the collector.

## Launching Steps:
- Clone this repository into the directory where you want to run the Docker containers.
- Review the `docker-compose.yaml` file to ensure that the selected ports are available and configure the HTTP endpoint for the collector.
- Update the `COLLECTOR_ENDPOINT` in the `monitoring.sh` script to match the new address.
- Adjust the memory and CPU limits for the containers based on your system’s resources.
- Build the Docker image by running the following command: `docker build -t observability_image PATH_TO_DIRECTORY_WITH_DOCKERFILE`
- Deploy and start the monitoring system environment by running: `docker-compose up`


# Usage:
 
To use monitoring in your calculations on MEE or some other Slurm environment you have to add to your liquid.sh file these script lines:

```
wget -q https://raw.githubusercontent.com/SanoScience/observability/main/monitoring.sh https://raw.githubusercontent.com/SanoScience/observability/main/monitoring-env.yml
source monitoring.sh
CASE_NUMBER=`param_or_empty {{ case_number }}`; PIPELINE_IDENTIFIER=`param_or_empty {{ pipeline_identifier }}`; PIPELINE_NAME=`param_or_empty {{ pipeline_name }}`; STEP_NAME=`param_or_empty {{ step_name }}`

setup_conda monitoring-env.yml
install_packages`
run_monitoring "--custom-labels case_number:$CASE_NUMBER pipeline_identifier:$PIPELINE_IDENTIFIER pipeline_name:$PIPELINE_NAME step_name:$STEP_NAME" &
```

There can be multiple name of labels (ex: label1) and for every label one value (ex: value1)

# Telemetry data visualisation:

The four services are responsible for data visualization, each serving a distinct purpose and providing different insights into the monitored resource utilization.

## Jaeger

To use Jaeger in the current deployment, you must be connected to the Sano Science VPN. The Jaeger address is: http://172.20.29.2:16686/search.
Through the interactive API, you can search for traces collected and stored in Jaeger. A pre-configured service, `AngioSupport_Monitoring`, is available for monitoring the instrumented application, AngioSupport.

## OpenSearch dashboards

OpenSearch Dashboards is primarily a development tool for detailed analysis of collected metrics. This service is accessible only through the Sano Science VPN and can be reached at: http://172.20.29.2:5601/app/home#/. To analyze metrics, select "Discover" from the menu bar and choose "metrics" to display the data. You can then adjust the time range and filter the data using Lucene queries.
OpenSearch dashboard shows whole documents from OpenSearch database representing metrics collected during computations.

## Grafana

Grafana is visualisation tool based on interactive dashboards made from charts and other data reports. 
In our deployed system, the Grafana service is accessible outside the VPN at the following address: https://monitoring.sano.science/?orgId=1
Predefined dashboards present consuption of memory or CPU as wel as informations about open files during computations. To explore these dashboards you have to select `Dasboards` in menu. The main dashboard prepared for the majority of computations is named `Per job monitoring`. The second dashboard `AngioSupport monitoring` is dedicated to use for monitoring of Angio Support application.

You can easily access the prepared dashboard and search for the data you need using the interactive interface. If certain charts are missing, the Grafana service allows you to create new dashboards and data summaries.

## APM Data Analyzer

APM Data Analyzer is deployed as JupyterHub service. To access it you must be connected to the Sano Science VPN. The APM Data Analyzer address is: http://172.20.29.2:7601/hub/login
You can aither create new account with `Sign up` button or sign in to existing account. After creating account for the first time you may have to launch server for your account.

After connecting to your account you will see Jupyter environment start page. 
There is one Jupyter Notebook named: `Test_notebook.ipynb` which shows possibilities of environment and how to use prepared functions to visualise metric data.
You can run basic visualisation for your own data simby by setting few variables and creating DataFrame based on data from OpenSearch:

```
start_time = '2024-06-04T08:15:13.908Z' # Desired start time
end_time = '2024-06-04T11:05:20.908Z' # Desired end time
dict_data = {"metric.attributes.user": "user_name", "name": "metric_name"}

df = read_data_to_df(dict_data, start_time, end_time)
```

You can set multiple filters using `dict_data` to refine your queries. Below are the available options:

- **`metric.attributes.array_job_id`**: Identifier of the array job in SLURM.
- **`metric.attributes.case_number`**: Name of the patient in the MEE environment (useful only with MEE).
- **`metric.attributes.node_id`**: Identifier of the node that computes the job.
- **`metric.attributes.pipeline_id`**: Pipeline number identifier (useful only with MEE).
- **`metric.attributes.pipeline_identifier`**: Full identifier of the MEE pipeline (useful only with MEE).
- **`metric.attributes.pipeline_name`**: Name of the pipeline in MEE (useful only with MEE).
- **`metric.attributes.slurm_job_id`**: SLURM job identifier.
- **`metric.attributes.step_name`**: Name of the step in MEE (useful only with MEE).
- **`metric.attributes.user`**: Username in the SLURM environment.

The `Test_notebook.ipynb` includes several preconfigured visualization functions designed to provide valuable insights into resource utilization. However, the most significant advantage of the APM Data Analyzer lies in its full customizability, enabling users to develop bespoke functions and perform tailored data aggregations to meet specific analytical requirements.

# Resources:
- Cyfronet AGH Ares: https://www.cyfronet.pl/en/computers/18827,artykul,ares_supercomputer.html
- https://grafana.com/grafana/plugins/grafana-opensearch-datasource/ - OpenSearch plugin for Grafana
