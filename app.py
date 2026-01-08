import os

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.FileHandler("flask_app.log"), logging.StreamHandler()],
)

app = Flask(__name__)
load_dotenv()
#app.secret_key = os.getenv("FLASK_SECRET", "fallback-secret")
app.secret_key = "very-secret-123"
#Talisman(app, content_security_policy=None, force_https=False)

es = Elasticsearch(os.getenv("ES_HOST"))


def convert_to_est(timestamp_series):
    """
    Convert timestamps to EST timezone.
    - If timestamp is already in EST (UTC-5), keep it as is
    - If timestamp is in UTC or other timezone, convert to EST
    """
    est_tz = pytz.timezone("US/Eastern")
    
    def smart_convert(ts):
        if pd.isna(ts):
            return ts
        
        # Parse the timestamp
        dt = pd.to_datetime(ts, errors='coerce')
        
        if pd.isna(dt):
            return dt
        
        # If timezone-naive, assume UTC and localize
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        # Check if already in EST/EDT (UTC offset of -5:00 or -4:00)
        # EST is UTC-5, EDT (daylight saving) is UTC-4
        offset_hours = dt.utcoffset().total_seconds() / 3600
        
        if offset_hours in [-5.0, -4.0]:
            # Already in US/Eastern timezone, just ensure it has the right tzinfo
            return dt.astimezone(est_tz)
        else:
            # Convert from other timezone (like UTC) to EST
            return dt.astimezone(est_tz)
    
    return timestamp_series.apply(smart_convert)


def fetch_data_from_es():
    query = {"query": {"match_all": {}},"sort": [{"time_stamp": {"order": "desc"}}], "size": 1000}
    res = es.search(index=os.getenv("ES_INDEX"), body=query, scroll="5m")
    records = [hit["_source"] for hit in res["hits"]["hits"]]
    return pd.DataFrame(records)


def fetch_data_from_es_api_search(api_name_search):
    query = {
        "query": {"bool": {"must": [{"term": {"api_name.keyword": api_name_search}}]}},
        "sort": [{"time_stamp": {"order": "desc"}}],
        "size": 10000, 
    }
    res = es.search(index=os.getenv("ES_INDEX"), body=query)
    records = [hit["_source"] for hit in res["hits"]["hits"]]
    return pd.DataFrame(records)


def fetch_data_from_es_correlationid_search(correlation_id_search):
    query = {
        "query": {
            "bool": {
                "must": [{"term": {"correlationid.keyword": correlation_id_search}}]
            }
        },"sort": [{"time_stamp": {"order": "desc"}}],
        "size": 1000,
    }
    res = es.search(index=os.getenv("ES_INDEX"), body=query)
    records = [hit["_source"] for hit in res["hits"]["hits"]]
    return pd.DataFrame(records)


def fetch_data_from_es_api_and_correlationid_search(
    api_name_search, correlation_id_search
):
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"api_name.keyword": api_name_search}},
                    {"term": {"correlationid.keyword": correlation_id_search}},
                ]
            }
        },"sort": [{"time_stamp": {"order": "desc"}}],
        "size": 1000,
    }
    res = es.search(index=os.getenv("ES_INDEX"), body=query)
    records = [hit["_source"] for hit in res["hits"]["hits"]]
    return pd.DataFrame(records)


def fetch_data_from_es_api_name():
    query = {
        "size": 0,
        "aggs": {"unique_ids": {"terms": {"field": "api_name.keyword", "size": 1000}}},
        "sort": [{"time_stamp": {"order": "desc"}}],
    }
    result = es.search(index=os.getenv("ES_INDEX"), body=query)
    unique_apis = [
        bucket["key"] for bucket in result["aggregations"]["unique_ids"]["buckets"]
    ]
    return sorted(unique_apis)  # Return sorted list of API names


