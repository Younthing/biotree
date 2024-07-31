import re
import time
import json
import zlib
from xml.etree import ElementTree
from urllib.parse import urlparse, parse_qs, urlencode
import logging
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd

from biotree.utils.decorator import batch_query_decorator, input_handler_decorator

logger = logging.getLogger("biotree.smiles_to_target.chembal")


# smiles_to_target/chembal.py
def original_function():
    print("This is the original function.")


## 官方API
POLLING_INTERVAL = 3
API_URL = "https://rest.uniprot.org"


retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retries))


def check_response(response):
    try:
        response.raise_for_status()
    except requests.HTTPError:
        print(response.json())
        raise


def submit_id_mapping(from_db, to_db, ids):
    request = requests.post(
        f"{API_URL}/idmapping/run",
        data={"from": from_db, "to": to_db, "ids": ",".join(ids)},
        timeout=600,
    )
    check_response(request)
    return request.json()["jobId"]


def get_next_link(headers):
    re_next_link = re.compile(r'<(.+)>; rel="next"')
    if "Link" in headers:
        match = re_next_link.match(headers["Link"])
        if match:
            return match.group(1)


def check_id_mapping_results_ready(job_id):
    while True:
        request = session.get(f"{API_URL}/idmapping/status/{job_id}")
        check_response(request)
        j = request.json()
        if "jobStatus" in j:
            if j["jobStatus"] == "RUNNING":
                print(f"Retrying in {POLLING_INTERVAL}s")
                time.sleep(POLLING_INTERVAL)
            else:
                raise Exception(j["jobStatus"])
        else:
            return bool(j["results"] or j["failedIds"])


def get_batch(batch_response, file_format, compressed):
    batch_url = get_next_link(batch_response.headers)
    while batch_url:
        batch_response = session.get(batch_url)
        batch_response.raise_for_status()
        yield decode_results(batch_response, file_format, compressed)
        batch_url = get_next_link(batch_response.headers)


def combine_batches(all_results, batch_results, file_format):
    if file_format == "json":
        for key in ("results", "failedIds"):
            if key in batch_results and batch_results[key]:
                all_results[key] += batch_results[key]
    elif file_format == "tsv":
        return all_results + batch_results[1:]
    else:
        return all_results + batch_results
    return all_results


def get_id_mapping_results_link(job_id):
    url = f"{API_URL}/idmapping/details/{job_id}"
    request = session.get(url)
    check_response(request)
    return request.json()["redirectURL"]


def decode_results(response, file_format, compressed):
    if compressed:
        decompressed = zlib.decompress(response.content, 16 + zlib.MAX_WBITS)
        if file_format == "json":
            j = json.loads(decompressed.decode("utf-8"))
            return j
        elif file_format == "tsv":
            return [line for line in decompressed.decode("utf-8").split("\n") if line]
        elif file_format == "xlsx":
            return [decompressed]
        elif file_format == "xml":
            return [decompressed.decode("utf-8")]
        else:
            return decompressed.decode("utf-8")
    elif file_format == "json":
        return response.json()
    elif file_format == "tsv":
        return [line for line in response.text.split("\n") if line]
    elif file_format == "xlsx":
        return [response.content]
    elif file_format == "xml":
        return [response.text]
    return response.text


def get_xml_namespace(element):
    m = re.match(r"\{(.*)\}", element.tag)
    return m.groups()[0] if m else ""


def merge_xml_results(xml_results):
    merged_root = ElementTree.fromstring(xml_results[0])
    for result in xml_results[1:]:
        root = ElementTree.fromstring(result)
        for child in root.findall("{http://uniprot.org/uniprot}entry"):
            merged_root.insert(-1, child)
    ElementTree.register_namespace("", get_xml_namespace(merged_root[0]))
    return ElementTree.tostring(merged_root, encoding="utf-8", xml_declaration=True)


def print_progress_batches(batch_index, size, total):
    n_fetched = min((batch_index + 1) * size, total)
    # print(f"Fetched: {n_fetched} / {total}")


