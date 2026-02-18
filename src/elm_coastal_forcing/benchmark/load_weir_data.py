
    #%% Load weir depth data ----------------------------------------
    def _load_weir_depth(self, site_id: str) -> pd.DataFrame:
        """
        Load and process weir depth (sonde) data for a site.

        Currently only implemented for 'GCW', similar to your original code.
        """
        if site_id != "GCW":
            # Return empty DataFrame if no sonde data
            return pd.DataFrame()

        path = f"{SONDE_DIR}/GCW/weir_exotable/GCReW_weir_exo.csv"
        df = (
            pd.read_csv(path)
            .assign(
                timestamp_local_hr=lambda x: pd.to_datetime(
                    x["timestamp_local_hr"], errors="coerce"
                )
            )
        )

        # Localize timestamps (hard-coded offset; you might improve this later)
        df["timestamp_local_hr"] = df["timestamp_local_hr"].dt.tz_localize("UTC-04:00")

        # Compute elevation using mean SWOT level and an offset, as in your code
        mean_swot = self.swot_tidal_wse_df["swot_wse_m_navd_mean"].mean()
        df["elev_m"] = df["depth_m_anomaly"] + mean_swot + 0.15
        return df
