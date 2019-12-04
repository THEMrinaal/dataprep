"""
    This module implements the plot_missing(df) function's
    calculating intermediate part
"""
from typing import Any, Optional, Tuple, Union

import dask
import numpy as np
import pandas as pd
from bokeh.io import show
from bokeh.models.widgets import Tabs
from bokeh.plotting import Figure

from ...utils import DataType, get_type
from ..common import Intermediate
from .visualization import (
    _vis_missing_impact,
    _vis_missing_impact_y,
    _vis_nonzero_count,
)


def _calc_nonzero_rate(data: np.ndarray, length: int) -> Any:
    """
    :param data: A column of data frame
    :param length: The length of array
    :return: The count of None, Nan, Null

    This function is used to calculate the rate of nonzero elements of each column
    """
    return np.count_nonzero(data) / length


def _calc_nonzero_count(
    pd_data_frame: pd.DataFrame,
    num_rows: Optional[int] = None,
    num_cols: Optional[int] = None,
) -> Intermediate:
    """
    :param pd_data_frame: the pandas data_frame for which plots are calculated
    for each column.
    :return: An object to encapsulate the
    intermediate results.

    This function is designed to calculate the intermediate result
    The intermediate result contains the nonzero elements rate of each column and
    the distribution of nonzero elements
    """
    pd_data_frame_value = pd.isnull(pd_data_frame.values.T)
    count_nonzero_list = []
    row, col = pd_data_frame_value.shape
    for i in range(row):
        count_nonzero_list.append(
            dask.delayed(_calc_nonzero_rate)(pd_data_frame_value[i, :], col)
        )
    count_nonzero_compute = dask.compute(*count_nonzero_list)
    pd_data_frame_value = pd_data_frame_value * 1
    if num_rows is not None and num_cols is not None:
        pd_data_frame_value = pd_data_frame_value[:num_cols, :num_rows]
    elif num_cols is not None:
        pd_data_frame_value = pd_data_frame_value[:num_cols, :]
    elif num_rows is not None:
        pd_data_frame_value = pd_data_frame_value[:, :num_rows]
    else:
        pd_data_frame_value = pd_data_frame_value
    result = {"distribution": pd_data_frame_value, "count": count_nonzero_compute}
    raw_data = {"df": pd_data_frame}
    intermediate = Intermediate(result=result, raw_data=raw_data, visual_type="dummy")
    return intermediate


def _calc_missing_impact(
    pd_data_frame: pd.DataFrame, x_name: str, num_bins: int = 10
) -> Intermediate:
    """
    :param pd_data_frame: the pandas data_frame for which plots are calculated
    for each column.
    :param x_name: The column whose value missing influence other columns
    :return: An object to encapsulate the
    intermediate results.

    This function is designed to delete rows whose x_name column are None, Nan, Null,
    then output data character of other columns
    """
    df_data_drop = pd_data_frame.dropna(subset=[x_name])
    columns_name = list(pd_data_frame.columns)
    columns_name.remove(x_name)
    result = {"df_data_drop": df_data_drop, "columns_name": columns_name}
    raw_data = {"df": pd_data_frame, "x_name": x_name, "num_bins": num_bins}
    intermediate = Intermediate(result=result, raw_data=raw_data, visual_type="dummy")
    return intermediate


def _calc_missing_impact_y(
    pd_data_frame: pd.DataFrame, x_name: str, y_name: str, num_bins: int = 10
) -> Intermediate:
    """
    :param pd_data_frame: the pandas data_frame for which plots are calculated for each
    column.
    :param x_name:
    :param y_name:
    :return: An object to encapsulate the
    intermediate results.

    This function is designed to delete rows whose x_name column are None, Nan, Null,
    then output data character of y_name column
    """
    df_data_sel = pd_data_frame[[x_name, y_name]]
    df_data_drop = df_data_sel.dropna(subset=[x_name])
    columns_name = list(df_data_drop.columns)
    result = {"df_data_drop": df_data_drop, "columns_name": columns_name}
    raw_data = {
        "df": pd_data_frame,
        "x_name": x_name,
        "y_name": y_name,
        "num_bins": num_bins,
    }
    intermediate = Intermediate(result=result, raw_data=raw_data, visual_type="dummy")
    return intermediate


def plot_missing(
    # pylint: disable=too-many-arguments
    pd_data_frame: pd.DataFrame,
    x_name: Optional[str] = None,
    y_name: Optional[str] = None,
    num_rows: Optional[int] = None,
    num_cols: Optional[int] = None,
    return_intermediate: bool = False,
) -> Union[Union[Figure, Tabs], Tuple[Union[Figure, Tabs], Any]]:
    """
    This function is designed to deal with missing values
    There are three functions: plot_missing(df), plot_missing(df, x)
    plot_missing(df, x, y)

    Parameters
    ----------
    pd_data_frame: pd.DataFrame
        the pandas data_frame for which plots are calculated for each column
    x_name: str, optional
        a valid column name of the data frame
    y_name: str, optional
        a valid column name of the data frame
    num_rows: int, optional
        The number of rows in the figure
    num_cols: int, optional
        The number of columns in the figure
    return_intermediate: bool
        whether show intermediate results to users

    Returns
    ----------
    An object of figure or
        An object of figure and
        An intermediate representation for the plots of different columns in the data_frame.

    Examples
    ----------
    >>> from dataprep.eda.missing.computation import plot_missing
    >>> import pandas as pd
    >>> df = pd.read_csv("suicide-rate.csv")
    >>> plot_missing(df, "HDI_for_year")
    >>> plot_missing(df, "HDI_for_year", "population")

    Notes
    ----------
    match (x_name, y_name)
        case (Some, Some) => histogram for numerical column,
        bars for categorical column, qq-plot, box-plot, jitter plot,
        CDF, PDF
        case (Some, None) => histogram for numerical column and
        bars for categorical column
        case (None, None) => heatmap
        otherwise => error
    """
    columns_name = list(pd_data_frame.columns)
    params = {"height": 375, "width": 325, "alpha": 0.3, "legend_position": "top"}
    for name in columns_name:
        if (
            get_type(pd_data_frame[name]) != DataType.TYPE_NUM
            and get_type(pd_data_frame[name]) != DataType.TYPE_CAT
        ):
            raise ValueError("the column's data type is error")
    if x_name is not None and y_name is not None:
        intermediate = _calc_missing_impact_y(
            pd_data_frame=pd_data_frame, x_name=x_name, y_name=y_name
        )
        fig = _vis_missing_impact_y(intermediate=intermediate, params=params)
    elif x_name is not None:
        intermediate = _calc_missing_impact(pd_data_frame=pd_data_frame, x_name=x_name)
        fig = _vis_missing_impact(intermediate=intermediate, params=params)
    elif x_name is None and y_name is not None:
        raise ValueError("Please give a value to x_name")
    else:
        intermediate = _calc_nonzero_count(
            pd_data_frame=pd_data_frame, num_rows=num_rows, num_cols=num_cols
        )
        fig = _vis_nonzero_count(intermediate=intermediate, params=params)
    show(fig)
    if return_intermediate:
        return fig, intermediate
    return fig
