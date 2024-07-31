import logging
import pandas as pd
from pathlib import Path
from functools import wraps
from collections.abc import Iterable

# 获取 logger
logger = logging.getLogger("biotree.utils.decorator")


def input_handler_decorator(func):
    @wraps(func)
    def wrapper(smiles_input):
        smiles_iterable = []
        if isinstance(smiles_input, (str, Path)):
            # 处理字符串或Path对象
            path = Path(smiles_input)
            if path.is_file():
                try:
                    with path.open("r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                smiles_iterable.append(line.split()[0])
                    logger.info(f"Read {len(smiles_iterable)} SMILES from {path}")
                except UnicodeDecodeError:
                    logger.error(f"Failed to decode {path} with utf-8 encoding")
                except OSError as e:
                    logger.error(f"Failed to read {path}: {e}")
            else:
                smiles_iterable.append(str(smiles_input))
        elif isinstance(smiles_input, Iterable):
            # 处理可迭代对象
            smiles_iterable.extend(smiles_input)
        else:
            logger.warning(f"Unsupported input type: {type(smiles_input)}")

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
