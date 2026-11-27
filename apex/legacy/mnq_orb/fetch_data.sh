#!/usr/bin/env bash
# Downloads the public NQ/MNQ 1-minute data used for the backtest (not committed here: ~80 MB).
# Source: https://github.com/s-k-28/nq-es-trader-5k-payout (data/ folder)
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d data_src ]; then
  git clone --depth 1 --filter=blob:none --no-checkout https://github.com/s-k-28/nq-es-trader-5k-payout data_src
fi
cd data_src
git checkout HEAD -- data/Dataset_NQ_1min_2022_2025.csv data/NQ_5min.csv data/mnq_2026_1min.csv
echo "Data ready in research/data_src/data/"
