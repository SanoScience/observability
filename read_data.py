import requests
import json
import sys
from datetime import datetime


elasticsearch_host = 'http://172.20.29.2:9200'
index_name = 'metrics'

url = f"{elasticsearch_host}/{index_name}/_search"

# def request_database(json_query):


#     # Send the request
#     resp = requests.post(url, json=query)



def get_job_ids(term_table, start_time, end_time):



    query = {
        "size": 0,
        "query": {
            "bool": {
            "filter": [
                {"range": {"time": {"gte": start_time, "lte": end_time}}}
            ]
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

    print(job_ids)


def get_metric_names(term_table, start_time, end_time):

    query = {
        "size": 0,
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "time": {
                                "gte": start_time,
                                "lte": end_time
                            }
                        }
                    }
                ]
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

    print(metric_names)


def read_data(atributes, start_time, end_time):
    start_req = "http://localhost:9200/metrics/_search?q=name%3Aslurm_job_memory_total_rss%20AND%20metric.attributes.user%3Aplgczerepak%20AND%20time%3A%5B2023-11-11T11%3A48%3A47.908292746Z%20TO%202023-11-11T11%3A48%3A47.908292746Z%5D"

    # "name": "slurm_job_memory_total_rss"
    # atributes = {"metric.attributes.user": "plgczerepak", "metric.attributes.pipeline_name": "test"}
    string_atributes = ""
    for atribute_key in atributes.keys():
        string_atributes += atribute_key + "%3A" + atributes[atribute_key] + "%20AND%20"
    # start_time = "2024-03-21T10:17:47.908Z"
    # end_time = "2024-03-21T10:27:47.908Z"
    request = "http://172.20.29.2:9200/metrics/_search?q={}time%3A%5B{}%20TO%20{}%5D".format(string_atributes, start_time, end_time)

    print(request)

    elasticsearch_host = 'http://172.20.29.2:9200'
    index_name = 'metrics'


 
    # Define the query parameters

    # start_time = "2024-03-21 10:17:47"
    # end_time = "2024-03-21 10:27:47"
    # start_datetime_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    # end_datetime_obj = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    # Converting to epoch milliseconds
    # gte = int(start_datetime_obj.timestamp() * 1000)
    # print(gte)
    # lte = int(end_datetime_obj.timestamp() * 1000)
    # print(lte)

    term_table = []

    for atribute_key in atributes.keys():
        term_table += {"term": {atribute_key: atributes[atribute_key]}}
    term_table += {"range": {"time": {"gte": start_time, "lte": end_time}}}

    get_job_ids(term_table, start_time, end_time)
    get_metric_names(term_table, start_time, end_time)


    query = {
        "size": 10000,
        "query": {
            "bool": {
                "must": term_table
            }
        },
        "aggs": {
                "sampled_data": {
                    "date_histogram": {
                        "field": "time",
                        "interval": "5s",
                        "min_doc_count": 0,
                        "order": {"_key": "asc"}
                    }
                }
            },
        "sort": [
            {"time": {"order": "asc"}}
        ]
    }


    url = f"{elasticsearch_host}/{index_name}/_search"

    # Send the request
    resp = requests.post(url, json=query)


    # resp = requests.get(request)

    # print(resp)

    raw_data = json.loads(resp.text)

    print(raw_data)

    documents = raw_data["aggregations"]["sampled_data"]

    # print("\n nowa linia \n")
    # print(documents)

    atributes = ["time", "name", "value", "unit"]
    for document in documents:
        # print(document)
        for key in document["_source"].keys():
            if key.startswith("metric.attributes") and key not in atributes:
                atributes.append(key)


    header = ",".join([f'"{atribute}"' for atribute in atributes]) + "\n"
    # print(header)

    data = header

    for document in documents:
        input = []
        for atribute in atributes:
            if atribute in document["_source"].keys():
                input.append('"{a}"'.format(a= str(document["_source"][atribute])))
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

    print(read_data(dict_data, start_time, end_time))
