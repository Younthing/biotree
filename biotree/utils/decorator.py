import logging
import pandas as pd
import os
from functools import wraps
from collections.abc import Iterable

# 获取 logger
logger = logging.getLogger("biotree.utils.decorator")


def input_handler_decorator(func):
    @wraps(func)
    def wrapper(smiles_input):
        # 检查输入是否为单个对象，如果是则转换为包含该对象的列表
        if not isinstance(smiles_input, Iterable) or isinstance(
            smiles_input, (str, bytes)
        ):
            smiles_iterable = [smiles_input]
            logger.info("Input is a single object, converted to a list.")
        else:
            # 如果输入是文件路径，读取文件的第一列
            if isinstance(smiles_input, str) and os.path.isfile(smiles_input):
                try:
                    with open(smiles_input, "r") as file:
                        smiles_iterable = [line.split()[0] for line in file]
                    logger.info("Input is a file path, read the first column.")
                except Exception as e:
                    logger.error(
                        "Failed to read the file: %s. Error: %s", smiles_input, str(e)
                    )
                    raise e
            else:
                smiles_iterable = smiles_input

        return func(smiles_iterable)

    return wrapper


def batch_query_decorator(func):
    @wraps(func)
    def wrapper(smiles_iterable):
        logger.info("Batch query started with %d SMILES.", len(smiles_iterable))
        results = []
        failed_smiles = []
        success_count = 0
        failure_count = 0

        for smiles in smiles_iterable:
            logger.info("Querying target predictions for: %s", smiles)
            try:
                result = func(smiles)
                if result is not None:
                    results.append(result)
                    success_count += 1
                    logger.info("Query successful for: %s", smiles)
                else:
                    raise ValueError("Result is None")
            except Exception as e:
                failure_count += 1
                failed_smiles.append(smiles)
                logger.warning("No result for: %s. Error: %s", smiles, str(e))

        if results:
            combined_df = pd.concat(results, ignore_index=True)
        else:
            combined_df = pd.DataFrame()  # 返回空的 DataFrame 以保持返回类型一致

        # 记录批量查询结果
        logger.info(
            "Batch query completed: %d succeeded, %d failed out of %d.",
            success_count,
            failure_count,
            len(smiles_iterable),
        )

        if failed_smiles:
            logger.debug("Failed SMILES: %s", ", ".join(failed_smiles))

        return combined_df

    return wrapper
