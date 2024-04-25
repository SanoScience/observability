FROM jupyter/datascience-notebook

# Install additional dependencies
RUN conda install --quiet --yes pandas


COPY read_data.py /home/jovyan/
COPY Test_notebook.ipynb /home/jovyan/work

# Set the notebook directory
USER jovyan
WORKDIR /home/jovyan