def fetch_data_from_es_search_fields(search_type, search_value):
    # print("search_type",search_type)
    # print("search_value",search_value)
    query = {
        "query": {"match": {f"{search_type}": search_value}},
        "sort": [{"time_stamp": {"order": "desc"}}],
        "size": 1000,
    }
    res = es.search(index=os.getenv("ES_INDEX"), body=query)
    records = [hit["_source"] for hit in res["hits"]["hits"]]
    return pd.DataFrame(records)


def fetch_data_from_es_date_range(start_date=None, end_date=None):
    # print("start date",start_date)
    # print("end date",end_date)
    query = {
        "query": {
            "range": {
                "time_stamp": {
                    "gte": start_date,
                    "lte": end_date,
                    "format": "strict_date_optional_time",
                }
            }
        },
        "sort": [{"time_stamp": {"order": "desc"}}],
        "size": 1000,
    }

    # If no dates provided, get last 24 hours
    if not start_date and not end_date:
        now = datetime.now(pytz.timezone("US/Eastern"))
        query["query"]["range"]["time_stamp"]["gte"] = (
            now - timedelta(hours=24)
        ).isoformat()
        query["query"]["range"]["time_stamp"]["lte"] = now.isoformat()

    res = es.search(index=os.getenv("ES_INDEX"), body=query)
    records = [hit["_source"] for hit in res["hits"]["hits"]]
    return pd.DataFrame(records)


def is_authenticated():
    return session.get("logged_in", False)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]
        if user == os.getenv("LOGIN_USER") and pwd == os.getenv("LOGIN_PASSWORD"):
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
def index():
    if not is_authenticated():
        return redirect(url_for("login"))

    api_names = fetch_data_from_es_api_name()

    # Get states from ES using similar aggregation
    query = {
        "size": 0,
        "aggs": {"unique_states": {"terms": {"field": "state.keyword", "size": 10}}},
    }
    result = es.search(index=os.getenv("ES_INDEX"), body=query)
    states = sorted(
        [bucket["key"] for bucket in result["aggregations"]["unique_states"]["buckets"]]
    )

    return render_template("index.html", api_names=api_names, states=states)


