import requests
import json

resp = requests.get('http://localhost:9200/metrics/_search?q=name%3Aslurm_job_memory_total_rss%20AND%20metric.attributes.user%3Aplgczerepak%20AND%20time%3A%5B2023-11-11T11%3A48%3A47.908292746Z%20TO%202023-11-11T11%3A48%3A47.908292746Z%5D')

raw_data = json.loads(resp.text)

documents = raw_data["hits"]["hits"]

atributes = {"time", "name", "value"}
for document in documents:
    for key in document["_source"].keys():
        print(key)

