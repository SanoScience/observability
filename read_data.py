import requests
import json
import sys

def read_data(atributes, start_time, end_time):
    start_req = "http://localhost:9200/metrics/_search?q=name%3Aslurm_job_memory_total_rss%20AND%20metric.attributes.user%3Aplgczerepak%20AND%20time%3A%5B2023-11-11T11%3A48%3A47.908292746Z%20TO%202023-11-11T11%3A48%3A47.908292746Z%5D"

    # "name": "slurm_job_memory_total_rss"
    # atributes = {"metric.attributes.user": "plgczerepak", "metric.attributes.pipeline_name": "test"}
    string_atributes = ""
    for atribute_key in atributes.keys():
        string_atributes += atribute_key + "%3A" + atributes[atribute_key] + "%20AND%20"
    # start_time = "2023-11-11T11%3A48%3A47.908Z"
    # end_time = "2023-11-11T11%3A48%3A47.909Z"
    request = "http://localhost:9200/metrics/_search?q={}time%3A%5B{}%20TO%20{}%5D".format(string_atributes, start_time, end_time)

    # print(request)

    resp = requests.get(request)

    # print(resp)

    raw_data = json.loads(resp.text)

    # print(raw_data)

    documents = raw_data["hits"]["hits"]

    atributes = ["time", "name", "value", "unit"]
    for document in documents:
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
