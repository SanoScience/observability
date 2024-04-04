FROM jupyter/datascience-notebook

# Install additional dependencies
RUN conda install --quiet --yes pandas


COPY /home/ubuntu/conf/observability/read_data.py /home/jovyan/

# Set the notebook directory
USER jovyan
WORKDIR /home/jovyan