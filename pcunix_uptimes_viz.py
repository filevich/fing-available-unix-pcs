import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import numpy as np # Used for arange to control label spacing

def plot_uptime_heatmap(csv_files):
    """
    Reads multiple CSV files (each representing a point in time scan of node reachability),
    and plots a heatmap visualizing the uptime evolution of each node with improved readability.

    Args:
        csv_files (list): A list of paths to the CSV files.
                          Each CSV should have 'Node_ID' and 'Reachable' columns.
    """

    if not csv_files:
        print("No CSV files provided. Exiting.")
        return

    # --- 1. Read and Parse CSV Files ---
    all_data = []
    file_labels = []

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            # Ensure 'Node_ID' and 'Reachable' columns exist
            if 'Node_ID' not in df.columns or 'Reachable' not in df.columns:
                print(f"Warning: Skipping {file_path}. Missing 'Node_ID' or 'Reachable' column.")
                continue

            # Add a 'timestamp' or 'scan_index' column for the x-axis
            # We'll use the filename (without extension) as a unique label for the x-axis
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
        return

    # Concatenate all dataframes into a single one
    combined_df = pd.concat(all_data, ignore_index=True)

    # Pivot the table to get Node_ID as index, Scan_Label as columns, and Reachable as values
    pivot_table = combined_df.pivot_table(
        index='Node_ID',
        columns='Scan_Label',
        values='Reachable',
        # aggfunc='first' will handle potential duplicates, though ideally there shouldn't be any.
        # If a node appears multiple times in the same scan, 'first' picks the first one.
        # If you expect this, consider a different aggfunc like 'mean' or 'max' if applicable.
        aggfunc='first'
    )

    # Ensure the columns (x-axis) are in the order of the provided csv_files
    # Fill any missing data (nodes not present in a specific scan) with 0 (unreachable)
    pivot_table = pivot_table.reindex(columns=file_labels, fill_value=0)

    # Sort Node_IDs on the y-axis for better readability (numerical sort)
    pivot_table = pivot_table.sort_index(ascending=True)

    # --- 2. Create the Heatmap Plot ---

    num_nodes = len(pivot_table.index)
    num_scans = len(pivot_table.columns)

    # Dynamic figure size:
    # Aim for roughly 0.25 to 0.3 inches per cell, allowing for labels.
    # Add extra space for labels and colorbar.
    cell_size = 0.3 # inches per cell
    fig_width = max(8, num_scans * cell_size + 2) # Min width of 8 inches, add space for labels
    fig_height = max(6, num_nodes * cell_size + 2) # Min height of 6 inches, add space for labels

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    # Define a custom colormap: 0 (red) -> 1 (green)
    cmap = mcolors.ListedColormap(['red', 'green'])
    # Set the boundaries for the colors. 0 for red, 1 for green.
    bounds = [-0.5, 0.5, 1.5]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    # Plot the heatmap
    # aspect='equal' is key for square cells
    cax = ax.imshow(pivot_table.values, cmap=cmap, norm=norm, aspect='equal', interpolation='nearest')

    # Add grid lines between cells for better visual separation
    ax.set_xticks(np.arange(-0.5, num_scans, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, num_nodes, 1), minor=True)
    ax.grid(which="minor", color="gray", linestyle='-', linewidth=0.5)
    ax.tick_params(which="minor", size=0) # Hide minor ticks themselves, just show grid

    # --- 3. Set Labels and Title ---
    # X-axis: File names (scan labels)
    ax.set_xticks(range(num_scans))
    ax.set_xticklabels(pivot_table.columns, rotation=45, ha='right', fontsize=8) # Reduce font size for X-labels
    ax.set_xlabel('Scan Time (Filename)')

    # Y-axis: Node IDs - Addressing Overlapping Labels
    # Get all node IDs (y-tick positions)
    all_y_ticks = np.arange(num_nodes)
    all_y_labels = pivot_table.index.tolist()

    # Determine how many labels to skip. Start with a common value like 5 or 10.
    # If num_nodes is large, increase this value.
    label_stride = 5 # Show every 5th label. Adjust this value (e.g., to 10) if still overlapping.
    if num_nodes > 50 and num_nodes <= 100:
        label_stride = 5
    elif num_nodes > 100:
        label_stride = 10 # For 129 nodes, 10 might be good (approx 13 labels)

    # Set ticks and labels with the determined stride
    ax.set_yticks(all_y_ticks[::label_stride])
    ax.set_yticklabels(all_y_labels[::label_stride])
    ax.set_ylabel('Unix Node ID')
    ax.tick_params(axis='y', labelsize=8) # Reduce font size for Y-labels

    ax.set_title('Cluster Node Uptime Evolution', fontsize=14)
    plt.tight_layout() # Adjust layout to prevent labels from overlapping

    # Add a colorbar to explain the colors
    # cbar = fig.colorbar(cax, ticks=[0, 1])
    # cbar.ax.set_yticklabels(['Down (0)', 'Up (1)'])
    # cbar.set_label('Reachability Status')

    # --- 4. Show and Save the Plot ---
    plt.savefig('/tmp/example.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Add the two new prints
    # Get the last scan's data (last column in pivot_table)
    last_scan = pivot_table.iloc[:, -1]
    
    # 1. Calculate percentage of nodes that were up
    up_nodes_percentage = (last_scan == 1).mean() * 100
    print(f"\nPercentage of nodes up in latest scan: {up_nodes_percentage:.2f}%")
    
    # 2. Get list of nodes that are up
    up_nodes = last_scan[last_scan == 1].index.tolist()
    print(f"Nodes that are up in latest scan: {up_nodes}")

# --- Hardcoded list of CSV files ---
# IMPORTANT: Replace these with the actual paths to your generated CSV files.
# Make sure these paths are correct relative to where you run the Python script,
# or provide absolute paths.
csv_files_to_plot = [
    '/tmp/pcunix_nodes_reachability_20250607_185820.csv',
    '/tmp/pcunix_nodes_reachability_20250607_190750.csv',
    '/tmp/pcunix_nodes_reachability_20250607_193422.csv',
]

plot_uptime_heatmap(csv_files_to_plot)