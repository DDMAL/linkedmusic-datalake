"""
helper functions to get the flattened CSV files
"""

import pandas as pd


def flatten_aliases():
    """
    flatten_aliases.csv merge all rows by tune_id and name and create columns for different aliases
    flatten aliases create a list of aliases for each tune_id and name pair
    """
    df = pd.read_csv("./data/aliases.csv")
    df = df.groupby(["tune_id", "name"])["alias"].agg(tuple)
    df = df.map(list).reset_index()
    # Display the result
    df.to_csv("data/transformed/flatten_aliases.csv", index=False)


def flatten_tunes():
    """
    flatten_tunes.csv doesn't have abc columns.
    It merge all rows with the same tune_id and name and create new columns with indexes
    for the subsequent columns
    """
    df = pd.read_csv("./data/tunes.csv")
    df.drop(["abc"], axis=1)
    merge_on = ["tune_id", "name", "type"]

    df["test_count"] = df.groupby(["tune_id", "name", "type"]).cumcount() + 1
    df2 = df.pivot(
        index=merge_on,
        columns="test_count",
        values=["setting_id", "type", "meter", "mode", "date", "username"],
    )

    df2.columns = [f"{col[0]}_{col[1]}" for col in df2.columns]

    # Reset the index
    df2 = df2.reset_index()
    df2.to_csv("data/transformed/flatten_tunes.csv", index=False)


def flatten_recordings(with_recording, merged_on):
    pivot_table = with_recording.pivot(
        index=merged_on,
        columns="index_suffix",
        values=[
            "recordings_id",
            "recordings_artist",
            "recordings_recording",
            "recordings_track",
            "recordings_number",
        ],
    )

    # # Flatten the multi-level column index
    pivot_table.columns = [f"{col[0]}_{col[1]}" for col in pivot_table.columns]

    # # Reset the index to make 'index_suffix' a regular column
    pivot_table.reset_index(inplace=True)
    pivot_table.to_csv("data/transformed/flatten_recordings.csv", index=False)
