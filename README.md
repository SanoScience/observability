# Observability:
Observability is project focused on bringing monitoring to scientific applications.
It is designed to work with supercomputer from Cyfronet AGH (Ares) 

# System:
System for collecting, storing and providing access to monitoring data is build from several components. Below diagram ilustrates connections between them:

![image](https://github.com/SanoScience/observability/assets/72197032/38ab2f3a-b0c0-43b6-bc0d-5b0307f2a26d)


# Usage:
 
To use monitoring in your calculations on mee you have to add to your liquid.sh file these script lines:

```
wget -q https://raw.githubusercontent.com/SanoScience/observability/main/monitoring.sh https://raw.githubusercontent.com/SanoScience/observability/main/monitoring-env.yml
source monitoring.sh
CASE_NUMBER=`param_or_empty {{ case_number }}`; PIPELINE_IDENTIFIER=`param_or_empty {{ pipeline_identifier }}`; PIPELINE_NAME=`param_or_empty {{ pipeline_name }}`; STEP_NAME=`param_or_empty {{ step_name }}`

setup_conda monitoring-env.yml
install_packages`
run_monitoring "--case-number $CASE_NUMBER --pipeline-identifier $PIPELINE_IDENTIFIER --pipeline-name $PIPELINE_NAME --step-name $STEP_NAME" &
```

There can be adde custom labels to metrics for achieving additional information during data processing:

 ```
wget -q https://raw.githubusercontent.com/SanoScience/observability/main/monitoring.sh https://raw.githubusercontent.com/SanoScience/observability/main/monitoring-env.yml
source monitoring.sh
CASE_NUMBER=`param_or_empty {{ case_number }}`; PIPELINE_IDENTIFIER=`param_or_empty {{ pipeline_identifier }}`; PIPELINE_NAME=`param_or_empty {{ pipeline_name }}`; STEP_NAME=`param_or_empty {{ step_name }}`

setup_conda monitoring-env.yml
install_packages`
run_monitoring "--case-number $CASE_NUMBER --pipeline-identifier $PIPELINE_IDENTIFIER --pipeline-name $PIPELINE_NAME --step-name $STEP_NAME --custom-labels label1:value1 label2:value2" &
```
There can be multiple name of labels (ex: label1) and for every label one value (ex: value1)

# Resources:
- Cyfronet AGH Ares: https://www.cyfronet.pl/en/computers/18827,artykul,ares_supercomputer.html
- https://grafana.com/grafana/plugins/grafana-opensearch-datasource/ - OpenSearch plugin for Grafana
