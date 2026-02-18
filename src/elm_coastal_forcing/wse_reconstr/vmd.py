# Description: runs VMD on gauge time series to extract tidal components for SWOT tidal reconstruction


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from vmdpy import VMD
from scripts.config import N_MODES

# Function to run VMD on gauge time series
def run_vmd_on_gauge(signal, n_modes=N_MODES):

    # Parameters for VMD; 
    # Taken from Matte & Innocenti (2025) 
    alpha = 2000       # Moderate bandwidth constraint
    tau = 1            # Noise-tolerance (no strict fidelity enforcement)
    K = 12             # Number of modes
    DC = 0             # Do not include DC part of signal
    init = 1           # Initialize modes uniformly
    tol = 1e-6         # Convergence tolerance

    # Perform VMD
    u, u_hat, omega = VMD(signal.values, alpha, tau, K, DC, init, tol)

    # Subset the modes to only first 9 intrinsic mode functions 
    imfs = u[0 : N_MODES, :] #.shape

    # Transpose and convert to DataFrame
    imfs = pd.DataFrame(imfs.T)

    # Rename columns to D0, D1, ..., D7
    imfs.columns = [f'D{i}' for i in range(imfs.shape[1])]

    # Convert IMFs to a DataFrame and align index with gauge_wse_df_sub
    imfs_df = pd.DataFrame(imfs) #, index=signal.index)

    print(f"    IMFs shape: {imfs_df.shape}")

    return imfs_df


#%%-----------------------------------------------------------------------
# Unit test for VMD

if __name__ == "__main__":
        
    # Generate a sample signal (for demonstration)
    t = np.linspace(0, 1, 40, endpoint=False)

    signal = (np.cos(2 * np.pi * 5 * t) + 
                np.cos(2 * np.pi * 10 * t) +
                np.cos(2 * np.pi * 30 * t))

    K = 12
    u = run_vmd_on_gauge(signal)

    if 1:
        # Plot the components
        plt.figure(figsize=(8, 22))
        plt.subplot(K+1, 1, 1)
        plt.plot(t, signal, 'k')
        plt.title("Original Signal")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")

        # Plot each mode
        for i in range(K):
            plt.subplot(K+1, 1, i+2)
            plt.plot(t, u[i, :])
            plt.title(f"Mode {i+1}")
            plt.xlabel("Time (s)")
            plt.ylabel("Amplitude")

        plt.tight_layout()
        plt.show()