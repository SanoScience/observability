import requests
import json
import sys
from datetime import datetime


elasticsearch_host = 'http://172.20.29.2:9200'
index_name = 'metrics'

url = f"{elasticsearch_host}/{index_name}/_search"

def create_term_table(attributes, start_time, end_time):
    term_table = []

    for atribute_key in attributes.keys():
        term_table.append({"term": {atribute_key: attributes[atribute_key]}})
    term_table.append({"range": {"time": {"gte": start_time, "lte": end_time}}})

def get_job_ids(term_table, start_time, end_time):
    query = {
        "size": 0,
        "query": {
            "bool": {
            "filter": term_table
            }
        },
        "aggs": {
            "slurm_job_id_count": {
            "terms": {
                "field": "metric.attributes.slurm_job_id.keyword",
                "size": 5000,
                "order": {
                "_key": "desc"
                },
                "min_doc_count": 1
            },
            "aggs": {
                "job_id_count": {
                    "value_count": {
                        "field": "metric.attributes.slurm_job_id.keyword"
                    }
                }
            }
            }
        }
    }

    resp = requests.post(url, json=query)
    raw_data = json.loads(resp.text)

    buckets = raw_data["aggregations"]["slurm_job_id_count"]["buckets"]

    job_ids = set()

    for bucket in buckets:
        job_ids.add(bucket["key"])

    return job_ids


def get_metric_names(term_table, start_time, end_time):

    query = {
        "size": 0,
        "query": {
            "bool": {
                "filter": term_table
            }
        },
        "aggs": {
            "name_count": {
                "terms": {
                    "field": "name.keyword",
                    "size": 100,
                    "order": {
                        "_key": "desc"
                    },
                    "min_doc_count": 1
                },
                "aggs": {
                    "name_doc_count": {
                        "value_count": {
                            "field": "name.keyword"
                        }
                    }
                }
            }
        }
    }

    resp = requests.post(url, json=query)
    raw_data = json.loads(resp.text)

    buckets = raw_data["aggregations"]["name_count"]["buckets"]

    metric_names = set()

    for bucket in buckets:
        metric_names.add(bucket["key"])

    return metric_names


def read_data(attributes, start_time, end_time):

    starting_term_table = []

    for atribute_key in attributes.keys():
        starting_term_table.append({"term": {atribute_key: attributes[atribute_key]}})
    starting_term_table.append({"range": {"time": {"gte": start_time, "lte": end_time}}})

    slurm_job_id_string = "metric.attributes.slurm_job_id"
    metric_name_string = "name"

    job_ids = [attributes[slurm_job_id_string]] if slurm_job_id_string in attributes.keys() else get_job_ids(starting_term_table, start_time, end_time)

    metric_names = [attributes[metric_name_string]] if metric_name_string in attributes.keys() else get_metric_names(starting_term_table, start_time, end_time)

    # print(job_ids)

    # print(metric_names)

    labels = ["time","name","value","unit","metric.attributes.case_number","metric.attributes.pipeline_id","metric.attributes.slurm_job_id","metric.attributes.step_name","metric.attributes.pipeline_name"]

    header = ",".join([f'"{label}"' for label in labels]) + "\n"

    # print(header)

    data = header
    

    for job_id in job_ids:
        new_attributes = attributes.copy()
        if slurm_job_id_string not in attributes.keys():
            new_attributes[slurm_job_id_string] = job_id
        for metric_name in metric_names:
            if metric_name_string not in attributes.keys():
                new_attributes[metric_name_string] = metric_name
            
            term_table = []

            for atribute_key in new_attributes.keys():
                term_table.append({"term": {atribute_key: new_attributes[atribute_key]}})
            term_table.append({"range": {"time": {"gte": start_time, "lte": end_time}}})

            query = {
                "size": 10000,
                "query": {
                    "bool": {
                        "must": term_table
                    }
                },
                "sort": [
                    {"time": {"order": "asc"}}
                ]
            }

            # print(query)

            url = f"{elasticsearch_host}/{index_name}/_search"

            # Send the request
            resp = requests.post(url, json=query)

            raw_data = json.loads(resp.text)

            documents = raw_data["hits"]["hits"]
        

        for document in documents:
            input = []
            for label in labels:
                if label in document["_source"].keys():
                    input.append('"{a}"'.format(a= str(document["_source"][label])))
                else:
                    input.append('""')
            line = ",".join(input) + "\n"
            data += line
        

    return data


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py dictionary start_time end_time")
        sys.exit(1)

    dictionary_str, start_time, end_time = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        dict_data = eval(dictionary_str)
        if not isinstance(dict_data, dict):
            raise ValueError("Invalid dictionary format")
    except Exception as e:
        print("Error: Invalid dictionary format.")
        print(e)
        sys.exit(1)

    data = read_data(dict_data, start_time, end_time)
    print(len(data.splitlines()))