@app.route("/search", methods=["POST"])
def search():
    try:
        if not is_authenticated():
            return jsonify([]), 200

        data = request.json or {}

        must_clauses = []

        if data.get("api_name"):
            must_clauses.append({"term": {"api_name.keyword": data["api_name"]}})
        if data.get("correlationid"):
            must_clauses.append({"term": {"correlationid.keyword": data["correlationid"]}})
        if data.get("search_type") and data.get("search_value"):
            must_clauses.append({"match": {f"{data['search_type']}": data["search_value"]}})
        if data.get("state"):
            must_clauses.append({"term": {"state.keyword": data["state"]}})

        # Time filtering logic
        start_date = None
        end_date = None
        timestamp_filter = data.get("timestamp_filter")
        now_est = datetime.now(pytz.timezone("US/Eastern"))

        if timestamp_filter == "custom":
            start_date = data.get("custom_start_time")
            end_date = data.get("custom_end_time")
        elif timestamp_filter:
            end_date = now_est.isoformat()
            if timestamp_filter == "30min":
                start_date = (now_est - timedelta(minutes=30)).isoformat()
            elif timestamp_filter == "1hr":
                start_date = (now_est - timedelta(hours=1)).isoformat()
            elif timestamp_filter == "6hr":
                start_date = (now_est - timedelta(hours=6)).isoformat()

        if start_date or end_date:
            range_query = {"range": {"time_stamp": {"format": "strict_date_optional_time"}}}
            if start_date:
                range_query["range"]["time_stamp"]["gte"] = start_date
            if end_date:
                range_query["range"]["time_stamp"]["lte"] = end_date
            must_clauses.append(range_query)

        if must_clauses:
            query_body = {"bool": {"must": must_clauses}}
            size = 1000  # More results for filtered queries
        else:
            query_body = {"match_all": {}}
            size = 1000   # Fewer results for unfiltered queries

        query = {
            "query": query_body,
            "sort": [{"time_stamp": {"order": "desc"}}],
            "size": size
        }

        res = es.search(index=os.getenv("ES_INDEX"), body=query)
        records = [hit["_source"] for hit in res.get("hits", {}).get("hits", [])]
        df = pd.DataFrame(records)

        if df.empty:
            return jsonify([]), 200

        # Convert to US/Eastern timezone using smart conversion
        df["time_stamp"] = convert_to_est(df["time_stamp"])
        
        # Drop rows with invalid timestamps (optional safety)
        df = df.dropna(subset=["time_stamp"])

        # Group by correlationid to find min and max timestamps
        duration_df = df.groupby("correlationid")["time_stamp"].agg(["min", "max"]).reset_index()

        # Calculate duration in seconds
        duration_df["duration_seconds"] = (duration_df["max"] - duration_df["min"]).dt.total_seconds()

        def format_duration(seconds):
            if pd.isna(seconds):
                return "N/A"

            seconds = float(seconds)

            # Less than 1 second - show in milliseconds
            if seconds < 1:
                milliseconds = seconds * 1000
                return f"{milliseconds:.2f}ms"
            
            # Less than 60 seconds - show in seconds
            elif seconds < 60:
                return f"{seconds:.2f}s"
            
            # Less than 60 minutes (3600 seconds) - show in minutes
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.2f}m"
            
            # 60 minutes or more - show in hours
            else:
                hours = seconds / 3600
                return f"{hours:.2f}h"

        duration_df["total_time_taken"] = duration_df["duration_seconds"].apply(format_duration)

        # Ensure one record per correlationid - keep latest by timestamp
        df.sort_values(by="time_stamp", ascending=False, inplace=True)
        unique_df = df.drop_duplicates(subset="correlationid", keep="first").copy()

        # Merge duration info with the unique records
        unique_df = pd.merge(
            unique_df,
            duration_df[["correlationid", "total_time_taken"]],
            on="correlationid",
            how="left"
        )

        # Format timestamp as a string for display and append "EST"
        unique_df["time_stamp"] = unique_df["time_stamp"].dt.strftime("%Y-%m-%d %H:%M:%S") + " EST"
        unique_df = unique_df.where(pd.notnull(unique_df), None)
        result = unique_df[["correlationid", "api_name", "time_stamp", "state", "total_time_taken"]].to_dict(orient="records")
        return jsonify(result), 200

    except Exception as e:
        # Log the error with stack trace for diagnostics
        print("Error in /search:", e, flush=True)
        import traceback
        traceback.print_exc()

        # Return a safe JSON error response
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500



@app.route("/chart-data")
def chart_data():
    if not is_authenticated():
        return jsonify({})
    data = request.json
    df = fetch_data_from_es_api_search(data["api_name"])
    # Convert timestamps using smart conversion
    df["time_stamp"] = convert_to_est(df["time_stamp"])
    df["hour"] = df["time_stamp"].dt.hour
    api_summary = (
        df.groupby(["hour", "state"]).size().unstack(fill_value=0).reset_index()
    )
    return jsonify(api_summary.to_dict(orient="records"))


@app.route("/details/<correlationid>")
def drill_down(correlationid):
    print('correlation id', correlationid)
    if not is_authenticated():
        return jsonify([])
    if correlationid:
        df = fetch_data_from_es_correlationid_search(correlationid)
    else:
        df = fetch_data_from_es()

    # Replace pandas NaN with None for valid JSON conversion.
    # JSON does not support NaN, but it does support null (which is what None becomes).
    df = df.where(pd.notnull(df), None)

    return jsonify(df.to_dict(orient="records"))


@app.route("/workflow")
def workflow():
    if not is_authenticated():
        return redirect(url_for("login"))
    return render_template("workflow.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)