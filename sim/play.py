import collections
import json
import statistics
import sys
import time
from pathlib import Path

from tqdm import tqdm

from sim.cpu import CPUSim
from sim.strategy import RandomStrategy, StrategyProvider


def simulate(n, results_dir=None, stepped=False):
    results = collections.defaultdict(lambda: collections.defaultdict(list))
    players = 2
    if results_dir:
        outdir = Path(results_dir)
        outdir.mkdir(exist_ok=False)
    else:
        outdir = None
    for i in tqdm(range(n)):
        start = time.time()
        game = CPUSim(players, StrategyProvider.constant(RandomStrategy()), step=stepped)
        turns = game.run()
        end = time.time()
        if outdir:
            with open(outdir / f"{i}.pickle", "wb") as f:
                game.save_buffers(f)
        results[players]["time"].append(end - start)
        results[players]["turns"].append(turns)
    for pc, data in results.items():
        meantime = statistics.mean(data['time'])
        medtime = statistics.median(data['time'])
        meanturn = statistics.mean(data['turns'])
        medturn = statistics.median(data['turns'])
        tpt = []
        for totaltime, turns in zip(data['time'], data['turns']):
            tpt.append(totaltime / turns)
        meantpt = statistics.mean(tpt)
        dat = {
            "meantime": meantime,
            "mediantime": medtime,
            "meanturn": meanturn,
            "medianturn": medturn,
            "mean_time_per_turn": meantpt,
        }
        print(f"For {pc} players:")
        print(json.dumps(dat, indent=4))

if __name__ == "__main__":
    try:
        outdir = sys.argv[1]
    except:
        outdir = None
    try:
        step = sys.argv[2]
    except:
        step = False
    simulate(20, outdir, step)

