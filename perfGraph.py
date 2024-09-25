import re
from flask import Flask, request, jsonify, render_template
import plotly.graph_objs as go
import datetime

# Define Flask app
app = Flask(__name__)


# Function to parse the log file
def parse_log_file(file_content):
    latencies = []
    logging_level_ok = False
    warning_message = ""

    for line in file_content.splitlines():
        # Check if the log level is set to TRACE or VERBOSE
        if "log level for 'PERFORMANCE'" in line:
            match = re.search(r"log level for 'PERFORMANCE' has been changed from 'INFO' to '(\w+)'", line)
            if match:
                level = match.group(1)
                if level in ['TRACE', 'VERBOSE']:
                    logging_level_ok = True

        # Extract latency information
        match = re.search(
            r"(\d+-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) \[PERFORMANCE\s+\]T:  Source latency (\d+\.\d+) seconds, Target latency (\d+\.\d+) seconds, Handling latency (\d+\.\d+) seconds",
            line)
        if match:
            timestamp_str = match.group(1)
            timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
            source_latency = float(match.group(2))
            target_latency = float(match.group(3))
            handling_latency = float(match.group(4))
            latencies.append({
                'timestamp': timestamp,
                'source': source_latency,
                'target': target_latency,
                'handling': handling_latency
            })

    if not logging_level_ok:
        warning_message = "Warning: The correct debug level for the 'Performance' component was not verified."

    return latencies, warning_message


# Function to calculate statistics from latencies
def calculate_statistics(latencies):
    if not latencies:
        return {}

    max_source = max(latencies, key=lambda x: x['source'])
    max_target = max(latencies, key=lambda x: x['target'])
    max_handling = max(latencies, key=lambda x: x['handling'])

    avg_source = sum(x['source'] for x in latencies) / len(latencies)
    avg_target = sum(x['target'] for x in latencies) / len(latencies)
    avg_handling = sum(x['handling'] for x in latencies) / len(latencies)

    return {
        'time_range': {
            'start': latencies[0]['timestamp'],
            'end': latencies[-1]['timestamp']
        },
        'max_source': max_source['source'],
        'max_source_time': max_source['timestamp'],
        'max_target': max_target['target'],
        'max_target_time': max_target['timestamp'],
        'max_handling': max_handling['handling'],
        'max_handling_time': max_handling['timestamp'],
        'avg_source': avg_source,
        'avg_target': avg_target,
        'avg_handling': avg_handling
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['logfile']
    file_content = file.read().decode('utf-8')
    latencies, warning_message = parse_log_file(file_content)
    stats = calculate_statistics(latencies)
    latencies_json = [
        {'timestamp': l['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 'source': l['source'], 'target': l['target'],
         'handling': l['handling']} for l in latencies]

    return jsonify({'latencies': latencies_json, 'stats': stats, 'warning': warning_message})


if __name__ == '__main__':
    app.run(debug=True)