def get_id_mapping_results_search(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    file_format = query["format"][0] if "format" in query else "json"
    if "size" in query:
        size = int(query["size"][0])
    else:
        size = 500
        query["size"] = size
    compressed = (
        query["compressed"][0].lower() == "true" if "compressed" in query else False
    )
    parsed = parsed._replace(query=urlencode(query, doseq=True))
    url = parsed.geturl()
    request = session.get(url)
    check_response(request)
    results = decode_results(request, file_format, compressed)
    total = int(request.headers["x-total-results"])
    print_progress_batches(0, size, total)
    for i, batch in enumerate(get_batch(request, file_format, compressed), 1):
        results = combine_batches(results, batch, file_format)
        print_progress_batches(i, size, total)
    if file_format == "xml":
        return merge_xml_results(results)
    return results


def get_id_mapping_results_stream(url):
    if "/stream/" not in url:
        url = url.replace("/results/", "/results/stream/")
    request = session.get(url)
    check_response(request)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    file_format = query["format"][0] if "format" in query else "json"
    compressed = (
        query["compressed"][0].lower() == "true" if "compressed" in query else False
    )
    return decode_results(request, file_format, compressed)


## 自己实现的 ######################################################################


def convert_results_to_dataframe(results):
    rows = []
    for result in results["results"]:
        from_value = result["from"]
        primary_accession = result["to"]["primaryAccession"]
        genes = result["to"]["genes"]
        genes_value = genes[0]["geneName"]["value"] if genes else None
        organism = result["to"]["organism"]["scientificName"]

        rows.append([from_value, primary_accession, genes_value, organism])

    df = pd.DataFrame(
        rows, columns=["chembal", "uniport_accession", "gene_name", "organism"]
    )

    return df


def get_dataframe_from_ids(ids):
    job_id = submit_id_mapping(from_db="ChEMBL", to_db="UniProtKB", ids=ids)
    if check_id_mapping_results_ready(job_id):
        link = get_id_mapping_results_link(job_id)
        results_dict = get_id_mapping_results_search(link)
        return convert_results_to_dataframe(results_dict)


@input_handler_decorator
@batch_query_decorator
def get_target_predictions(smiles):
    url = "https://www.ebi.ac.uk/chembl/target-predictions"
    headers = {"Content-Type": "application/json"}
    payload = {"smiles": smiles}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=600)
        response.raise_for_status()  # 如果响应状态不是200，抛出HTTPError异常

        data = response.json()
        result_df = pd.DataFrame(data)
        result_df.insert(0, "smiles", smiles)
        return result_df
    except requests.exceptions.RequestException as e:
        logger.error("Request failed for %s with error: %s", smiles, e)
        return None


## 合并
def add_gene_name_to_predictions(smiles):
    # 获取目标预测数据
    df_predictions = get_target_predictions(smiles)
    # 只保留 organism 为 Homo sapiens 且 80% 列为 active 的行
    df_filtered = df_predictions[
        (df_predictions["organism"] == "Homo sapiens")
        & (df_predictions["80%"] == "active")
    ]
    # 提取所有唯一的 target_chemblid
    unique_chembl_ids = df_filtered["target_chemblid"].unique().tolist()

    # 获取基因名数据
    df_genes = get_dataframe_from_ids(unique_chembl_ids)

    # 只保留必要的列以减少内存使用
    df_genes = df_genes[["chembal", "gene_name"]]

    # 合并两个 DataFrame，按 chembal 和 target_chemblid 列进行合并
    df_merged = pd.merge(
        df_filtered,
        df_genes,
        left_on="target_chemblid",
        right_on="chembal",
        how="left",
    )

    # 删除不需要的列
    df_merged = df_merged.drop(columns=["chembal"])

    return df_merged


# if __name__ == "__main__":
#     # 使用示例
#     smiles = "CC(C)C1=CC=C(C=C1)C(C)C(=O)O"
#     result_df = add_gene_name_to_predictions(smiles)
#     print(result_df)
