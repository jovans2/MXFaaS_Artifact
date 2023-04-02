from __future__ import division
from statistics import mean
from collections import defaultdict
from matplotlib import rcParams
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import ast

rcParams['font.serif'] = ['Times']
#plt.style.use('grayscale')
new_params = {
    'axes.labelsize': 70,
    'xtick.labelsize': 70,
    'ytick.labelsize': 70,
    'legend.fontsize': 70,
    'lines.markersize': 15,
    'xtick.major.pad': 0,
    'ytick.major.pad': 10,
    'font.size': 70,
    'grid.linestyle': 'dashdot',
    'patch.edgecolor': 'black',
    'patch.force_edgecolor': True,
    'font.serif': 'Times',
    'grid.alpha': 0.4,
}
mpl.rcParams.update(new_params)

fig, ax = plt.subplots(figsize=(12, 6))

ax2 = ax.twinx()

t_merges = [0, 0.5, 1, 10, 20, 50, 100, 200, 500, 1000]

percent_merged = [0.9933065595716198, 0.9866131191432396, 0.9678714859437751, 0.9397590361445783, 0.8908969210174029, 0.7891566265060241, 0.6941097724230254, 0.47121820615796517, 0.45314591700133866, 0.44176706827309237]
fetch_latency = [1.5534909129142755, 1.3967915058135986, 1.2918736934661864, 1.2442637801170349, 1.0249151706695556, 1.0012211084365845, 0.9711835551261902, 0.9422359085083008, 0.847205429077148, 0.9911181426048279]
percent_merged.reverse()
fetch_latency.reverse()

maxFL = max(fetch_latency)

#for indFL in range(len(fetch_latency)):
#    fetch_latency[indFL] = fetch_latency[indFL] / maxFL

#ax.plot(x1, y1, label="Cloud Storage", color="orange")
ax.set_xscale("log")
lns1 = ax.plot(t_merges, percent_merged, label = "Fraction of merged I/Os", color="black", linewidth=3)
lns2 = ax2.plot(t_merges, fetch_latency, "--", label="Tail Data Access Latency [s]", color="red", linewidth=3)

lns = lns1 + lns2
lbs = [l.get_label() for l in lns]

ax.set_xlabel("$T_{merge}$ [ms]", fontsize=22)
ax.set_ylabel("Fraction of merged I/Os", fontsize=22)
ax2.set_ylabel("Tail Latency [s]", fontsize=22)
ax.tick_params(axis="y", labelsize=20)
ax2.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=20)
ax.set_yticks(np.arange(0.0, 1.1, 0.2))
ax2.set_yticks(np.arange(0.0, 2.1, 0.5))
ax.grid(visible=True, axis='y')
handles, labels = ax.get_legend_handles_labels()
ax.legend(lns, lbs, loc="lower left", mode=None, borderaxespad=0, fancybox=True, shadow=True, ncol=1, frameon=False, fontsize=23)
#ax2.legend(loc="lower left", mode=None, borderaxespad=0, fancybox=True, shadow=True, ncol=1, frameon=False, fontsize=23)
plt.tight_layout()
plt.savefig("sensitivity_tmerge.pdf")
