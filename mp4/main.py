import pandas as pd
from flask import Flask, request, jsonify,render_template, Response
import time
import zipfile
import edgar_utils as util
import geopandas as gpd
import re
import matplotlib.pyplot as plt

app = Flask(__name__)
homepage_visits = 0
donations = {'A': 0, 'B': 0}

def read_and_modify_html(version):
    '''
    Helper
    '''
    # Read the index.html file
    with open('index.html', 'r') as file:
        content = file.read()

    # Modify the donation link based on the version
    if version == 'A':
        modified_content = content.replace('donate.html', 'donate.html?from=A')
        modified_content = modified_content.replace('Donate', '<a href="donate.html?from=A" style="color:blue;">Donate</a>')
    else:
        modified_content = content.replace('donate.html', 'donate.html?from=B')
        modified_content = modified_content.replace('Donate', '<a href="donate.html?from=B" style="color:red;">Donate</a>')

    return modified_content

@app.route('/')
def home():
    global homepage_visits
    homepage_visits += 1

    # Determine which version to show
    version = 'A' if homepage_visits % 2 == 1 else 'B'
    if homepage_visits > 10:
        version = 'A' if donations['A'] > donations['B'] else 'B'

    modified_html = read_and_modify_html(version)
    return modified_html

@app.route('/browse.html')
def browse():
    # Read the first 500 rows of the CSV file from the zip archive
    df = pd.read_csv('server_log.zip', compression='zip', nrows=500)
    # Convert the DataFrame to an HTML table
    html_table = df.to_html()
    return f"<html><body><h1>Browse first 500 rows of rows.csv</h1></body>{html_table}</html>"

# Dictionary to store the last request time for each IP
last_request_time = {}

# Set to store the IPs of visitors
visitors = set()

@app.route('/browse.json')
def browse_json():
    client_ip = request.remote_addr
    current_time = time.time()
    
    # Update the visitors set
    visitors.add(client_ip)
    
    # Check if the client has made a request in the last minute
    if client_ip in last_request_time and current_time - last_request_time[client_ip] < 60:
        # Return 429 Too Many Requests if the request is too frequent
        return Response("Too many requests", status = 429, headers = {"Retry-After": 60 - (current_time - last_request_time[client_ip])})

    last_request_time[client_ip] = current_time

    df = pd.read_csv('server_log.zip', compression='zip', nrows=500)
    return jsonify(df.to_dict('records'))

@app.route('/visitors.json')
def visitors_json():
    return jsonify(list(visitors))

@app.route('/donate.html')
def donate():
    source = request.args.get('from', '')
    if source in donations:
        donations[source] += 1
    # # Serve the original donations page
    # with open('donations.html', 'r') as file:
    #     content = file.read()
    return """
    <h1>We Need Your Support</h1>
    <p>Your donation can help us continue our work and make a difference. Every contribution matters, no matter how small. Thank you for your support!</p>
    """


server_log = pd.read_csv('server_log.zip',compression = "zip")
@app.route('/analysis.html')
def analysis():
    
    #q1
    q1_dict = server_log.groupby('ip').size().nlargest(10).to_dict()
    
    #q2
    docs = zipfile.ZipFile('docs.zip')
    files = []
    objects = []
    file_names = docs.namelist()
    filing_dict = {}
    for i in file_names:
        if "htm" in i:
            files.append(i)
            
    with docs as j:
        for i in files:
            with j.open(i) as k:
                file = k.read()
                objects.append(util.Filing(str(file)))
                filing_dict[i] = util.Filing(str(file))
    
    sic_list = []
    for i in objects:
        sic_list.append(i.sic)
        
    q2 = {}
    for i in sic_list:
        if i != None and i not in q2.keys():
            q2[i] = 1
        elif i != None and i in q2.keys():
            q2[i] += 1
    q2 = dict(sorted(q2.items(), key = lambda x:x[1], reverse = True))
    q2_dict = {k: q2[k] for k in list(q2)[:10]}
    
    
    #q3
    addr_dict = {}
    server_log['find_path'] = server_log.apply(lambda row: f"{int(row['cik'])}/{row['accession']}/{row['extention']}", axis=1)
    
    matching_addr = server_log['find_path'].isin(filing_dict.keys())
    filtered = server_log[matching_addr]

    for idx, row in filtered.iterrows():
        filing_path = row['find_path']
        filing = filing_dict.get(filing_path)
        for addr in filing.addresses:
            mod_address = addr.replace('\\n', '')
            addr_dict[mod_address] = addr_dict.get(mod_address, 0) + 1
            
    q3_dict = {}
    for addr, c in addr_dict.items():
        if c >= 300:
            q3_dict[addr] = c
            
            
    # Loading GeoDataFrames
    state_shapes = gpd.read_file('shapes/cb_2018_us_state_20m.shp')
    geolocations = gpd.read_file('locations.geojson')

    # Setting the boundary box for filtering data
    boundary_box = (-95, -60, 25, 50)
    geolocations = geolocations.cx[boundary_box[0]:boundary_box[1], boundary_box[2]:boundary_box[3]]

    # Applying coordinate reference system and filtering state shapes
    state_shapes = state_shapes.cx[-95:-60, 25:50].to_crs("epsg:2022")

    # Converting geolocations to the same CRS
    geolocations = geolocations.to_crs("epsg:2022")
    # Extracting zipcodes from addresses
    geolocations['zipcode'] = geolocations['address'].apply(lambda address: int(re.search(r'(\d{5})', address).group(1)) if re.search(r'(\d{5})', address) else None)
    # Filtering locations by zipcode range
    geolocations = geolocations[(geolocations['zipcode'] >= 25000) & (geolocations['zipcode'] <= 65000)]

    # Creating and plotting the figure
    fig, ax = plt.subplots(figsize=(10, 10))
    state_shapes.plot(ax=ax, color='lightgray')
    geolocations.plot(ax=ax, column='zipcode', cmap='RdBu', legend=True)

    # Saving the figure
    plt.savefig('dashboard.svg', format='svg')
    plt.close(fig)

    
    return f"""<h1>Analysis of EDGAR Web Logs</h1>
    <p>Q1: how many filings have been accessed by the top ten IPs?</p>
    <p>{str(q1_dict)}</p>
    <p>Q2: what is the distribution of SIC codes for the filings in docs.zip?</p> 
    <p>{str(q2_dict)}</p>
    <p>Q3: what are the most commonly seen street addresses?</p>
    <p>{str(q3_dict)}</p>
    <h4>Dashboard: geographic plotting of postal code</h4>
    <img src="dashboard.svg">
    """

@app.route('/dashboard.svg')
def serve_svg():
    with open('dashboard.svg', 'r') as file:
        svg = file.read()
    return Response(svg, headers = {'Content-Type':'image/svg+xml'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False) # don't change this line!

# NOTE: app.run never returns (it runs for ever, unless you kill the process)
# Thus, don't define any functions after the app.run call, because it will
# never get that far.
