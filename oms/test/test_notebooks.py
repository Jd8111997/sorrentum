"""
Import as:

import oms.test.test_notebooks as otteno
"""

import logging
import os

import pytest

import core.config as cconfig
import dev_scripts.notebooks as dsnrn
import helpers.hgit as hgit
import helpers.hs3 as hs3
import helpers.hserver as hserver
import oms.execution_analysis_configs as oexancon
import reconciliation as reconcil

_LOG = logging.getLogger(__name__)


def build_test_broker_debugging_config(
    system_log_dir: str,
) -> cconfig.ConfigList:
    """
    Default config builder for testing the Master_broker_debugging notebook.
    """
    config_dict = {"system_log_dir": system_log_dir}
    config = cconfig.Config.from_dict(config_dict)
    config_list = cconfig.ConfigList([config])
    return config_list


def build_test_bid_ask_execution_analysis_config(
    system_log_dir: str,
) -> cconfig.ConfigList:
    """
    Default config builder for testing the Master_bid_ask_execution_analysis
    notebook.
    """
    config_list = oexancon.get_bid_ask_execution_analysis_configs(
        system_log_dir,
        "5T",
        test_asset_id=1464553467,
    )
    return config_list


def build_test_master_execution_analysis_config(
    system_log_dir: str,
) -> cconfig.ConfigList:
    """
    Default config builder for testing the Master_execution_analysis notebook.
    """
    id_col = "asset_id"
    universe_version = "v7.1"
    vendor = "CCXT"
    mode = "trade"
    test_asset_id = 1464553467
    bar_duration = "5T"
    child_order_execution_freq = "1T"
    use_historical = True
    config_list = oexancon.build_execution_analysis_configs(
        system_log_dir,
        id_col,
        universe_version,
        vendor,
        mode,
        test_asset_id,
        bar_duration,
        child_order_execution_freq,
        use_historical,
    )
    return config_list


def build_test_broker_portfolio_reconciliation_config(
    system_log_dir: str,
) -> cconfig.ConfigList:
    """
    Default config builder for testing the
    Master_broker_portfolio_reconciliation notebook.
    """
    id_col = "asset_id"
    universe_version = reconcil.extract_universe_version_from_pkl_config(
        system_log_dir
    )
    price_column_name = "twap"
    vendor = "CCXT"
    mode = "trade"
    bar_duration = reconcil.extract_bar_duration_from_pkl_config(system_log_dir)
    config_list = oexancon.build_broker_portfolio_reconciliation_configs(
        system_log_dir,
        id_col,
        universe_version,
        price_column_name,
        vendor,
        mode,
        bar_duration,
    )
    return config_list


class Test_run_master_notebooks(dsnrn.Test_Run_Notebook_TestCase):
    @pytest.mark.superslow("~125 seconds.")
    @pytest.mark.skipif(
        hserver.is_inside_ci(),
        reason="The prod database is not available via GH actions",
    )
    def test_run_master_bid_ask_execution_analysis(self) -> None:
        """
        Run `oms/notebooks/Master_bid_ask_execution_analysis.ipynb` notebook
        end-to-end.
        """
        notebook_path = "oms/notebooks/Master_bid_ask_execution_analysis.ipynb"
        config_builder = (
            "oms.test.test_notebooks.build_test_bid_ask_execution_analysis_config"
        )
        self._run_notebook(notebook_path, config_builder)

    @pytest.mark.superslow("~50 seconds.")
    def test_run_master_broker_debugging(self) -> None:
        """
        Run `oms/notebooks/Master_broker_debugging.ipynb` notebook end-to-end.
        """
        notebook_path = "oms/notebooks/Master_broker_debugging.ipynb"
        config_builder = (
            "oms.test.test_notebooks.build_test_broker_debugging_config"
        )
        self._run_notebook(notebook_path, config_builder)

    @pytest.mark.superslow("~90 seconds.")
    @pytest.mark.skipif(
        hserver.is_inside_ci(),
        reason="The prod database is not available via GH actions",
    )
    def test_run_master_execution_analysis(self) -> None:
        """
        Run `oms/notebooks/Master_execution_analysis.ipynb` notebook end-to-
        end.
        """
        notebook_path = "oms/notebooks/Master_execution_analysis.ipynb"
        config_builder = (
            "oms.test.test_notebooks.build_test_master_execution_analysis_config"
        )
        self._run_notebook(notebook_path, config_builder)

    # TODO(Henry): Move unit test data to s3 when `CcxtLogsReader` is adjusted.
    @pytest.mark.skipif(
        hserver.is_inside_ci(),
        reason="The prod database is not available via GH actions",
    )
    @pytest.mark.superslow("~50 seconds.")
    def test_run_master_broker_portfolio_reconciliation(self) -> None:
        """
        Run `oms/notebooks/Master_broker_portfolio_reconciliation.ipynb`
        notebook end-to-end.
        """
        notebook_path = (
            "oms/notebooks/Master_broker_portfolio_reconciliation.ipynb"
        )
        config_builder = "oms.test.test_notebooks.build_test_broker_portfolio_reconciliation_config"
        self._run_notebook(notebook_path, config_builder)

    def _run_notebook(self, notebook_path: str, config_builder: str) -> None:
        """
        Run the specific notebook end-to-end.
        """
        # Copy test data from S3 to scratch space.
        aws_profile = "ck"
        s3_input_dir = self.get_s3_input_dir()
        scratch_dir = self.get_scratch_space()
        hs3.copy_data_from_s3_to_local_dir(s3_input_dir, scratch_dir, aws_profile)
        # Run the notebook.
        amp_dir = hgit.get_amp_abs_path()
        notebook_path = os.path.join(amp_dir, notebook_path)
        config_builder = f'{config_builder}("{scratch_dir}")'
        self._test_run_notebook(notebook_path, config_builder)
