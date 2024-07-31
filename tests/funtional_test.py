import pandas as pd
import pytest
from biotree.smiles_to_target import prediction


@pytest.fixture
def test_smiles():
    return ["CC(C)C1=CC=C(C=C1)C(C)C(=O)O", "CCO"]


def test_prediction(test_smiles):
    # 调用预测函数
    target_df = prediction(test_smiles)

    # 检查结果是否为pandas DataFrame且非空
    assert (
        isinstance(target_df, pd.DataFrame) and not target_df.empty
    ), "预测结果应该为非空的DataFrame"

    # 检查返回的DataFrame的行数是否符合预期
    assert len(target_df) != 0, "返回的DataFrame行数应不为0"
