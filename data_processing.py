import pandas as pd
import requests
from api import submit_id_mapping, check_id_mapping_results_ready, get_id_mapping_results_link, get_id_mapping_results_search

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

def get_target_predictions(smiles):
    url = "https://www.ebi.ac.uk/chembl/target-predictions"
    headers = {"Content-Type": "application/json"}
    payload = {"smiles": smiles}

    # 发送POST请求
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        result_df = pd.DataFrame(data)
        result_df.insert(0, "smiles", smiles)
        return result_df
    else:
        print(f"Request failed for {smiles} with status code {response.status_code}")
        return None
