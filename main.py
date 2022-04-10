import collections
import json
import statistics
import sys
import time

from tqdm import tqdm

from sim.cpu import CPUSim
from sim.strategy import FifoStrategy, StrategyProvider


def simulate(n, stepped=False):
    results = collections.defaultdict(lambda: collections.defaultdict(list))
    players = 2
    for i in tqdm(range(n)):
        start = time.time()
        game = CPUSim(players, StrategyProvider.constant(FifoStrategy()), step=stepped)
        turns = game.run()
        end = time.time()
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
        step = sys.argv[1]
    except:
        step = False
    simulate(20, step)

