from matplotlib import pyplot
import matplotlib
import datetime
import pandas

import numpy as np

matplotlib.rcParams['font.size'] = 12

from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

####

PLOT_DATE_FMT = '%b %d %H:%M'
TZONE_DT = datetime.timedelta(hours=-5)
STATE = 'Pennsylvania'

ZOOMBOX = False  # currently only manually set up for GA


minor_dt = 3  # hours
major_dt = 12 # hours

major_loc = matplotlib.dates.HourLocator(interval=major_dt)
minor_loc = matplotlib.dates.HourLocator(interval=minor_dt)
major_fmt = matplotlib.dates.DateFormatter('%b %d %H:%M')
minor_fmt = matplotlib.dates.DateFormatter('%H:%M')

dt0 = datetime.datetime(2020,11,3)
dt1 = datetime.datetime(2020,11,8)


def dproc(inp, formatter="%Y-%m-%d %H:%M:%S.%f", tzone=TZONE_DT):
    # process one or more strings from this table.
    if isinstance(inp,list) or isinstance(inp, np.ndarray):
        return [dproc(i, formatter=formatter) for i in inp]
    #
    try:
        return datetime.datetime.strptime(inp, formatter) + tzone
    except:
        return np.nan
#


df = pandas.read_csv('battleground-state-changes.csv')

# need to get rid of junk after state name.
df['state'] = [s.split(' ')[0] for s in df['state'].values]

# create new column
df['votes_counted'] = df['leading_candidate_votes'] + df['trailing_candidate_votes']


# create new columns
df['votes_counted'] = df['leading_candidate_votes'] + df['trailing_candidate_votes']

# Fix vote differential to go into negatives (instead of flipping candidate).
name_map = {'Trump':1, 'Biden':-1}
candidate_sign = np.array([ name_map[name] for name in df['leading_candidate_name'].values ])
df['signed_vote_differential'] = candidate_sign*df['vote_differential']

df['fractional_lead'] = df['signed_vote_differential'].values/(df['votes_counted'].values + df['votes_remaining'].values)




# Fix vote differential to go into negatives (instead of flipping candidate).
name_map = {'Trump':1, 'Biden':-1}
candidate_sign = np.array([ name_map[name] for name in df['leading_candidate_name'].values ])
df['signed_vote_differential'] = candidate_sign*df['vote_differential']


# Select out the desired state.
df_sub = df.loc[df['state']==STATE]

df_sub = df_sub.sort_values(by='timestamp')

# replace timestamp with actual datetime object (currently just strings)
timestamps = dproc(df_sub['timestamp'].values)
df_sub['timestamp'] = timestamps

# reduce to datetime window of interest.
df_sub = df_sub.loc[df_sub['timestamp'] > dt0].loc[df_sub['timestamp'] < dt1]

# get best-fit line from data from Nov 4.
day = np.array([t.day for t in timestamps])


idx = np.where(day==4)[0]
coef = np.polyfit(df_sub['votes_counted'].values[idx], df_sub['signed_vote_differential'].values[idx], 1)

fitx = df_sub['votes_counted'].values[[0,-1]]
fitx += np.array([-.02e6, +.02e6], dtype=int)
fity = np.polyval(coef, fitx)

############
#
# visualization
#
fig,ax = pyplot.subplots(2,1, sharex=True, constrained_layout=True, figsize=(12,6))

t = df_sub['timestamp'].values

ax[0].plot(t, df_sub['votes_remaining'].values, marker='.', c='k')
ax[1].plot(t, df_sub['signed_vote_differential'].values, marker='.', c='r')

for axi in ax:
    axi.grid()
    yr = axi.get_ylim()
    mag = 10**(np.floor(np.log10(yr[1]-yr[0]))-1)
    axi.set_ylim([-mag, yr[1]])
#


ax[0].set_ylabel('votes_remaining')
ax[1].set_ylabel('vote_differential')

ax[1].xaxis.set_major_locator(major_loc)
ax[1].xaxis.set_minor_locator(minor_loc)
ax[1].xaxis.set_major_formatter(major_fmt)
ax[1].xaxis.set_minor_formatter(minor_fmt)
pyplot.setp(ax[1].get_xticklabels(), rotation=70, horizontalalignment='right')

fig.suptitle('%s remaining vote timeline'%STATE)

fig.show()

fig2,ax2 = pyplot.subplots(1,1, constrained_layout=True, figsize=(12,8))

ax2.scatter(df_sub['votes_counted'].values, 
    df_sub['signed_vote_differential'].values, 
    marker='.', 
    s=200, 
    c=[t.timestamp() for t in timestamps],
    cmap = pyplot.cm.inferno_r
)

ax2.set_xlabel('Votes counted')
ax2.set_ylabel('Trump vote lead')

if ZOOMBOX:
    ax2z = zoomed_inset_axes(ax2, zoom=3, loc='lower left', borderpad=4)

    mark_inset(ax2, ax2z, loc1=1, loc2=3)
    ax2z.set_xlim([4.88e6, 4.91e6])
    ax2z.set_ylim([-0.5e4, 1e4])
    ax2z.scatter(df_sub['votes_counted'].values, 
        df_sub['signed_vote_differential'].values, 
        marker='.', 
        s=200, 
        c=[t.timestamp() for t in timestamps],
        cmap = pyplot.cm.inferno_r
    )
#

# annotation
x = df_sub['votes_counted'].values
y = df_sub['signed_vote_differential'].values

MIN_STEP = 4 # hours
tref = -999
for i,t in enumerate(timestamps):
    if t.timestamp() - tref > MIN_STEP*60*60:
        tref = t.timestamp()
        xx = x[i]
        yy = y[i]
        ax2.annotate( t.strftime(PLOT_DATE_FMT), (xx, yy), ha='left' )
        if ZOOMBOX:
            ax2z.annotate( t.strftime(PLOT_DATE_FMT), (xx, yy), ha='left' )
#

###############
# Trendline

ax2.plot(fitx,fity, ls='--', lw=1)

if ZOOMBOX:
    ax2z.plot(fitx,fity, ls='--', lw=1)

if False:
    ax2.annotate('Linear fit for Nov 4 data only', 
        xy=(x[idx[-1]], y[idx[-1]]),
        xytext=(x[idx[-1]]+0.04e6, y[idx[-1]]+2e4),
        arrowprops={
            'arrowstyle': 'simple',
            'color': [0.5,0.5,0.5,0.5]
        },
        fontsize=10
        )

#####

ax2.yaxis.grid()
if ZOOMBOX:
    ax2z.yaxis.grid()
    ax2z.set_xticklabels([]) # remove
    ax2zyt = ax2z.get_yticks()

    ax2z.set_yticks([ ax2zyt[0], 0, ax2zyt[-1] ])
    ax2z.set_facecolor('#eee')
#

fig2.show()

fig2.suptitle('%s vote counting'%STATE)

fig2.savefig('%s_diff_vs_count.png'%(STATE.lower()), dpi=120)

pyplot.ion()
