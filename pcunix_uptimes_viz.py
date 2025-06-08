import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import numpy as np

def load_and_validate_csvs(csv_files):
    """Load and validate CSV files, returning combined data and file labels."""
    if not csv_files:
        print("No CSV files provided. Exiting.")
        return None, None

    all_data = []
    file_labels = []

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            if 'Node_ID' not in df.columns or 'Reachable' not in df.columns:
                print(f"Warning: Skipping {file_path}. Missing 'Node_ID' or 'Reachable' column.")
                continue
            file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]
            df['Scan_Label'] = file_name_without_ext
            all_data.append(df)
            file_labels.append(file_name_without_ext)
        except FileNotFoundError:
            print(f"Error: File not found - {file_path}")
        except pd.errors.EmptyDataError:
            print(f"Warning: {file_path} is empty. Skipping.")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    if not all_data:
        print("No valid data found in the provided CSV files. Exiting.")
        return None, None

    return all_data, file_labels

def process_data(all_data, file_labels):
    """Process data into a pivot table for heatmap plotting."""
    combined_df = pd.concat(all_data, ignore_index=True)
    pivot_table = combined_df.pivot_table(
        index='Node_ID',
        columns='Scan_Label',
        values='Reachable',
        aggfunc='first'
    )
    pivot_table = pivot_table.reindex(columns=file_labels, fill_value=0)
    pivot_table = pivot_table.sort_index(ascending=True)
    return pivot_table

def setup_plot_dimensions(pivot_table):
    """Calculate dynamic figure dimensions based on data size."""
    num_nodes = len(pivot_table.index)
    num_scans = len(pivot_table.columns)
    cell_size = 0.3
    fig_width = max(8, num_scans * cell_size + 2)
    fig_height = max(6, num_nodes * cell_size + 2)
    return fig_width, fig_height

def configure_axes(ax, pivot_table, num_nodes, num_scans):
    """Configure axes, labels, and grid for the heatmap."""
    ax.set_xticks(np.arange(-0.5, num_scans, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, num_nodes, 1), minor=True)
    ax.grid(which="minor", color="gray", linestyle='-', linewidth=0.5)
    ax.tick_params(which="minor", size=0)

    ax.set_xticks(range(num_scans))
    ax.set_xticklabels(pivot_table.columns, rotation=45, ha='right', fontsize=8)
    ax.set_xlabel('Scan Time (Filename)')

    all_y_ticks = np.arange(num_nodes)
    all_y_labels = pivot_table.index.tolist()
    label_stride = 5 if num_nodes <= 50 else 10 if num_nodes > 100 else 5
    ax.set_yticks(all_y_ticks[::label_stride])
    ax.set_yticklabels(all_y_labels[::label_stride])
    ax.set_ylabel('Unix Node ID')
    ax.tick_params(axis='y', labelsize=8)

    ax.set_title('Cluster Node Uptime Evolution', fontsize=14)

def create_heatmap(pivot_table):
    """Create and configure the heatmap plot."""
    num_nodes = len(pivot_table.index)
    num_scans = len(pivot_table.columns)
    fig_width, fig_height = setup_plot_dimensions(pivot_table)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    cmap = mcolors.ListedColormap(['red', 'green'])
    bounds = [-0.5, 0.5, 1.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    ax.imshow(pivot_table.values, cmap=cmap, norm=norm, aspect='equal', interpolation='nearest')
    configure_axes(ax, pivot_table, num_nodes, num_scans)
    plt.tight_layout()
    return fig

def analyze_latest_scan(pivot_table):
    """Analyze and print statistics for the latest scan."""
    last_scan = pivot_table.iloc[:, -1]
    up_nodes_percentage = (last_scan == 1).mean() * 100
    print(f"\nPercentage of nodes up in latest scan: {up_nodes_percentage:.2f}%")
    up_nodes = last_scan[last_scan == 1].index.tolist()
    print(f"Nodes that are up in latest scan: {up_nodes}")

def plot_uptime_heatmap(csv_files):
    """
    Reads CSV files and plots a heatmap visualizing node uptime evolution.

    Args:
        csv_files (list): Paths to CSV files with 'Node_ID' and 'Reachable' columns.
    """
    all_data, file_labels = load_and_validate_csvs(csv_files)
    if all_data is None or file_labels is None:
        return

    pivot_table = process_data(all_data, file_labels)
    fig = create_heatmap(pivot_table)
    plt.savefig('/tmp/example.png', dpi=300, bbox_inches='tight')
    plt.show()
    analyze_latest_scan(pivot_table)

# Hardcoded list of CSV files
csv_files_to_plot = [
    '/tmp/pcunix_nodes_reachability_20250607_185820.csv',
    '/tmp/pcunix_nodes_reachability_20250607_190750.csv',
    '/tmp/pcunix_nodes_reachability_20250607_193422.csv',
    '/tmp/pcunix_nodes_reachability_20250607_202154.csv'
]

plot_uptime_heatmap(csv_files_to_plot)
