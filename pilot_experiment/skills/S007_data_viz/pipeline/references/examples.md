# Loading and processing neural data
df = pd.read_csv('neural_data.csv')
neuron_cols = [col for col in df.columns if col.startswith('neuron_')]

# Efficient population mean calculation
neuron_data = df[neuron_cols].values
pop_means = np.nanmean(neuron_data, axis=1)

# Proper trial-averaged statistics
pivot_data = df.pivot_table(index='trial', columns='time', values='pop_mean')
time_mean = pivot_data.mean(axis=0, skipna=True)
time_sem = pivot_data.sem(axis=0, skipna=True).fillna(0)

# Adaptive y-axis labeling
n_neurons = len(neuron_cols)
if n_neurons <= 20:
    plt.yticks(range(n_neurons), neuron_cols)
elif n_neurons <= 100:
    step = 5
    tick_indices = range(0, n_neurons, step)
    plt.yticks(tick_indices, [neuron_cols[i] for i in tick_indices])
else:
    n_ticks = 10
    tick_indices = np.linspace(0, n_neurons-1, n_ticks, dtype=int)
    plt.yticks(tick_indices, [f'neuron_{i}' for i in tick_indices])

# Memory-efficient fallback for large datasets
try:
    pivot_data = df.pivot_table(index='trial', columns='time', values='pop_mean')
except MemoryError:
    time_stats = df.groupby('time')['pop_mean'].agg(['mean', 'sem'])
