#!/usr/bin/env python
"""
Script to download OHLCV data for a single exchange from CCXT periodically.

Use as:
> im_v2/ccxt/data/extract/download_exchange_data_to_db_periodically.py \
    --download_mode 'periodic_1min' \
    --downloading_entity 'manual' \
    --action_tag 'downloaded_1min' \
    --vendor 'ccxt' \
    --exchange_id 'binance' \
    --universe 'v7' \
    --db_stage 'dev' \
    --db_table 'ccxt_ohlcv_test' \
    --aws_profile 'ck' \
    --data_type 'ohlcv' \
    --data_format 'postgres' \
    --contract_type 'spot' \
    --interval_min '1' \
    --start_time '2022-05-16 00:45:00' \
    --stop_time '2022-05-16 00:55:00' \
    --method 'rest'
"""

import argparse
import logging

import helpers.hdbg as hdbg
import helpers.hparser as hparser
import helpers.hs3 as hs3
import im_v2.common.data.extract.extract_utils as imvcdeexut
import im_v2.common.db.db_utils as imvcddbut

_LOG = logging.getLogger(__name__)


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--websocket_data_buffer_size",
        required=False,
        type=int,
        help="Number of websocket messages to cache before attempting DB insert",
    )
    parser.add_argument(
        "--db_saving_mode",
        action="store",
        required=False,
        type=str,
        default="on_buffer_full",
        choices=["on_buffer_full", "on_sufficient_time"],
        help="Specifies the database saving mode. \n"
        "on_buffer_full: Save data to the database when the buffer is full. \n"
        "on_sufficient_time: Save data to the database based on a predefined time interval.",
    )
    parser = imvcdeexut.add_periodical_download_args(parser)
    parser = hparser.add_verbosity_arg(parser)
    parser = imvcddbut.add_db_args(parser)
    parser = hs3.add_s3_args(parser)
    return parser  # type: ignore[no-any-return]


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if args.websocket_data_buffer_size is not None:
        hdbg.dassert_eq(args.method, "websocket")
        _LOG.warning(
            "max_buffer_size is changed from %d to %d",
            imvcdeexut.WEBSOCKET_CONFIG[args.data_type]["max_buffer_size"],
            args.websocket_data_buffer_size,
        )
        imvcdeexut.WEBSOCKET_CONFIG[args.data_type][
            "max_buffer_size"
        ] = args.websocket_data_buffer_size
    # Check that arguments correspond to the table name,
    # e.g. `ohlcv` and `futures` in `ccxt_ohlcv_futures`.
    hdbg.dassert_in(args.data_type, args.db_table)
    hdbg.dassert_in(args.contract_type, args.db_table)
    # Initialize the Extractor class.
    exchange = imvcdeexut.get_CcxtExtractor(args.exchange_id, args.contract_type)
    args = vars(args)
    # The vendor argument is added for compatibility so for CCXT-specific
    #  scripts it should be 'ccxt'.
    hdbg.dassert_eq(args["vendor"], "ccxt")
    imvcdeexut.download_realtime_for_one_exchange_periodically(args, exchange)


if __name__ == "__main__":
    _main(_parse())
