import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import numpy as np
import argparse

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Plot node uptime heatmap and analyze reachable nodes.")
    parser.add_argument(
        "csv_files",
        nargs="+",
        help="Paths to CSV files with node reachability data."
    )
    parser.add_argument(
        "--format",
        choices=["plain", "md", "markdown"],
        default="plain",
        help="Output format for the grouped nodes table: 'plain' or 'md'/'markdown' (default: plain)"
    )
    return parser.parse_args()

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
            required_columns = ['Node_ID', 'Reachable', 'CPU_Name', 'Cores_Per_Socket', 'Total_CPUs', 'Total_RAM_GiB']
            if not all(col in df.columns for col in required_columns):
                print(f"Warning: Skipping {file_path}. Missing one or more required columns: {required_columns}.")
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

def format_node_ranges(node_ids):
    """Convert a list of node IDs into a compact string with unified ranges."""
    if not node_ids:
        return ""
    node_ids = sorted(node_ids)
    ranges = []
    start = node_ids[0]
    prev = node_ids[0]

    for curr in node_ids[1:] + [None]:
        if curr is None or curr > prev + 1:
            if start == prev:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{prev}")
            if curr is not None:
                start = curr
        prev = curr if curr is not None else prev

    return ", ".join(ranges)

def analyze_latest_scan(pivot_table, latest_data, output_format):
    """Analyze and print statistics for the latest scan, including grouped nodes by CPU and RAM."""
    last_scan = pivot_table.iloc[:, -1]
    up_nodes_percentage = (last_scan == 1).mean() * 100
    print(f"\nPercentage of nodes up in latest scan: {up_nodes_percentage:.2f}%")
    up_nodes = last_scan[last_scan == 1].index.tolist()
    print(f"Nodes that are up in latest scan: {up_nodes}")

    # Group reachable nodes by CPU and RAM configuration
    if up_nodes:
        up_nodes_df = latest_data[latest_data['Node_ID'].isin(up_nodes)][
            ['Node_ID', 'CPU_Name', 'Cores_Per_Socket', 'Total_CPUs', 'Total_RAM_GiB']
        ]
        grouped = up_nodes_df.groupby(
            ['CPU_Name', 'Cores_Per_Socket', 'Total_CPUs', 'Total_RAM_GiB']
        ).agg({'Node_ID': list}).reset_index()

        print("\nGrouped Reachable Nodes by CPU and RAM Configuration:")
        
        if output_format in ["md", "markdown"]:
            # Markdown table header
            print("| Number of Nodes | CPU | Physical Cores | Logical Threads | DRAM (GiB) | Node IDs |")
            print("|-----------------|-----|----------------|-----------------|------------|----------|")
            
            # Markdown table rows
            for _, row in grouped.iterrows():
                num_nodes = len(row['Node_ID'])
                cpu_name = row['CPU_Name'].replace("|", "\\|")  # Escape pipes for Markdown
                cores = row['Cores_Per_Socket']
                threads = row['Total_CPUs']
                ram = row['Total_RAM_GiB']
                node_ids = format_node_ranges(row['Node_ID']).replace("|", "\\|")  # Escape pipes
                print(f"| {num_nodes} | {cpu_name} | {cores} | {threads} | {ram} | {node_ids} |")
        else:
            # Plain text table
            print("-" * 60)
            print(f"{'Number of Nodes':<15} {'CPU':<20} {'Physical Cores':<15} {'Logical Threads':<15} {'DRAM (GiB)':<10} {'Node IDs'}")
            print("-" * 60)

            for _, row in grouped.iterrows():
                num_nodes = len(row['Node_ID'])
                cpu_name = row['CPU_Name']
                cores = row['Cores_Per_Socket']
                threads = row['Total_CPUs']
                ram = row['Total_RAM_GiB']
                node_ids = format_node_ranges(row['Node_ID'])
                print(f"{num_nodes:<15} {cpu_name:<20} {cores:<15} {threads:<15} {ram:<10} {node_ids}")

def plot_uptime_heatmap():
    """
    Reads CSV files and plots a heatmap visualizing node uptime evolution.
    """
    args = parse_arguments()
    csv_files = args.csv_files
    output_format = args.format

    all_data, file_labels = load_and_validate_csvs(csv_files)
    if all_data is None or file_labels is None:
        return

    pivot_table = process_data(all_data, file_labels)
    latest_data = all_data[-1]  # Use the latest CSV file for grouping
    fig = create_heatmap(pivot_table)
    plt.savefig('/tmp/example.png', dpi=300, bbox_inches='tight')
    plt.show()
    analyze_latest_scan(pivot_table, latest_data, output_format)

if __name__ == "__main__":
    plot_uptime_heatmap()