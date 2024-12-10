# Observability:
Observability is project focused on bringing monitoring to scientific applications.
It is designed to work with supercomputer from Cyfronet AGH (Ares) 

# System:
System for collecting, storing and providing access to monitoring data is build from several components. Below diagram ilustrates connections between them:

![monitoring workflow](https://github.com/user-attachments/assets/b62096c2-37a3-48fe-9ed5-61463f4ddb08)



# Usage:
 
To use monitoring in your calculations on mee you have to add to your liquid.sh file these script lines:

```
wget -q https://raw.githubusercontent.com/SanoScience/observability/main/monitoring.sh https://raw.githubusercontent.com/SanoScience/observability/main/monitoring-env.yml
source monitoring.sh
CASE_NUMBER=`param_or_empty {{ case_number }}`; PIPELINE_IDENTIFIER=`param_or_empty {{ pipeline_identifier }}`; PIPELINE_NAME=`param_or_empty {{ pipeline_name }}`; STEP_NAME=`param_or_empty {{ step_name }}`

setup_conda monitoring-env.yml
install_packages`
run_monitoring "--custom-labels case_number:$CASE_NUMBER pipeline_identifier:$PIPELINE_IDENTIFIER pipeline_name:$PIPELINE_NAME step_name:$STEP_NAME" &
```

There can be multiple name of labels (ex: label1) and for every label one value (ex: value1)

# Resources:
- Cyfronet AGH Ares: https://www.cyfronet.pl/en/computers/18827,artykul,ares_supercomputer.html
- https://grafana.com/grafana/plugins/grafana-opensearch-datasource/ - OpenSearch plugin for Grafana
