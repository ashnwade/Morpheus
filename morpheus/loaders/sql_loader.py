# Copyright (c) 2022-2023, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import logging
import typing

import pandas as pd
from sqlalchemy import create_engine

import cudf

from morpheus.messages import ControlMessage
from morpheus.messages import MessageMeta
from morpheus.utils.control_message_utils import CMDefaultFailureContextManager
from morpheus.utils.control_message_utils import cm_skip_processing_if_failed
from morpheus.utils.execution_chain import ExecutionChain
from morpheus.utils.loader_utils import register_loader

logger = logging.getLogger(__name__)


def _parse_query_data(
    query_data: dict[str, str | typing.Optional[dict[str, typing.Any]]]
) -> dict[str, str | typing.Optional[dict[str, typing.Any]]]:
    """
    Parses a dictionary of query data.

    Parameters
    ----------
    query_data : Dict[str, Union[str, Optional[Dict[str, Any]]]]
        The dictionary containing the connection string, query, and params (optional).

    Returns
    -------
    Dict[str, Union[str, Optional[Dict[str, Any]]]]
        A dictionary containing parsed connection string, query, and params (if present).
    """

    return {
        "connection_string": query_data["connection_string"],
        "query": query_data["query"],
        "params": query_data.get("params", None)
    }


def _read_sql(connection_string: str, query: str, params: typing.Optional[typing.Dict[str, typing.Any]] = None) -> \
        typing.Dict[str, pd.DataFrame]:
    """
    Creates a DataFrame from a SQL query.

    Parameters
    ----------
    connection_string : str
        Connection string to the database.
    query : str
        SQL query.
    params : Optional[Dict[str, Any]], default=None
        Parameters to pass to pd.read_sql.

    Returns
    -------
    Dict[str, pd.DataFrame]
        A dictionary containing a DataFrame of the SQL query result.
    """

    # TODO(Devin): PERFORMANCE OPTIMIZATION
    # TODO(Devin): Add connection pooling -- Probably needs to go on the actual loader
    engine = create_engine(connection_string)

    if (params is None):
        df = pd.read_sql(query, engine)
    else:
        df = pd.read_sql(query, engine, params=params)

    return {"df": df}


def _aggregate_df(df_aggregate: typing.Optional[cudf.DataFrame], df: pd.DataFrame) -> cudf.DataFrame:
    """
    Aggregates two DataFrames.

    Parameters
    ----------
    df_aggregate : Optional[cudf.DataFrame]
        DataFrame to append the other DataFrame to. If None, returns the converted DataFrame.
    df : pd.DataFrame
        DataFrame to append to df_aggregate.

    Returns
    -------
    cudf.DataFrame
        The aggregated DataFrame.
    """

    cdf = cudf.from_pandas(df)
    if (df_aggregate):
        return df_aggregate.append(cdf)

    return cdf


@register_loader("SQLLoader")
@cm_skip_processing_if_failed
def sql_loader(control_message: ControlMessage, task: typing.Dict[str, typing.Any]) -> ControlMessage:
    """
    SQL loader to fetch data from a SQL database and store it in a DataFrame.

    Parameters
    ----------
    control_message : ControlMessage
        The control message containing metadata and a payload.
    task : Dict[str, Any]
        The task configuration containing SQL config and queries.

    Returns
    -------
    ControlMessage
        Control message with the final DataFrame in the payload.
    """

    with CMDefaultFailureContextManager(control_message):
        final_df = None

        sql_config = task["sql_config"]
        queries = sql_config["queries"]

        for query_data in queries:
            aggregate_df = functools.partial(_aggregate_df, df_aggregate=final_df)
            execution_chain = ExecutionChain(function_chain=[_parse_query_data, _read_sql, aggregate_df])
            final_df = execution_chain(query_data=query_data)

        control_message.payload(MessageMeta(final_df))

    return control_message
